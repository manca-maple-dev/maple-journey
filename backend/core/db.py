"""MongoDB connection (Motor) and shared document helpers."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

_mongo_url = os.environ.get("MONGO_URL", "mongodb://localhost:27017")
_db_name = os.environ.get("DB_NAME", "maplejourney")

client = AsyncIOMotorClient(_mongo_url)
db = client[_db_name]


def clean(doc: dict) -> dict:
    """Strip the raw Mongo ObjectId so a document is JSON-serializable."""
    doc = dict(doc)
    doc.pop("_id", None)
    return doc
