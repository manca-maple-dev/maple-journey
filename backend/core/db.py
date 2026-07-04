"""MongoDB connection (Motor) and shared document helpers."""
import os
from motor.motor_asyncio import AsyncIOMotorClient

client = AsyncIOMotorClient(os.environ["MONGO_URL"])
db = client[os.environ["DB_NAME"]]


def clean(doc: dict) -> dict:
    """Strip the raw Mongo ObjectId so a document is JSON-serializable."""
    doc = dict(doc)
    doc.pop("_id", None)
    return doc
