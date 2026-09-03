import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    
    TRUSTED_NEWS_SOURCES = [
        # Wire services / global agencies
        "wikipedia.org", "reuters.com", "apnews.com", "afp.com",
        # Major international outlets
        "bbc.com", "bbc.co.uk", "npr.org", "theguardian.com", "cnn.com",
        "nytimes.com", "washingtonpost.com", "wsj.com", "aljazeera.com",
        "dw.com", "france24.com", "cbsnews.com", "abcnews.go.com",
        "nbcnews.com", "economist.com", "time.com", "usatoday.com",
        # Dedicated fact-checkers
        "factcheck.org", "politifact.com", "snopes.com", "fullfact.org",
        "afpfactcheck.com",
        # Science / health / official bodies
        "who.int", "cdc.gov", "un.org", "nasa.gov", "nature.com",
        "science.org",
        # Indian outlets
        "thehindu.com", "timesofindia.indiatimes.com", "indianexpress.com",
        "ndtv.com", "pib.gov.in", "hindustantimes.com",
    ]