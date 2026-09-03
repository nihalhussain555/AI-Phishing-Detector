"""MongoDB connection helper.

Connects to a MongoDB Atlas free-tier cluster (external, so it costs no
storage/RAM on Render's own instance). Connection is guarded so a bad
MONGO_URI or a temporary network hiccup does not crash the whole app -
routes that use the DB should catch exceptions when calling into it.
"""

import os
import logging

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import PyMongoError

load_dotenv()

logger = logging.getLogger(__name__)

MONGO_URI = os.getenv("MONGO_URI")

client = None
db = None
scans_collection = None
db_available = False

if not MONGO_URI:
    logger.warning(
        "[MongoDB] MONGO_URI is not set. Scan history / dashboard features "
        "will be disabled until it is configured."
    )
else:
    try:
        client = MongoClient(
            MONGO_URI,
            server_api=ServerApi("1"),
            serverSelectionTimeoutMS=5000,  # fail fast instead of hanging the request
            connectTimeoutMS=5000,
        )
        # Force a round trip now so startup fails loudly in logs (but not
        # by crashing the process) rather than on the user's first click.
        client.admin.command("ping")
        db = client["phishing_detector"]
        scans_collection = db["scans"]
        db_available = True
        logger.info("[MongoDB] Connected successfully.")
    except PyMongoError as e:
        logger.error("[MongoDB] Failed to connect: %s", e)
        client = None
        db = None
        scans_collection = None
        db_available = False