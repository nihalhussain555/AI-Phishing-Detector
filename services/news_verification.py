import os
import re

import time
import logging
import urllib.parse
from typing import List, Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from sentence_transformers import SentenceTransformer, util
from groq import Groq
import json
from utils.source_manager import SourceManager

# ---------------------------------------------------------------------------
# Logging configuration (Flask app can configure handlers as needed)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------
def _is_valid_url(url: str) -> bool:
    """Very small URL validator – ensures scheme and netloc are present."""
    try:
        parsed = urlparse(url)
        return all([parsed.scheme in ("http", "https"), parsed.netloc])
    except Exception:
        return False

# removed _extract_keywords as per user request to keep input intact
# ---------------------------------------------------------------------------
# Service: GNews API – now the preferred primary source
# ---------------------------------------------------------------------------
class GNewsService:
    """Stage 1 – Retrieves articles using the GNews API (free tier).
    Normalises results to a list of URLs.
    """

    ENDPOINT = "https://gnews.io/api/v4/search"
    MAX_RESULTS = 7

    def __init__(self):
        self.api_key = os.getenv("GNEWS_API_KEY")
        if not self.api_key:
            logger.warning("[GNewsService] GNEWS_API_KEY not set in environment")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AI-Phishing-Detector/1.0 (+https://github.com/nihalhussain555/AI-Phishing-Detector)"
        })

    def fetch(self, query: str) -> List[str]:
        if not self.api_key:
            logger.info("[GNewsService] Skipping because API key missing")
            return []
        params = {
            "q": query,
            "lang": "en",
            "max": self.MAX_RESULTS,
            "apikey": self.api_key,
        }
        logger.info("[GNewsService] Requesting %s with params %s", self.ENDPOINT, params)
        # Simple retry logic (2 attempts) with exponential backoff
        for attempt in range(2):
            try:
                resp = self.session.get(self.ENDPOINT, params=params, timeout=20)
                # If we get a 400 Bad Request, it's likely an API key or query issue – stop retrying
                if resp.status_code == 400:
                    logger.error("[GNewsService] 400 Bad Request – likely invalid API key or query. Skipping GNews.")
                    return []
                resp.raise_for_status()
                data = resp.json()
                urls = []
                for article in data.get("articles", []):
                    url = article.get("url")
                    if url and _is_valid_url(url):
                        urls.append(url)
                logger.info("[GNewsService] Retrieved %d valid URLs", len(urls))
                return urls
            except Exception as e:
                logger.error("[GNewsService] Request failed (attempt %d): %s", attempt + 1, e)
                if attempt < 1:
                    backoff = 2 ** attempt
                    logger.info("[GNewsService] Backing off for %d seconds", backoff)
                    time.sleep(backoff)
        return []

# ---------------------------------------------------------------------------
# Service: DuckDuckGo HTML based search – secondary fallback
# ---------------------------------------------------------------------------
class DuckDuckGoService:
    """Stage 2 – Free HTML search using DuckDuckGo.
    Parses <a class='result__a'> links, unwraps redirection and validates URLs.
    """

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    )
    MAX_RESULTS = 10

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.USER_AGENT})

    def search(self, query: str) -> List[str]:
        logger.info("[DuckDuckGoService] Query: %s", query)
        encoded = urllib.parse.quote_plus(query + " news")
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        logger.info("[DuckDuckGoService] GET %s", url)
        try:
            resp = self.session.get(url, timeout=10)
            logger.info("[DuckDuckGoService] HTTP %s", resp.status_code)
            resp.raise_for_status()
        except Exception as e:
            logger.error("[DuckDuckGoService] Request failed: %s", e)
            return []
        soup = BeautifulSoup(resp.text, "html.parser")
        raw_links: List[str] = []
        for a in soup.select('a.result__a'):
            href = a.get('href')
            if not href:
                continue
            parsed = urllib.parse.urlparse(href)
            if parsed.netloc == "duckduckgo.com" and parsed.path.startswith('/l/'):
                qs = urllib.parse.parse_qs(parsed.query)
                uddg = qs.get('uddg')
                if uddg:
                    href = uddg[0]
            if not _is_valid_url(href):
                continue
            final_url = href
            try:
                head_resp = self.session.head(href, allow_redirects=True, timeout=5)
                final_url = head_resp.url
            except Exception:
                pass
            if final_url not in raw_links:
                raw_links.append(final_url)
                logger.debug("[DuckDuckGoService] Found URL: %s", final_url)
        unique = list(dict.fromkeys(raw_links))[: self.MAX_RESULTS]
        logger.info("[DuckDuckGoService] Returned %d unique URLs", len(unique))
        return unique

