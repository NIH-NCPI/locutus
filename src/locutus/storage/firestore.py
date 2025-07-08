import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

from rich import print

import os

_db = None

# This doesn't work for sub-collections. We have to know to delete
# those as well. At this time, there are none to worry about.
def delete_collection(coll):
    for doc in coll.list_documents():
        doc.delete()


def persistence():
    global _db
    if _db is None:
        # On my local machine, I'll use an environment variable to store the path to my
        # service account credentials. However, GCP itself, we'll use a different
        # mechanism to authorize the application
        cert = None
        if "FSSA" in os.environ:
            cert = credentials.Certificate(os.environ["FSSA"])

        else:
            cert = credentials.ApplicationDefault()

        app = firebase_admin.initialize_app(cert)
        _db = firestore.client()
    return _db
