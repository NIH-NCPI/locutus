import pdb

# Follow KF with the use of nanoid for ID generation.
from nanoid import generate
from copy import deepcopy

# By default, we'll use a dumb JSON cache for storage
from locutus.storage import JStore


"""
The application should set this to the desired 
"""
_datastore = None


def persistence(datastore=None):
    global _datastore
    if datastore is not None:
        _datastore = datastore

    # if we don't have a valid persistence, we'll default to
    # JSON based cache
    if _datastore is None:
        _datastore = JStore("~~tmp~~")

    return _datastore


def build_object(resource):
    return Serializable.build_object(resource)


# TODO Build a cache and a way to perform ID lookups so that we can safely
# reapply a pre-existing ID
def get_id(resource):
    id = resource.id
    if id is None:
        perc = persistence()

        if perc is not None:
            keys = resource.keys()
            assert keys is not None, "Incomplete Serializable Object-No Key Returned"

            doc = perc.collection(resource.resource_type).document(keys[0])
            if doc is not None and doc.get("id") is None:
                id = f"{type(resource)._id_prefix}-{generate()}"
                print(f"New ID ({keys[0]}): {id}")
                doc["id"] = id
                perc.collection(resource.resource_type).document(id, doc)
                perc.collection(resource.resource_type).add_aliases(keys, id)
            else:
                id = doc.get("id")

        else:
            id = f"{type(resource)._id_prefix}-{generate()}"

    return id


class Serializable:
    _schema = None
    # Register each of our data_types with their corresponding class for
    # deserialization
    _factory_workers = {}

    def __init__(self, id=None, collection_type=None, resource_type=None):
        self.id = id

        # This is used to identify the persistence source
        self._collection_type = collection_type

        # This is used to identify the resource type to the client
        self.resource_type = resource_type

    def identify(self):
        if self.id is None:
            self.id = get_id(self)

    def save(self):
        # commit the data to persistent storage
        persistence().collection(self.resource_type).document(self.id, data=self.dump())

    def dump(self):
        # pdb.set_trace()
        return self.__class__._get_schema().dump(self)

    def load(self, resource):
        # We probably will want to use the schema to validate this first
        self.__init__(**resource)

    def all(self):
        persistence().collection(self.resource_type).documents()

    # Returns 1 or more keys, the first of which is recognized as the primary
    # and all subsequent keys are useful lookups. The primary key is what is
    # used to generate the unique ID
    def keys(self):
        return None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        # pdb.set_trace()
        cls._factory_workers[cls.__name__.lower()] = cls

    @classmethod
    def init(cls, resource):
        return cls._get_schema().load(resource)
        # pdb.set_trace()

    @classmethod
    def _get_schema(cls):
        if cls._schema is None:
            cls._schema = cls._Schema()
            cls._schema._parent = cls
        return cls._schema

    @classmethod
    def build_object(cls, data):
        d = deepcopy(data)
        del d["resource_type"]
        return cls._factory_workers[data["resource_type"].lower()](**d)
