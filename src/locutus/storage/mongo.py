import os
from pymongo import MongoClient
import logging
from urllib.parse import urlparse, unquote
logger = logging.getLogger(__name__) 

class DocumentSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def data(self):
        return self._data

    def to_dict(self):
        return self._data if self._data else {}


class DocumentReference:
    def __init__(self, collection, doc_id):
        self._collection = collection
        self._doc_id = doc_id

    def get(self):
        doc = self._collection.find_one({"_id": self._doc_id})
        return DocumentSnapshot(self._doc_id, doc)

    def set(self, data):
        # Overwrites the entire document (upsert = True)
        data["_id"] = self._doc_id
        self._collection.replace_one({"_id": self._doc_id}, data, upsert=True)

    def update(self, fields):
        # Merges fields into existing doc
        self._collection.update_one(
            {"_id": self._doc_id},
            {"$set": fields},
            upsert=False
        )

    def delete(self):
        self._collection.delete_one({"_id": self._doc_id})


class CollectionReference:
    def __init__(self, collection):
        self._collection = collection
    
    def stream(self):
        return self._collection.find()
    
    def document(self, doc_id=None):
        return DocumentReference(self._collection, doc_id)
    
    def add_aliases(self, keys, doc_id):
        doc = self._collection.find_one({"_id": doc_id})
        aliases = doc.get("aliases", []) if doc else []
        updated_aliases = list(set(aliases) | set(keys))
        self._collection.update_one(
            {"_id": doc_id},
            {"$set": {"aliases": updated_aliases}},
            upsert=True
        )


class FirestoreCompatibleClient:
    print("FirestoreCompatibleClient")
    def __init__(self):
        # Prefer FIRESTORE_MONGO_URI, fallback to MONGO_URI
        mongo_uri = os.getenv("FIRESTORE_MONGO_URI") or os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        parsed = urlparse(mongo_uri)
        db_name = unquote(parsed.path.lstrip("/")) if parsed.path else None
        logger.info(f"Connecting to Mongo URI: {mongo_uri}")
        logger.info(f"Database name parsed: '{db_name}'")
        if not db_name:
            raise ValueError("Database name must be specified in the Mongo URI path!")
        self.client = MongoClient(mongo_uri)
        self.db = self.client[db_name]

    def collection(self, collection_name):
        return CollectionReference(self.db[collection_name])

# Maintain singleton client instance
_client = None

def persistence():
    global _client
    if _client is None:
        _client = FirestoreCompatibleClient()
    return _client
