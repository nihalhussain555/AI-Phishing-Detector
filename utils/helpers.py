from urllib.parse import urlparse
import requests


def is_valid_url(url):
    """Basic check to see if string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def normalize_url(raw_url: str) -> str:
    """Turns user input like 'example.com' into a fully-qualified URL.

    Users only need to type the domain (e.g. 'paypal.com') - no 'https://'
    required. If a scheme is already given, it's left untouched. Otherwise
    we prefer HTTPS (the modern default for virtually all legitimate sites)
    and only fall back to HTTP if the site doesn't respond on HTTPS at all.
    Using the wrong scheme here would make the HTTPS/trust checks downstream
    inaccurate, so this check matters for scoring, not just convenience.
    """
    url = (raw_url or "").strip()
    if not url:
        return url

    if url.lower().startswith(("http://", "https://")):
        return url

    # Strip any accidental leading slashes/@ (e.g. pasted "www.example.com/")
    url = url.lstrip("/")

    https_url = "https://" + url
    try:
        requests.head(https_url, timeout=5, allow_redirects=True)
        return https_url
    except requests.exceptions.RequestException:
        return "http://" + url


def ensure_http(url):
    """Deprecated alias kept for backward compatibility - prefer normalize_url."""
    return normalize_url(url)