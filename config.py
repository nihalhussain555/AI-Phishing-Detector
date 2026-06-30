import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI")
    
    TRUSTED_NEWS_SOURCES = [
        "wikipedia.org",
        "reuters.com",
        "bbc.com",
        "bbc.co.uk",
        "thehindu.com",
        "timesofindia.indiatimes.com",
        "indianexpress.com",
        "ndtv.com",
        "pib.gov.in"
    ]