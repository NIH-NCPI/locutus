# Follow KF with the use of nanoid for ID generation.
from nanoid import generate
from copy import deepcopy

from locutus import persistence

"""
The application should set this to the desired 
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
"""


def build_object(resource):
    return Serializable.build_object(resource)


# TODO Build a cache and a way to perform ID lookups so that we can safely
# reapply a pre-existing ID
def get_id(resource):
    id = resource.id
    perc = persistence()
    keys = resource.keys()

    if id is None:
        if perc is not None:
            assert keys is not None, "Incomplete Serializable Object-No Key Returned"
            doc = (
                perc.collection(resource.resource_type)
                .document(keys[0].replace("/", "_"))
                .get()
                .to_dict()
            )
            if doc is not None:
                if doc.get("id") is None:
                    id = f"{type(resource)._id_prefix}-{generate()}"

                    # TBD
                    # Do we really want to record the record at this time? It seems
                    # a bit heavy in terms of side-effects for a get_id function...
                    doc["id"] = id
                    perc.collection(resource.resource_type).document(id).set(doc)
                    perc.collection(resource.resource_type).add_aliases(keys, id)
                else:
                    id = doc.get("id")

        if id is None:
            id = f"{type(resource)._id_prefix}-{generate()}"

    else:
        perc.collection(resource.resource_type).document(id).set(doc)
        perc.collection(resource.resource_type).add_aliases(keys, id)
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

    @classmethod
    def get(cls, id=None, return_instance=True):
        """Pull instance from the database and (default) instantiate"""

        # Return all items of this type.
        if id is None:
            serializables = []

            for item in persistence().collection(cls.__name__).stream():
                item = item.to_dict()
                if return_instance:
                    serializables.append(cls(**item))
                else:
                    serializables.append(item)
            return serializables

        # Return a single resource
        resource = persistence().collection(cls.__name__).document(id).get().to_dict()

        # Just in case we just need the dict representation as it is found in
        # the database.
        if not return_instance:
            return resource

        return cls(**resource)

    def identify(self):
        if self.id is None:
            self.id = get_id(self)

    def save(self):
        # commit the data to persistent storage
        persistence().collection(self.resource_type).document(self.id).set(self.dump())

    def dump(self):
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
