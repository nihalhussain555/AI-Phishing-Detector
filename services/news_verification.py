import os
import re
import logging
import urllib.parse
from typing import List, Dict, Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
import trafilatura
from newspaper import Article
from sentence_transformers import SentenceTransformer, util

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

def _extract_keywords(text: str) -> str:
    """Return a simplified search query consisting of the most relevant nouns.
    This is a lightweight heuristic – split on whitespace, drop common stopwords,
    and keep words longer than 3 characters.
    """
    stopwords = {
        "the", "a", "an", "and", "or", "but", "if", "is", "are", "was",
        "were", "be", "been", "to", "of", "in", "on", "for", "with",
        "at", "by", "from", "that", "this", "it", "as", "about",
    }
    words = re.findall(r"[A-Za-z]+", text)
    keywords = [w.lower() for w in words if w.lower() not in stopwords and len(w) > 3]
    # Return the first few unique keywords (max 5) to keep the query concise
    seen = set()
    result = []
    for kw in keywords:
        if kw not in seen:
            seen.add(kw)
            result.append(kw)
        if len(result) >= 5:
            break
    return " ".join(result)

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
        try:
            resp = self.session.get(self.ENDPOINT, params=params, timeout=10)
            logger.info("[GNewsService] HTTP %s for URL %s", resp.status_code, resp.url)
            resp.raise_for_status()
        except Exception as e:
            logger.error("[GNewsService] Request failed: %s", e)
            return []
        try:
            data = resp.json()
        except Exception as e:
            logger.error("[GNewsService] Failed to parse JSON: %s", e)
            return []
        urls = []
        for article in data.get("articles", []):
            url = article.get("url")
            if url and _is_valid_url(url):
                urls.append(url)
        logger.info("[GNewsService] Retrieved %d valid URLs", len(urls))
        return urls

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
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote_plus(title)}"
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
    def extract(url: str) -> Any:
        logger.info("[ExtractionService] Extracting URL: %s", url)
        try:
            # trafilatura.fetch_url does not accept a timeout kwarg; using default behavior
            downloaded = trafilatura.fetch_url(url)
            if downloaded:
                text = trafilatura.extract(downloaded)
                if text and len(text) >= ExtractionService.MIN_LENGTH:
                    logger.debug("[ExtractionService] trafilatura succeeded for %s", url)
                    return ExtractionService._clean(text)
        except Exception as e:
            logger.warning("[ExtractionService] trafilatura error for %s: %s", url, e)
        try:
            article = Article(url)
            article.download()
            article.parse()
            text = article.text
            if text and len(text) >= ExtractionService.MIN_LENGTH:
                logger.debug("[ExtractionService] newspaper3k succeeded for %s", url)
                return ExtractionService._clean(text)
        except Exception as e:
            logger.warning("[ExtractionService] newspaper3k error for %s: %s", url, e)
        logger.info("[ExtractionService] Extraction failed or text too short for %s", url)
        return None

    @staticmethod
    def _clean(raw: str) -> str:
        return re.sub(r"\s+", " ", raw).strip()

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
        logger.info("[EmbeddingService] Loading SentenceTransformer model")
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

    def embed_claim(self, claim: str):
        return self.model.encode(claim, convert_to_tensor=True)

    def embed_articles(self, texts: List[str]):
        return self.model.encode(texts, convert_to_tensor=True)

class VerificationEngine:
    THRESHOLDS = {
        "True": 0.75,
        "Mostly True": 0.60,
        "Partially True": 0.45,
        "Misleading": 0.30,
    }

    def __init__(self, trust_weight: float):
        self.trust_weight = trust_weight

    def decide(self, best_score: float, avg_score: float) -> Dict[str, Any]:
        weighted = (best_score * 0.6) + (avg_score * 0.2) + (self.trust_weight * 0.2)
        prediction = "Insufficient Evidence"
        for label, cutoff in self.THRESHOLDS.items():
            if weighted > cutoff:
                prediction = label
                break
        reason = (
            f"Weighted score {weighted:.2f} leads to {prediction}."
            if prediction != "Insufficient Evidence"
            else "Aggregated similarity too low after trust weighting."
        )
        confidence = round(weighted * 100, 2)
        return {"prediction": prediction, "confidence": confidence, "reason": reason, "weighted_score": weighted}

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

    def verify_claim(self, claim: str) -> Dict[str, Any]:
        logger.info("[NewsVerification] Starting verification for claim: %s", claim)
        search_query = _extract_keywords(claim) or claim
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
        article_texts = [a["text"] for a in extracted]
        article_embs = self.embedding_service.embed_articles(article_texts)
        scores = util.cos_sim(claim_emb, article_embs)[0].tolist()
        for i, s in enumerate(scores):
            extracted[i]["similarity"] = s
        extracted.sort(key=lambda x: x["similarity"], reverse=True)
        best_article = extracted[0]
        best_score = best_article["similarity"]
        top_k = min(3, len(extracted))
        avg_score = sum(a["similarity"] for a in extracted[:top_k]) / top_k
        # Stage 8 – Prediction
        engine = VerificationEngine(best_article["trust_weight"])
        decision = engine.decide(best_score, avg_score)
        # Stage 9 – Explanation
        support = [a["url"] for a in extracted if a["similarity"] > 0.5]
        contradict = [a["url"] for a in extracted if a["similarity"] <= 0.3]
        return {
            "prediction": decision["prediction"],
            "confidence": decision["confidence"],
            "similarity_score": round(best_score, 4),
            "closest_article": best_article["url"],
            "supporting_sources": support,
            "contradicting_sources": contradict,
            "evidence_summary": best_article["text"][:400] + "...",
            "reason": decision["reason"],
        }

    def _insufficient_evidence(self, msg: str) -> Dict[str, Any]:
        logger.warning("[NewsVerification] Insufficient evidence: %s", msg)
        return {
            "prediction": "Insufficient Evidence",
            "confidence": 0,
            "similarity_score": 0,
            "closest_article": None,
            "supporting_sources": [],
            "contradicting_sources": [],
            "evidence_summary": "",
            "reason": msg,
        }
