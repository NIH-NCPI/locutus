# from locutus import logger
import logging
import os
import re
from datetime import UTC, datetime
from typing import ClassVar, cast
from urllib.parse import unquote, urlparse

from bson import ObjectId
from bson.errors import InvalidId
from pymongo import MongoClient

logger = logging.getLogger(__name__)

uri_filter = re.compile(r"(mongodb:\/\/[^:]*:)([^@]*)(@)")


class DocumentSnapshot:
    def __init__(self, doc_id, data, collection):
        self.id = doc_id
        self._data = data
        self._collection = collection

    @property
    def exists(self):
        return self._data is not None

    def data(self):
        return self._data

    def to_dict(self):
        if not self._data:
            return {}
        # Filter out any database-specific fields (starting with _)
        this = {k: v for k, v in self._data.items()}  # if not k.startswith('_')}
        if "id" not in this:
            this["id"] = str(this["_id"])
        return this

    def delete(self):
        self._collection.delete_one({"_id": ObjectId(self.id)})


class DocumentReference:
    def __init__(self, collection, doc_id, parent_path=""):
        self._collection = collection
        self._doc_id = doc_id
        self._parent_path = parent_path

    def get(self):
        # Try to find by _id first (MongoDB native way). A doc_id that
        # isn't a valid ObjectId (a custom/nanoid-style id, or simply a
        # nonexistent one) falls through to the id-field lookup below
        # instead of raising -- this method must return a "doesn't exist"
        # snapshot for a bad id, not crash.
        try:
            doc = self._collection.find_one({"_id": ObjectId(self._doc_id)})
        except InvalidId:
            doc = None

        if not doc:
            # If not found, try to find by id field (Firestore compatibility)
            doc = self._collection.find_one({"id": str(self._doc_id)})

        if doc:
            # Ensure compatibility with Firestore and MongoDB
            # Remove all database-specific fields (starting with _)
            doc = {k: v for k, v in doc.items()}  # if not k.startswith('_')}
            if "id" not in doc:
                doc["id"] = doc["_id"]
        return DocumentSnapshot(self._doc_id, doc, collection=self._collection)

    def set(self, data):
        # Overwrites the entire document (upsert = True)
        # Use the id field for consistency, and also set _id for MongoDB compatibility
        if self._doc_id:
            data["_id"] = ObjectId(self._doc_id)
            if "id" not in data:
                data["id"] = self._doc_id
            self._collection.replace_one(
                {"_id": ObjectId(self._doc_id)}, data, upsert=True
            )
        else:
            _id = self._collection.insert_one(data)
            data["_id"] = str(_id.inserted_id)
            data["id"] = data["_id"]

        return data["_id"]

    def update(self, fields):
        # Merges fields into existing doc. _id is stored as an ObjectId, so
        # the query must wrap doc_id the same way .get()/.delete() do below --
        # matching on the bare string would silently match nothing.
        self._collection.update_one(
            {"_id": ObjectId(self._doc_id)}, {"$set": fields}, upsert=False
        )

    def delete(self):
        # Try to delete by _id first, then by id field for compatibility
        result = self._collection.delete_one({"_id": ObjectId(self._doc_id)})
        if result.deleted_count == 0:
            result = self._collection.delete_one({"id": ObjectId(self._doc_id)})
        return result

    def collection(self, subcollection_name):
        # Implement Firestore-style subcollections using MongoDB collection naming convention
        # Format: parent_collection__parent_doc_id__subcollection_name
        current_collection_name = self._collection.name
        subcollection_full_name = (
            f"{current_collection_name}__{self._doc_id}__{subcollection_name}"
        )

        # Get the database instance from the current collection
        db = self._collection.database
        subcollection = db[subcollection_full_name]

        # Create path for nested subcollections
        new_parent_path = (
            f"{self._parent_path}/{current_collection_name}/{self._doc_id}"
            if self._parent_path
            else f"{current_collection_name}/{self._doc_id}"
        )

        return CollectionReference(subcollection, parent_path=new_parent_path)


class CollectionReference:
    def __init__(self, collection, parent_path=""):
        self._collection = collection
        self._parent_path = parent_path

    def stream(self):
        """Stream all documents in the collection (for Firestore compatibility)"""
        for doc in self._collection.find():
            doc_id = doc.get("_id") or doc.get("id")
            # Remove all database-specific fields (starting with _)
            filtered_doc = {k: v for k, v in doc.items()}  # if not k.startswith('_')}
            yield DocumentSnapshot(doc_id, filtered_doc, collection=self._collection)

    def find(self, query=None, sorting=None, return_instance=True):
        """Find documents matching the query - returns raw dictionaries for direct use"""
        if query is None:
            query = {}

        qresult = self._collection.find(query)
        if sorting is not None:
            qresult = qresult.sort(sorting)
        for doc in qresult:
            if return_instance:
                yield DocumentSnapshot(doc["_id"], doc, collection=self._collection)
            else:
                yield doc

    def find_one(self, query=None):
        """Find one document matching the query - returns raw dictionary for direct use"""
        if query is None:
            query = {}
        doc = self._collection.find_one(query)
        if doc:
            # Remove all database-specific fields (starting with _)
            return {k: v for k, v in doc.items() if not k.startswith("_")}
        return None

    def document(self, doc_id=None):
        return DocumentReference(self._collection, doc_id, self._parent_path)

    def add_aliases(self, keys, doc_id):
        doc = self._collection.find_one({"_id": doc_id})
        aliases = doc.get("aliases", []) if doc else []
        updated_aliases = list(set(aliases) | set(keys))
        self._collection.update_one(
            {"_id": doc_id}, {"$set": {"aliases": updated_aliases}}, upsert=True
        )

    def list_documents(self, page_size):
        return [doc for doc in self.stream()]

    def create_index(self, keys):
        return self._collection.create_index(keys)