# ---------------------------------------------------------------------------
# Service: Wikipedia fallback – final stage
# ---------------------------------------------------------------------------
class WikipediaService:
    """Stage 3 – Queries the MediaWiki API with proper headers.
    Returns the URL of the top matching article.
    """

    SEARCH_ENDPOINT = "https://en.wikipedia.org/w/api.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "AI-Phishing-Detector/1.0 (+https://github.com/nihalhussain555/AI-Phishing-Detector)"
        })

    def search(self, query: str) -> List[str]:
        logger.info("[WikipediaService] Searching for: %s", query)
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "",
            "format": "json",
        }
        try:
            resp = self.session.get(self.SEARCH_ENDPOINT, params=params, timeout=10)
            logger.info("[WikipediaService] HTTP %s for URL %s", resp.status_code, resp.url)
            resp.raise_for_status()
        except Exception as e:
            logger.error("[WikipediaService] Request failed: %s", e)
            return []
        try:
            data = resp.json()
        except Exception as e:
            logger.error("[WikipediaService] JSON parse error: %s", e)
            return []
        results = data.get("query", {}).get("search", [])
        if not results:
            logger.info("[WikipediaService] No search results")
            return []
        title = results[0]["title"]
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(title.replace(' ', '_'))}"
        logger.info("[WikipediaService] Selected article: %s", page_url)
        return [page_url]

# ---------------------------------------------------------------------------
# Service: Article Extraction (stage 4)
# ---------------------------------------------------------------------------
class ExtractionService:
    """Extracts readable text from a URL.
    Tries trafilatura first, then newspaper3k as a fallback.
    Returns cleaned text or None.
    """

    MIN_LENGTH = 80  # lowered to accept shorter but meaningful articles

    @staticmethod
    def _generate_url_variations(url: str) -> List[str]:
        """Generate variations of the URL by swapping common space characters in the last path segment."""
        parsed = urlparse(url)
        path = parsed.path
        if not path or path == '/':
            return [url]
            
        segments = path.split('/')
        last_segment = segments[-1] if segments[-1] else (segments[-2] if len(segments) > 1 else "")
        
        if not last_segment:
            return [url]
            
        decoded_segment = urllib.parse.unquote(last_segment)
        base_words = re.split(r'[-_+ ]', decoded_segment)
        base_words = [w for w in base_words if w]
        
        if len(base_words) <= 1:
            return [url]
            
        variations = []
        for sep in ['_', '-', '+', '%20']:
            if sep == '%20':
                new_segment = urllib.parse.quote(" ".join(base_words))
            else:
                new_segment = sep.join([urllib.parse.quote(w) for w in base_words])
                
            new_path = path.replace(last_segment, new_segment)
            new_url = urllib.parse.urlunparse(parsed._replace(path=new_path))
            if new_url not in variations:
                variations.append(new_url)
                
        # Ensure original url is first
        if url in variations:
            variations.remove(url)
        variations.insert(0, url)
        
        return variations

    @staticmethod
    def extract(url: str) -> Any:
        logger.info("[ExtractionService] Extracting URL: %s", url)
        
        url_variations = ExtractionService._generate_url_variations(url)
        
        for variant_url in url_variations:
            try:
                # trafilatura.fetch_url does not accept a timeout kwarg; using default behavior
                downloaded = trafilatura.fetch_url(variant_url)
                if downloaded:
                    text = trafilatura.extract(downloaded)
                    if text and len(text) >= ExtractionService.MIN_LENGTH:
                        logger.debug("[ExtractionService] trafilatura succeeded for %s", variant_url)
                        return ExtractionService._clean(text)
            except Exception as e:
                logger.warning("[ExtractionService] trafilatura error for %s: %s", variant_url, e)
                
            try:
                article = Article(variant_url)
                article.download()
                article.parse()
                text = article.text
                if text and len(text) >= ExtractionService.MIN_LENGTH:
                    logger.debug("[ExtractionService] newspaper3k succeeded for %s", variant_url)
                    return ExtractionService._clean(text)
            except Exception as e:
                logger.warning("[ExtractionService] newspaper3k error for %s: %s", variant_url, e)
                
        logger.info("[ExtractionService] Extraction failed or text too short for all variations of %s", url)
        return None

    @staticmethod
    def _clean(raw: str) -> str:
        # Remove Markdown table separators like |---|---|
        cleaned = re.sub(r'\|[-|]+', ' ', raw)
        # Remove multiple pipes (e.g. |||||)
        cleaned = re.sub(r'\|{2,}', ' ', cleaned)
        # Remove single pipes used in tables
        cleaned = cleaned.replace('|', ' ')
        # Remove wikipedia-style citations like [1], [a]
        cleaned = re.sub(r'\[\w+\]', '', cleaned)
        # Collapse multiple spaces and newlines into a single space
        return re.sub(r"\s+", " ", cleaned).strip()

