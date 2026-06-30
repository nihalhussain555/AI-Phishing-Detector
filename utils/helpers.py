from urllib.parse import urlparse

def is_valid_url(url):
    """Basic check to see if string is a valid URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def ensure_http(url):
    """Ensures the URL starts with http:// or https://."""
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url