def filter_uri(uri):
    return uri_filter.sub(r"\1****\3", uri)


class FirestoreCompatibleClient:
    logger.info("FirestoreCompatibleClient")
    from locutus.model import resource_types, simple_types

    allowed_collections: ClassVar[set] = set(
        list(resource_types.keys())
        + simple_types
        + ["OntologyAPI", "User", "Institution", "ApiToken"]
    )

    def __init__(self, mongo_uri=None, missing_ok=False):
        if mongo_uri is None:
            mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017/locutus")

        print(f"Mongo DB URI: {filter_uri(mongo_uri)}")
        parsed = urlparse(filter_uri(mongo_uri))
        db_name = unquote(parsed.path.lstrip("/")) if parsed.path else None

        logger.info(f"Database name parsed: '{db_name}'")
        if not db_name:
            raise ValueError("Database name must be specified in the Mongo URI path!")
        self.client = MongoClient(mongo_uri)
        available_dbs = self.client.list_database_names()

        if db_name not in available_dbs:
            if not missing_ok:
                raise ValueError(
                    f"The specified database, {db_name}, isn't present in the database. Available DBs include: {', '.join(self.client.list_database_names())}"
                )
            logger.error(f"Database, {db_name}, not currently found.")
        self.db = self.client[db_name]
        self.db_name = db_name
        self.collection_list = self.db.list_collection_names()
        logger.info(
            f"List of database collections in the connected DB: \n{', '.join(self.collection_list)}"
        )

    def collection(self, collection_name):
        if collection_name not in FirestoreCompatibleClient.allowed_collections:
            collection_names = "\n *".join(
                FirestoreCompatibleClient.allowed_collections
            )
            msg = f"{collection_name} is not present in the database. Available collections are:\n * {collection_names}"
            logger.info(msg)

            raise KeyError(msg)
        return CollectionReference(self.db[collection_name])

    # ── Auth abstraction-layer methods ──────────────────────────────────
    # Named query/mutation helpers for auth code (locutus/auth.py) to call,
    # so auth logic never touches pymongo/Firestore directly and keeps
    # working unmodified on both backends.

    def get_user(self, user_id):
        """Fetch a user document by id, or None if it doesn't exist."""
        snapshot = self.collection("User").document(user_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def get_resource(self, resource_type, resource_id):
        """Fetch any resource document (ownerId, access, visibility) by its
        collection name and id, or None if it doesn't exist. Used by the
        access decorators without needing the full model class."""
        snapshot = self.collection(resource_type).document(resource_id).get()
        return snapshot.to_dict() if snapshot.exists else None

    def get_api_token(self, token_hash):
        """Fetch an API token document by its hash, or None if not found."""
        return self.collection("ApiToken").find_one({"tokenHash": token_hash})

    def create_api_token(self, token_doc):
        """Insert a new API token document, returning its generated id."""
        return self.collection("ApiToken").document().set(token_doc)

    def list_api_tokens(self, user_id):
        """List a user's API tokens, never including the token hash."""
        # return_instance=False makes find() yield plain dicts, but its
        # signature doesn't say so -- cast rather than widen a shared method
        # nothing else here depends on.
        tokens = cast(
            "list[dict]",
            list(
                self.collection("ApiToken").find(
                    {"userId": user_id}, return_instance=False
                )
            ),
        )
        return [
            {k: v for k, v in token.items() if k != "tokenHash"} for token in tokens
        ]

    def delete_api_token(self, token_id, user_id):
        """Delete a token if it belongs to user_id.

        Returns True if deleted, False if the token doesn't exist or
        belongs to someone else -- callers use this to distinguish "already
        gone" from "not yours" without a second lookup.
        """
        snapshot = self.collection("ApiToken").document(token_id).get()
        if not snapshot.exists or snapshot.to_dict().get("userId") != user_id:
            return False
        snapshot.delete()
        return True

    def update_token_last_used(self, token_id):
        """Best-effort update of a token's lastUsedAt timestamp. Callers
        should not block a request waiting on this."""
        self.collection("ApiToken").document(token_id).update(
            {"lastUsedAt": datetime.now(UTC)}
        )


# Maintain singleton client instance
_client = None


def persistence(mongo_uri=None, missing_ok=True):
    global _client

    if _client is None:
        _client = FirestoreCompatibleClient(mongo_uri, missing_ok)
    return _client
