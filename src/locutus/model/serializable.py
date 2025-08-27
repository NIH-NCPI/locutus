
from copy import deepcopy

import locutus 
import locutus.model.global_id
from pymongo import ASCENDING

# from . import get_id

import pdb

class Serializable:
    _schema = None
    # Register each of our data_types with their corresponding class for
    # deserialization
    _factory_workers = {}

    def __init__(self, id=None, _id=None, collection_type=None, resource_type=None):
        self.id = id
        # For Simple objects, we won't have an actual ID, we'll keep both, but here, 
        # we are requiring an ID is present for all Serializable. _id will be created
        # when the data hits the db if it is None
        self._id = _id 
        if type(self._id) is dict:
            self._id = self._id['$oid']

        # This is used to identify the persistence source
        self._collection_type = collection_type

        # This is used to identify the resource type to the client
        self.resource_type = resource_type


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
    def pull(cls, resource_type, id, return_instance=True):
        """Works like get except that it uses resource_type to select the right class"""
        resource_class = cls._factory_workers[resource_type.lower()]

        return resource_class.get(id=id, return_instance=return_instance)

    @classmethod
    def get(cls, id=None, return_instance=True):
        """Pull instance from the database and (default) instantiate"""

        # Return all items of this type.
        if id is None:
            serializables = []

            for item in locutus.persistence().collection(cls.__name__).stream():
                item = item.to_dict()
                if return_instance:
                    serializables.append(cls(**item))
                else:
                    serializables.append(item)
            return serializables

        # Return a single resource
        resource = cls.find(params={"id": id}, return_instance=return_instance)

        if len(resource) == 0:
            return None

        return resource[0]

    def identify(self):
        if self.id is None:
            gid = locutus.model.global_id.GlobalID(resource_type=self.resource_type, key=":".join(self.keys()))
            self.id = gid.id

    def save(self):
        # commit the data to persistent storage
        
        if self._id is None and id is not None:
            id_matches = self.__class__.get(self.id, return_instance=False)
            if id_matches is not None and len(id_matches) > 0:
                if type(id_matches) is list:
                    id_matches = id_matches[0]
                self._id = id_matches['_id']

        self._id = locutus.persistence().collection(self.resource_type).document(self._id).set(self.dump())

    def dump(self):
        return self.__class__._get_schema().dump(self)

    def load(self, resource):
        # We probably will want to use the schema to validate this first
        self.__init__(**resource)

    def all(self):
        locutus.persistence().collection(self.resource_type).documents()

    # Returns 1 or more keys, the first of which is recognized as the primary
    # and all subsequent keys are useful lookups. The primary key is what is
    # used to generate the unique ID
    def keys(self):
        return None

    def global_id(self):
        gid = locutus.model.global_id.GlobalID(resource_type=self.resource_type, key=":".join(self.keys()))
        return gid 


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

    def delete(self, hard_delete=True):
        if not hard_delete:
            self.valid = False 
            self.save()
            t = self.to_dict()
        else:
            dref = locutus.persistence().collection(self._collection_type).document(self._id)
            t = dref.get().to_dict()

            time_of_delete = dref.delete()

        return t
