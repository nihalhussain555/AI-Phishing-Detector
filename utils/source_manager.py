from config import Config
from urllib.parse import urlparse
import tldextract

class SourceManager:
    """Manages the whitelist of trusted domains."""

    def __init__(self):
        self.trusted_sources = Config.TRUSTED_NEWS_SOURCES

    def is_trusted(self, url):
        """Checks if a URL belongs to a trusted source."""
        try:
            ext = tldextract.extract(url)
            domain = f"{ext.domain}.{ext.suffix}"
            return domain in self.trusted_sources
        except Exception:
            return False

    def add_source(self, domain):
        """Adds a new domain to the trusted sources list."""
        if domain not in self.trusted_sources:
            self.trusted_sources.append(domain)

    def remove_source(self, domain):
        """Removes a domain from the trusted sources list."""
        if domain in self.trusted_sources:
            self.trusted_sources.remove(domain)

    def get_sources(self):
        """Returns the current list of trusted sources."""
        return self.trusted_sources
