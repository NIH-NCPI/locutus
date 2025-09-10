from copy import deepcopy

import locutus #import persistence
from pymongo import ASCENDING
from rich import print
from bson import ObjectId
# from . import get_id

import inspect

class Simple:
    """Similar in some ways to serializables but these will be only retrievable by searches not by usable IDs"""
    _schema = None 
    _factory_workers = {}

    def __init__(self, _id=None, id=None, collection_type=None, resource_type=None):
        self.id = id 
        self._id = _id
        if type(self._id) is dict:
            self._id = ObjectId(self._id['$oid'])
        if id is None and _id is not None:
            self.id = str(_id)
        elif id is not None and _id is None:
            self._id = ObjectId(id)
        self._collection_type = collection_type 
        self.resource_type = resource_type 

    @classmethod 
    def pull(cls, resource_type, id, return_instance=True):
        resource_class = cls._factory_workers[resource_type.lower()]
        return resource_class.get(_id=id, return_instance=return_instance)

    @classmethod
    def find(cls, params, sorting=None, return_instance=True):
        """Pull instance from the database and (default) instantiate"""

        items = []

        # Return a single resource
        cref = locutus.persistence().collection(cls.__name__)
        for item in cref.find(params, sorting=sorting):
            item = item.to_dict()
            if return_instance:
                items.append(cls(**item))
            else:
                items.append(item)

        return items

    @classmethod
    def index_list(cls):
        "This should be overridden by all derived classes. This is a list of lists where the inner list contains the tuples (key, dir) for each compound index"
        return []

    @classmethod 
    def create_indexes(cls):
        index_items = cls.index_list()

        for idx in index_items:
            collection.create_index(idx)
        # For now, let's not do this. I suspect nothing really needs this sort of work done. We'll explicity enumerate all valid indexes
        """
        for idx in index_items:
            while len(idx) 0 :
                collection.create_index(idx)

                idx.pop(0)
        """

    def save(self):
        # commit the data to persistent storage
        self._id = locutus.persistence().collection(self.resource_type).document(self._id).set(self.dump())
        self.id = str(self._id)
        if self.resource_type == "Coding":
            print(f"\n\n\n{self.resource_type}:{self._id} (from: {inspect.stack()[1]})")
            print(f"{self.id} Save")
            print(self.dump())
            print("--------------------------")

    def dump(self):
        return self.__class__._get_schema().dump(self)

    def load(self, resource):
        # We probably will want to use the schema to validate this first
        self.__init__(**resource)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._factory_workers[cls.__name__.lower()] = cls

    @classmethod
    def init(cls, resource):
        return cls._get_schema().load(resource)

    @classmethod
    def _get_schema(cls):
        if cls._schema is None:
            cls._schema = cls._Schema()
            cls._schema._parent = cls
        return cls._schema

    @classmethod
    def build_object(cls, data):
        d = deepcopy(data)

        if "resource_type" in d:
            del d["resource_type"]
        return cls._factory_workers[data["resource_type"].lower()](**d)
    
    def delete(self, hard_delete=False):
        if hasattr(self, 'valid') and not hard_delete:
            self.valid =False 
            self.save()
            t = self.to_dict()
        else:
            dref = locutus.persistence().collection(self.__class__.__name__).document(self._id)
            t = dref.get().to_dict()

            time_of_delete = dref.delete()
        return t