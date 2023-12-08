"""
Just a rudimentary storage mechanism which should be replaced with a true 
database that supports storing objects. Once we have a clear decision on 
what is necessary, we can probably drop this altogether. I'll be mimicking
some basic firestore functionality but using a simple JSON file for initial
local dev testing. 

"""
from collections import defaultdict
from pathlib import Path
from copy import deepcopy
import json


import pdb


class StorageBase:
    def __init__(self, project_id):
        self.project_id = project_id
        self._collections = {}

    def collection(self, key):
        return self._collections[key]


class JStoreCollection:
    """
    TODO: Add aliases to persistence...but only if it makes sense to use them.
          FHIR doesn't do this, so it probably should be a more formal query
          rather than a way to short link using familiar names
    """

    def __init__(self, cname, data=None):
        self.name = cname

        # Just a rudimentary dictionary of dicts
        self.data = defaultdict(dict)

        if data is not None:
            for k, v in data.items():
                self.data[k] = deepcopy(v)

        # Lookup to allow names to point back to IDs for proper reading
        self.aliases = {}

    def documents(self):
        from locutus.model import build_object

        docs = []
        for (
            k,
            v,
        ) in self.data.items():
            docs.append(build_object(v))

        return docs

    def document(self, docid, data=None):
        # Allow an alias be used in place of the ID if the ID isn't already
        # present in the data
        # pdb.set_trace()
        id = docid
        if docid not in self.data and docid in self.aliases:
            id = self.aliases[docid]

        if data is not None:
            self.data[id] = data

        # we don't want to forcibly add this unless we want to actually use it.
        data_chunk = self.data.get(id)
        if data_chunk is None:
            return {}

        return self.data[id]

    def add_aliases(self, aliases, id):
        for alias in aliases:
            if alias not in self.aliases:
                self.aliases[alias] = id


class JStore(StorageBase):
    file_path = Path("db")

    def __init__(self, project_id):
        super().__init__(project_id)
        # pdb.set_trace()
        self._collections = {}

        self.filename = JStore.file_path / f"{self.project_id}.json"

        if self.filename.exists():
            self.load()

    def collection(self, name):
        if name not in self._collections:
            self._collections[name] = JStoreCollection(name)

        return self._collections[name]

    def load(self):
        with self.filename.open("rt") as f:
            data = json.load(f)
            # pdb.set_trace()
            collections = data.get("collections")
            # pdb.set_trace()
            if type(collections) is dict:
                for collection in collections:
                    self._collections[collection] = JStoreCollection(
                        collection, data=collections[collection]
                    )

    def save(self):
        self.filename.parent.mkdir(exist_ok=True, parents=True)
        with self.filename.open("wt") as f:
            data = {"collections": {}}  # self._collections}
            for collection in self._collections.keys():
                data["collections"][collection] = self._collections[collection].data

            json.dump(data, f, indent=2)

    @classmethod
    def data_path(cls, pth):
        cls.file_path = Path(pth)
