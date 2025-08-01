import os
from pymongo import MongoClient
from locutus import logger
from urllib.parse import urlparse, unquote

import pdb
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
        if not self._data:
            return {}
        # Filter out any database-specific fields (starting with _)
        return {k: v for k, v in self._data.items() if not k.startswith('_')}
    
    def delete(self):
        pdb.set_trace()
        print(self._data)
        print(self.id)


class DocumentReference:
    def __init__(self, collection, doc_id, parent_path=""):
        self._collection = collection
        self._doc_id = doc_id
        self._parent_path = parent_path

    def get(self):
        # Try to find by _id first (MongoDB native way)
        print(f"[DEBUG] Looking for document with _id: {self._doc_id}")
        doc = self._collection.find_one({"_id": self._doc_id})
        if not doc:
            # If not found, try to find by id field (Firestore compatibility)
            print(f"[DEBUG] Not found by _id, trying id field: {self._doc_id}")
            doc = self._collection.find_one({"id": self._doc_id})
        
        if doc:
            # Ensure compatibility with Firestore and MongoDB
            print(f"[DEBUG] Found document: {doc.get('id', 'no-id')} / {doc.get('name', 'no-name')}")
            # Remove all database-specific fields (starting with _)
            doc = {k: v for k, v in doc.items() if not k.startswith('_')}
        else:
            print(f"[DEBUG] Document not found: {self._doc_id}")
        return DocumentSnapshot(self._doc_id, doc)

    def set(self, data):
        # Overwrites the entire document (upsert = True)
        # Use the id field for consistency, and also set _id for MongoDB compatibility
        data["id"] = self._doc_id
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
        # Try to delete by _id first, then by id field for compatibility
        result = self._collection.delete_one({"_id": self._doc_id})
        if result.deleted_count == 0:
            self._collection.delete_one({"id": self._doc_id})
    
    def collection(self, subcollection_name):
        # Implement Firestore-style subcollections using MongoDB collection naming convention
        # Format: parent_collection__parent_doc_id__subcollection_name
        current_collection_name = self._collection.name
        subcollection_full_name = f"{current_collection_name}__{self._doc_id}__{subcollection_name}"
        
        # Get the database instance from the current collection
        db = self._collection.database
        subcollection = db[subcollection_full_name]
        
        # Create path for nested subcollections
        new_parent_path = f"{self._parent_path}/{current_collection_name}/{self._doc_id}" if self._parent_path else f"{current_collection_name}/{self._doc_id}"
        
        return CollectionReference(subcollection, parent_path=new_parent_path)


class CollectionReference:
    def __init__(self, collection, parent_path=""):
        self._collection = collection
        self._parent_path = parent_path
    
    def stream(self):
        """Stream all documents in the collection (for Firestore compatibility)"""
        for doc in self._collection.find():
            doc_id = doc.get('_id') or doc.get('id')
            # Remove all database-specific fields (starting with _)
            filtered_doc = {k: v for k, v in doc.items() if not k.startswith('_')}
            yield DocumentSnapshot(doc_id, filtered_doc)
    
    def find(self, query=None):
        """Find documents matching the query - returns raw dictionaries for direct use"""
        if query is None:
            query = {}
        for doc in self._collection.find(query):
            # Remove all database-specific fields (starting with _)
            yield {k: v for k, v in doc.items() if not k.startswith('_')}
    
    def find_one(self, query=None):
        """Find one document matching the query - returns raw dictionary for direct use"""
        if query is None:
            query = {}
        doc = self._collection.find_one(query)
        if doc:
            # Remove all database-specific fields (starting with _)
            return {k: v for k, v in doc.items() if not k.startswith('_')}
        return None
    
    def document(self, doc_id=None):
        return DocumentReference(self._collection, doc_id, self._parent_path)
    
    def add_aliases(self, keys, doc_id):
        doc = self._collection.find_one({"_id": doc_id})
        aliases = doc.get("aliases", []) if doc else []
        updated_aliases = list(set(aliases) | set(keys))
        self._collection.update_one(
            {"_id": doc_id},
            {"$set": {"aliases": updated_aliases}},
            upsert=True
        )

    def list_documents(self, page_size):
        return [doc for doc in self.stream()]


class FirestoreCompatibleClient:
    print("FirestoreCompatibleClient")
    def __init__(self, mongo_uri=None, missing_ok=False):
        # Prefer FIRESTORE_MONGO_URI, fallback to MONGO_URI
        # pdb.set_trace()
        if mongo_uri is None:
            mongo_uri = os.getenv("FIRESTORE_MONGO_URI") or os.getenv("MONGO_URI", "mongodb://localhost:27017/locutus")
        parsed = urlparse(mongo_uri)
        db_name = unquote(parsed.path.lstrip("/")) if parsed.path else None
        logger.info(f"Mongo DB Interface")
        logger.info(f"Connecting to Mongo URI: {mongo_uri}")
        logger.info(f"Database name parsed: '{db_name}'")
        if not db_name:
            raise ValueError("Database name must be specified in the Mongo URI path!")
        self.client = MongoClient(mongo_uri)
        available_dbs = self.client.list_database_names()

        if db_name not in available_dbs:
            if not missing_ok:
                raise ValueError(f"The specified database, {db_name}, isn't present in the database. Available DBs include: {', '.join(self.client.list_database_names())}")            
            logger.info(f"Database, {db_name}, not currently found.")
        self.db = self.client[db_name]
        self.collection_list = self.db.list_collection_names()
        logger.info(f"List of database collections in the connected DB: {', '.join(self.collection_list)}")


    def collection(self, collection_name):
        if collection_name not in self.collection_list:
            logger.info(f"{collection_name} is not present in the database. Available collections are:")
            collection_names = "\n *".join(self.collection_list)
            msg = f"  * {collection_names}"
            logger.info(msg)
            
            raise KeyError(msg)
        return CollectionReference(self.db[collection_name])

# Maintain singleton client instance
_client = None

def persistence(mongo_uri=None, missing_ok=False):
    global _client
    if _client is None:
        _client = FirestoreCompatibleClient(mongo_uri, missing_ok)
    return _client
