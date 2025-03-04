import os
from pymongo import MongoClient
import logging
logger = logging.getLogger(__name__) 

class DocumentReference:
    def __init__(self, collection, doc_id):
        self._collection = collection
        self._doc_id = doc_id

    def set(self, data):
        data["_id"] = self._doc_id
        self._collection.replace_one({"_id": self._doc_id}, data, upsert=True)

    def delete(self):
        self._collection.delete_one({"_id": self._doc_id})

class CollectionReference:
    def __init__(self, collection):
        self._collection = collection

    def document(self, doc_id=None):
        return DocumentReference(self._collection, doc_id)

class FirestoreCompatibleClient:
    print("FirestoreCompatibleClient")
    def __init__(self):
        mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
        db_name = os.getenv("MONGO_DB_NAME", "locutus")
        print("Mongo URI: ", mongo_uri)       
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
