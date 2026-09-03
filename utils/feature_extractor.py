"""URL feature extraction for phishing detection.

Every feature here is computed purely from the URL string itself - no
network calls, no WHOIS lookups, no third-party APIs. That matters for two
reasons:
  1. It works even when the site is unreachable (down, DNS failure, etc.)
  2. It stays fast and light enough to run comfortably on Render's free tier.

IMPORTANT: this exact function is used both to build the training data
(model/train_model.py) and to score URLs at inference time
(services/phishing_ml.py). Keep FEATURE_NAMES and extract_features() in
sync - changing one without retraining the model will silently break
predictions.
"""

import re
import math
from urllib.parse import urlparse

SUSPICIOUS_TLDS = {
    "tk", "ml", "ga", "cf", "gq", "xyz", "top", "work", "click", "loan",
    "download", "review", "country", "stream", "gdn", "mom", "party",
    "trade", "date", "faith", "science", "accountant", "bid", "win",
    "cricket", "racing", "men",
}

URL_SHORTENERS = {
    "bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "is.gd", "buff.ly",
    "adf.ly", "shorte.st", "rebrand.ly", "cutt.ly", "rb.gy", "shorturl.at",
    "tiny.cc", "lnkd.in", "s.id", "v.gd",
}

# A short list of frequently-impersonated brands. If one of these words
# appears in the URL but NOT as the actual registrable domain, it's a
# classic phishing pattern (e.g. "paypal-secure-login.tk" or
# "appleid.com.verify-account.xyz").
COMMON_BRANDS = {
    "paypal", "apple", "google", "microsoft", "amazon", "netflix", "facebook",
    "instagram", "whatsapp", "bank", "chase", "wellsfargo", "citibank",
    "americanexpress", "ebay", "irs", "outlook", "office365", "dropbox",
    "linkedin", "twitter", "coinbase", "binance", "bankofamerica", "hsbc",
    "adobe", "yahoo", "steam", "spotify",
}

PHISH_HINT_WORDS = {
    "login", "signin", "verify", "update", "secure", "account", "confirm",
    "banking", "webscr", "password", "credential", "suspend", "unlock",
    "reactivate", "billing", "invoice", "security", "alert", "urgent",
}

FEATURE_NAMES = [
    "url_length", "hostname_length", "path_length",
    "has_ip", "nb_dots", "nb_hyphens", "nb_at", "nb_qm", "nb_and", "nb_eq",
    "nb_underscore", "nb_percent", "nb_slash", "nb_www", "nb_com",
    "https_token_in_path", "ratio_digits_url", "ratio_digits_host",
    "punycode", "has_port", "nb_subdomains", "abnormal_subdomain",
    "prefix_suffix", "is_shortened", "suspicious_tld", "nb_hyphens_host",
    "longest_word_length", "avg_word_length", "char_repeat",
    "domain_entropy", "tld_in_subdomain", "brand_in_url_not_domain",
    "phish_hint_count", "is_https", "digit_letter_ratio", "nb_words",
]


def _shannon_entropy(s: str) -> float:
    if not s:
        return 0.0
    freq = {}
    for ch in s:
        freq[ch] = freq.get(ch, 0) + 1
    length = len(s)
    return -sum((c / length) * math.log2(c / length) for c in freq.values())


def _max_char_repeat(s: str) -> int:
    if not s:
        return 0
    max_run = run = 1
    for i in range(1, len(s)):
        if s[i] == s[i - 1]:
            run += 1
            max_run = max(max_run, run)
        else:
            run = 1
    return max_run


def extract_features(url: str) -> list:
    """Returns a list of numeric features, in FEATURE_NAMES order."""
    url = (url or "").strip()
    if not re.match(r"^https?://", url, re.IGNORECASE):
        url = "http://" + url

    parsed = urlparse(url)
    hostname = parsed.netloc.split(":")[0].split("@")[-1].lower()
    path = parsed.path or ""
    full_query = url.split("?", 1)[1] if "?" in url else ""

    # Registrable-ish domain parts (avoid pulling in tldextract's public
    # suffix list here to keep this dependency-free and fast; a simple
    # split is good enough for lexical signal purposes).
    host_parts = hostname.split(".") if hostname else []
    tld = host_parts[-1] if len(host_parts) >= 2 else ""
    domain = host_parts[-2] if len(host_parts) >= 2 else (host_parts[0] if host_parts else "")
    subdomain_parts = host_parts[:-2] if len(host_parts) > 2 else []
    subdomain = ".".join(subdomain_parts)

    has_ip = 1 if re.fullmatch(r"(\d{1,3}\.){3}\d{1,3}", hostname) else 0
    nb_subdomains = len(subdomain_parts)

    words = re.split(r"[/\-_.?=&%]+", url)
    words = [w for w in words if w and w not in ("http", "https")]
    word_lengths = [len(w) for w in words] or [0]

    digits_in_url = sum(c.isdigit() for c in url)
    digits_in_host = sum(c.isdigit() for c in hostname)
    letters_in_url = sum(c.isalpha() for c in url)

    brand_hit = 0
    for brand in COMMON_BRANDS:
        if brand in url.lower() and brand != domain:
            brand_hit = 1
            break

    phish_hint_count = sum(1 for w in PHISH_HINT_WORDS if w in url.lower())

    features = {
        "url_length": len(url),
        "hostname_length": len(hostname),
        "path_length": len(path),
        "has_ip": has_ip,
        "nb_dots": url.count("."),
        "nb_hyphens": url.count("-"),
        "nb_at": url.count("@"),
        "nb_qm": url.count("?"),
        "nb_and": url.count("&"),
        "nb_eq": url.count("="),
        "nb_underscore": url.count("_"),
        "nb_percent": url.count("%"),
        "nb_slash": url.count("/"),
        "nb_www": url.lower().count("www"),
        "nb_com": url.lower().count("com"),
        "https_token_in_path": 1 if "https" in (path + full_query).lower() else 0,
        "ratio_digits_url": digits_in_url / len(url) if url else 0,
        "ratio_digits_host": digits_in_host / len(hostname) if hostname else 0,
        "punycode": 1 if hostname.startswith("xn--") or "xn--" in hostname else 0,
        "has_port": 1 if ":" in parsed.netloc and not parsed.netloc.endswith(":80") and not parsed.netloc.endswith(":443") else 0,
        "nb_subdomains": nb_subdomains,
        "abnormal_subdomain": 1 if nb_subdomains > 2 else 0,
        "prefix_suffix": 1 if "-" in domain else 0,
        "is_shortened": 1 if hostname in URL_SHORTENERS else 0,
        "suspicious_tld": 1 if tld in SUSPICIOUS_TLDS else 0,
        "nb_hyphens_host": hostname.count("-"),
        "longest_word_length": max(word_lengths),
        "avg_word_length": sum(word_lengths) / len(word_lengths),
        "char_repeat": _max_char_repeat(url),
        "domain_entropy": round(_shannon_entropy(domain), 3),
        "tld_in_subdomain": 1 if tld and tld in subdomain.split(".") else 0,
        "brand_in_url_not_domain": brand_hit,
        "phish_hint_count": phish_hint_count,
        "is_https": 1 if url.lower().startswith("https") else 0,
        "digit_letter_ratio": digits_in_url / letters_in_url if letters_in_url else 0,
        "nb_words": len(words),
    }

    return [features[name] for name in FEATURE_NAMES]