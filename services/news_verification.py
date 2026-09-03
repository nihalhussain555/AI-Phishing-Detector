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
from groq import Groq
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
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
    Tries trafilatura first, then falls back to a simple BeautifulSoup
    paragraph scrape. Returns cleaned text or None.
    """

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        )
    }

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
                resp = requests.get(variant_url, headers=ExtractionService._HEADERS, timeout=10)
                resp.raise_for_status()
                soup = BeautifulSoup(resp.content, "lxml")
                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()
                paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
                text = " ".join(p for p in paragraphs if p)
                if text and len(text) >= ExtractionService.MIN_LENGTH:
                    logger.debug("[ExtractionService] BeautifulSoup fallback succeeded for %s", variant_url)
                    return ExtractionService._clean(text)
            except Exception as e:
                logger.warning("[ExtractionService] BeautifulSoup fallback error for %s: %s", variant_url, e)
                
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

    def verify_claim_with_context(self, claim: str, context: str, source_count: int = 0, trusted_count: int = 0) -> Dict[str, Any]:
        if not self.client:
            return {"prediction": "Insufficient Evidence", "confidence": 0, "insight": "GROQ_API_KEY missing. Cannot perform LLM verification."}

        corroboration_note = ""
        if trusted_count == 0:
            corroboration_note = (
                "\nIMPORTANT: none of the sources below are from a known, reliable outlet - "
                "they are unverified. Do not report high confidence (above ~60) purely on "
                "unverified sources; lean toward 'Insufficient Evidence' unless the claim is "
                "something you are independently confident about from general knowledge."
            )
        elif source_count == 1:
            corroboration_note = (
                "\nNote: only one source was found. A single source, even a reliable one, is "
                "weaker corroboration than multiple independent sources agreeing - factor this "
                "into your confidence score rather than treating it as fully settled."
            )

        prompt = f"""You are a rigorous, skeptical professional fact-checker. Your job is to
verify the claim below the way a real fact-checking organization would: weigh
source reliability, look for corroboration across independent sources, and
resist over-stating confidence when evidence is thin.

Claim: "{claim}"

Cross-Verification Data (sources are explicitly labeled as "Trusted" or
"Unverified" - weigh Trusted sources far more heavily than Unverified ones):
{context}
{corroboration_note}

Guidelines:
- "True"/"False": use only when evidence directly and clearly confirms or contradicts the claim.
- "Mostly True"/"Partially True": the claim is broadly correct but has a minor inaccuracy, missing context, or exaggeration.
- "Misleading": technically not false, but framed in a way that gives a false impression.
- "Insufficient Evidence": the sources don't actually address the claim, or are too unreliable/thin to judge - prefer this over guessing.
- confidence should reflect how strong and corroborated the evidence actually is, not just how the claim "feels".