# ---------------------------------------------------------------------------
# Service: Groq Insight (Stage 10)
# ---------------------------------------------------------------------------
class GroqInsightService:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        if self.api_key:
            # The SDK automatically targets the correct groq endpoint
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def verify_claim_with_context(self, claim: str, context: str) -> Dict[str, Any]:
        if not self.client:
            return {"prediction": "Insufficient Evidence", "confidence": 0, "insight": "GROQ_API_KEY missing. Cannot perform LLM verification."}
            
        prompt = f"""You are a professional fact-checking AI. 
Analyze the following claim using your internal knowledge AND the provided cross-verification search results. 
If the search results contradict your knowledge, trust the search results if they appear to be from reliable news/wiki sources.

Claim: "{claim}"

Cross-Verification Data: 
{context}

Respond strictly in the following JSON format without any markdown backticks:
{{
    "prediction": "True", "Mostly True", "Partially True", "Misleading", "False", or "Insufficient Evidence",
    "confidence": <integer between 0 and 100>,
    "insight": "<2-3 sentences explaining the verdict and how the cross-verification data aligns or contradicts the claim>"
}}"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=300,
                # reasoning_effort="medium",  # optional depending on model
                stream=False
            )

            content = completion.choices[0].message.content.strip()

            # Clean any surrounding markdown fences or stray whitespace
            content = re.sub(r'^```json\s*', '', content)
            content = re.sub(r'\s*```$', '', content)
            content = content.strip()

            if not content:
                logger.warning("[GroqInsightService] Empty response from LLM.")
                result = {"prediction": "Insufficient Evidence", "confidence": 0, "insight": "LLM returned empty output."}
            else:
                # Attempt to parse JSON directly; if that fails, try to extract a JSON block using regex
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    logger.warning("[GroqInsightService] Direct JSON parse failed – attempting regex extraction.")
                    json_match = re.search(r"\{.*\}", content, re.DOTALL)
                    if json_match:
                        try:
                            result = json.loads(json_match.group(0))
                        except json.JSONDecodeError as e2:
                            logger.error("[GroqInsightService] Regex JSON extraction also failed: %s", e2)
                            result = {"prediction": "Insufficient Evidence", "confidence": 0, "insight": f"Failed to parse LLM response: {e2}"}
                    else:
                        logger.error("[GroqInsightService] No JSON found in LLM response.")
                        result = {"prediction": "Insufficient Evidence", "confidence": 0, "insight": "LLM returned non‑JSON output.", "raw_output": content}

            return {
                "prediction": result.get("prediction", "Insufficient Evidence"),
                "confidence": int(result.get("confidence", 0)),
                "insight": result.get("insight", "")
            }
        except Exception as e:
            logger.error("[GroqInsightService] Failed to verify: %s", e)
            return {"prediction": "Insufficient Evidence", "confidence": 0, "insight": f"LLM Error: {e}"}

# ---------------------------------------------------------------------------
# Service: Deduplication (stage 6)
# ---------------------------------------------------------------------------
class DeduplicationService:
    @staticmethod
    def deduplicate(urls: List[str]) -> List[str]:
        return list(dict.fromkeys(urls))

    @staticmethod
    def deduplicate_content(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        seen = set()
        unique = []
        for art in articles:
            body_hash = hash(art["text"][:300])
            if body_hash not in seen:
                seen.add(body_hash)
                unique.append(art)
        return unique

# ---------------------------------------------------------------------------
# Service: Embedding & Verification (unchanged)
# ---------------------------------------------------------------------------
class EmbeddingService:
    def __init__(self):
        # Ensure HF token is set for loading SentenceTransformer models
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            os.environ["HF_HUB_TOKEN"] = hf_token
        else:
            logger.warning("[EmbeddingService] HF_TOKEN not set – may hit rate limits when loading models.")
    def _load_model(self):
        # Ensure HF token is set for loading SentenceTransformer models
        hf_token = os.getenv("HF_TOKEN")
        if hf_token:
            os.environ["HF_HUB_TOKEN"] = hf_token
        else:
            logger.warning("[EmbeddingService] HF_TOKEN not set – may hit rate limits when loading models.")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
    def embed_claim(self, claim: str):
        if not hasattr(self, "model"):
            self._load_model()
        return self.model.encode(claim, convert_to_tensor=True)

    def embed_articles(self, texts: List[str]):
        if not hasattr(self, "model"):
            self._load_model()
        return self.model.encode(texts, convert_to_tensor=True)

# VerificationEngine removed. LLM handles prediction logic natively.
# ---------------------------------------------------------------------------
# Facade Service – orchestrates the pipeline (stages 1‑9)
# ---------------------------------------------------------------------------
class NewsVerificationService:
    MIN_ARTICLES = 1  # lowered to allow verification with a single article

    def __init__(self):
        self.source_manager = SourceManager()
        self.gnews_service = GNewsService()
        self.duck_service = DuckDuckGoService()
        self.wikipedia_service = WikipediaService()
        self.extraction_service = ExtractionService()
        self.dedup_service = DeduplicationService()
        self.embedding_service = EmbeddingService()
        self.groq_service = GroqInsightService()

    def verify_claim(self, claim: str) -> Dict[str, Any]:
        logger.info("[NewsVerification] Starting verification for claim: %s", claim)
        search_query = claim
        logger.info("[NewsVerification] Optimised search query: %s", search_query)
        # Stage 1 – GNews primary
        urls = self.gnews_service.fetch(search_query)
        if len(urls) < self.MIN_ARTICLES:
            logger.info("[NewsVerification] GNews insufficient (%d). Falling back to DuckDuckGo.", len(urls))
            urls = self.dedup_service.deduplicate(urls + self.duck_service.search(search_query))
        if len(urls) < self.MIN_ARTICLES:
            logger.info("[NewsVerification] Still insufficient (%d). Falling back to Wikipedia.", len(urls))
            urls = self.dedup_service.deduplicate(urls + self.wikipedia_service.search(search_query))
        if not urls:
            return self._insufficient_evidence("All retrieval stages failed – no URLs collected.")
        logger.info("[NewsVerification] Collected %d candidate URLs after fallbacks.", len(urls))
        # Stage 4 – Extraction
        extracted = []
        for url in urls:
            if not _is_valid_url(url):
                logger.warning("[NewsVerification] Invalid URL skipped: %s", url)
                continue
            text = self.extraction_service.extract(url)
            if text:
                extracted.append({
                    "url": url,
                    "text": text,
                    "trust_weight": 1.0 if self.source_manager.is_trusted(url) else 0.6,
                })
        if len(extracted) < self.MIN_ARTICLES:
            return self._insufficient_evidence("Extraction yielded too few usable articles.")
        extracted = self.dedup_service.deduplicate_content(extracted)
        logger.info("[NewsVerification] %d unique articles after deduplication.", len(extracted))
        # Stage 7 – Semantic Verification
        claim_emb = self.embedding_service.embed_claim(claim)
        
        for a in extracted:
            text = a["text"]
            # Split into sentences using a simple regex
            sentences = re.split(r'(?<=[.!?]) +', text)
            
            chunks = []
            chunk_size = 3
            if len(sentences) <= chunk_size:
                chunks.append((text, 0)) # store chunk text and its starting index
            else:
                # Limit to first 100 chunks to prevent performance issues on huge pages
                for i in range(0, min(len(sentences) - chunk_size + 1, 100)):
                    chunks.append((" ".join(sentences[i:i+chunk_size]), i))
                    
            if not chunks:
                chunks = [(text[:1500], 0)]
                
            chunk_texts = [c[0] for c in chunks]
            chunk_embs = self.embedding_service.embed_articles(chunk_texts)
            chunk_scores = util.cos_sim(claim_emb, chunk_embs)[0].tolist()
            
            best_idx = chunk_scores.index(max(chunk_scores))
            best_score_for_article = chunk_scores[best_idx]
            start_sentence_idx = chunks[best_idx][1]
            
            # For the summary, grab a slightly wider window (e.g. 5 sentences) for better context
            summary_start = max(0, start_sentence_idx - 1)
            summary_end = start_sentence_idx + chunk_size + 1
            best_snippet = " ".join(sentences[summary_start:summary_end])
            
            a["similarity"] = best_score_for_article
            a["best_snippet"] = best_snippet

        extracted.sort(key=lambda x: x["similarity"], reverse=True)
        best_article = extracted[0]
        best_score = best_article["similarity"]
        
        # Stage 8 – Groq LLM Verification with Cross-Verification Data
        context_data = ""
        for i, a in enumerate(extracted[:3]):
            context_data += f"[Source {i+1}]: {a['best_snippet']}\n"
            
        llm_result = self.groq_service.verify_claim_with_context(claim, context_data)
        
        sources = [{"url": a["url"], "text": a["best_snippet"], "similarity": a["similarity"]} for a in extracted]
        return {
            "prediction": llm_result["prediction"],
            "confidence": llm_result["confidence"],
            "similarity_score": round(best_score, 4),
            "closest_article": best_article["url"],
            "sources_checked": sources,
            "evidence_summary": best_article["best_snippet"],
            "reason": llm_result["insight"],
            "llm_insight": llm_result["insight"],
        }

    def _insufficient_evidence(self, msg: str) -> Dict[str, Any]:
        logger.warning("[NewsVerification] Insufficient evidence: %s", msg)
        return {
            "prediction": "Insufficient Evidence",
            "confidence": 0,
            "similarity_score": 0,
            "closest_article": None,
            "sources_checked": [],
            "evidence_summary": "",
            "reason": msg,
            "llm_insight": "",
        }