Respond strictly in the following JSON format without any markdown backticks:
{{
    "prediction": "True", "Mostly True", "Partially True", "Misleading", "False", or "Insufficient Evidence",
    "confidence": <integer between 0 and 100>,
    "insight": "<2-3 sentences explaining the verdict, citing which source(s) it relies on, and noting reliability/corroboration>"
}}"""
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_completion_tokens=1024,
                # gpt-oss models are reasoning models: their internal "thinking"
                # tokens are drawn from the SAME max_completion_tokens budget as
                # the final answer. With a low budget and default/medium
                # reasoning effort, the model can burn through the whole budget
                # thinking and return an EMPTY final answer (finish_reason
                # "length"). reasoning_effort="low" keeps more of the budget
                # free for the actual JSON response.
                reasoning_effort="low",
                # Forces valid JSON output directly, instead of relying on
                # regex-extracting JSON out of free-form text.
                response_format={"type": "json_object"},
                stream=False
            )

            finish_reason = completion.choices[0].finish_reason
            content = (completion.choices[0].message.content or "").strip()

            if not content and finish_reason == "length":
                # Still ran out of room - retry once with a much bigger
                # budget rather than silently failing.
                logger.warning("[GroqInsightService] Empty output (ran out of tokens) - retrying with a larger budget.")
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.2,
                    max_completion_tokens=2048,
                    reasoning_effort="low",
                    response_format={"type": "json_object"},
                    stream=False
                )
                content = (completion.choices[0].message.content or "").strip()

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
# Service: Text similarity (stage 7)
# ---------------------------------------------------------------------------
class TextSimilarityService:
    """Lightweight claim/article similarity scoring using TF-IDF + cosine
    similarity. Deliberately avoids heavyweight ML dependencies (torch /
    sentence-transformers) so the app stays within Render free-tier RAM
    limits.
    """

    def score(self, claim: str, texts: List[str]) -> List[float]:
        """Returns a cosine-similarity score (0-1) for `claim` against each
        text in `texts`, in the same order."""
        if not texts:
            return []
        corpus = [claim] + texts
        vectorizer = TfidfVectorizer(stop_words="english", max_features=5000)
        try:
            matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            # Happens if the corpus is empty after stop-word removal
            return [0.0] * len(texts)
        claim_vec = matrix[0:1]
        text_vecs = matrix[1:]
        sims = cosine_similarity(claim_vec, text_vecs)[0]
        return sims.tolist()

    def score_grouped(self, claim: str, groups: List[List[str]]) -> List[List[float]]:
        """Same idea as score(), but scores multiple groups of chunks (e.g.
        one group per article) against the claim using a SINGLE shared
        TF-IDF vocabulary fit across the claim + every chunk from every
        group.

        This matters: fitting a fresh TfidfVectorizer per article (the old
        behaviour) gives each article its own IDF weighting, so a
        similarity score of 0.4 from article A is not actually comparable
        to a 0.4 from article B - the "best matching article" pick was
        effectively arbitrary. With one shared vocabulary, every score is
        on the same scale and cross-article ranking is meaningful.
        """
        if not groups or not any(groups):
            return [[] for _ in groups]

        all_chunks = []
        boundaries = []  # (start, end) index into all_chunks for each group
        for group in groups:
            start = len(all_chunks)
            all_chunks.extend(group)
            boundaries.append((start, len(all_chunks)))

        if not all_chunks:
            return [[] for _ in groups]

        corpus = [claim] + all_chunks
        vectorizer = TfidfVectorizer(stop_words="english", max_features=8000)
        try:
            matrix = vectorizer.fit_transform(corpus)
        except ValueError:
            return [[0.0] * len(g) for g in groups]

        claim_vec = matrix[0:1]
        chunk_vecs = matrix[1:]
        all_sims = cosine_similarity(claim_vec, chunk_vecs)[0]

        return [all_sims[start:end].tolist() for start, end in boundaries]

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
        self.similarity_service = TextSimilarityService()
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
                    "trust_weight": 1.0 if self.source_manager.is_trusted(url) else 0.5,
                })
        if len(extracted) < self.MIN_ARTICLES:
            return self._insufficient_evidence("Extraction yielded too few usable articles.")
        extracted = self.dedup_service.deduplicate_content(extracted)
        logger.info("[NewsVerification] %d unique articles after deduplication.", len(extracted))
        # Stage 7 – Semantic Verification (shared vocabulary across all
        # articles, so similarity scores are comparable to each other -
        # see TextSimilarityService.score_grouped docstring)
        article_chunks = []  # list of (chunks list, starting-sentence-index list) per article
        article_sentences = []
        for a in extracted:
            text = a["text"]
            sentences = re.split(r'(?<=[.!?]) +', text)
            article_sentences.append(sentences)

            chunks = []
            chunk_size = 3
            if len(sentences) <= chunk_size:
                chunks.append((text, 0))
            else:
                for i in range(0, min(len(sentences) - chunk_size + 1, 100)):
                    chunks.append((" ".join(sentences[i:i + chunk_size]), i))

            if not chunks:
                chunks = [(text[:1500], 0)]

            article_chunks.append(chunks)

        groups = [[c[0] for c in chunks] for chunks in article_chunks]
        grouped_scores = self.similarity_service.score_grouped(claim, groups)

        for a, chunks, scores, sentences in zip(extracted, article_chunks, grouped_scores, article_sentences):
            if not scores:
                scores = [0.0]

            best_idx = scores.index(max(scores))
            best_score_for_article = scores[best_idx]
            start_sentence_idx = chunks[best_idx][1]

            summary_start = max(0, start_sentence_idx - 1)
            summary_end = start_sentence_idx + 3 + 1
            best_snippet = " ".join(sentences[summary_start:summary_end])

            a["similarity"] = best_score_for_article
            a["best_snippet"] = best_snippet
            # Trusted sources are weighted up when RANKING which articles
            # to trust most - a mediocre-similarity match from Reuters
            # should generally outrank a slightly-higher-similarity match
            # from an unknown blog. Raw similarity is still reported
            # separately so the UI shows the true text-match strength.
            a["ranking_score"] = best_score_for_article * a["trust_weight"]

        extracted.sort(key=lambda x: x["ranking_score"], reverse=True)
        best_article = extracted[0]
        best_score = best_article["similarity"]
        trusted_sources_used = sum(1 for a in extracted[:3] if a["trust_weight"] >= 1.0)

        # Stage 8 – Groq LLM Verification with Cross-Verification Data.
        # Label each source's trustworthiness explicitly so the LLM can
        # weigh a known, reliable outlet more heavily than an unknown site
        # - the same way a human fact-checker would.
        context_data = ""
        for i, a in enumerate(extracted[:3]):
            trust_label = "Trusted News/Reference Source" if a["trust_weight"] >= 1.0 else "Unverified Source"
            context_data += f"[Source {i+1} - {trust_label} - {a['url']}]: {a['best_snippet']}\n"

        llm_result = self.groq_service.verify_claim_with_context(
            claim, context_data, source_count=len(extracted), trusted_count=trusted_sources_used
        )

        sources = [{"url": a["url"], "text": a["best_snippet"], "similarity": a["similarity"], "trusted": a["trust_weight"] >= 1.0} for a in extracted]
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