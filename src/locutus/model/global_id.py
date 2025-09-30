import locutus
from pymongo import ASCENDING
from marshmallow import Schema, fields, post_load
from nanoid import generate
from .simple import Simple

"""
{
    resource_type: XXXXXXXXX,   # Terminology, DataDictionary, etc
    key: YYYYYYYYYYY,           # Unique properties that define a unique instance of this entity
    id: ZZZZZZZZZZ,             # global ID assocaited with the entity
    object_id: WWWWWWWWWWWW     # DB Specific ID for the entity (may be specific to this database instance)
}

"""

class GlobalID(Simple):
    _schema = None
    global resource_types
    
    def __init__(self, resource_type, key, domain="", id=None, object_id=None, _id=None):
        if not isinstance(resource_type, str) or not resource_type.strip():
            raise ValueError("resource_type is required for all Global IDs.")
        if not isinstance(key, str) or not key.strip():
            raise ValueError("key is required for all Global IDs.")
        if resource_type not in locutus.model.resource_types:
            resource_list = ",".join(locutus.model.resource_types.keys())
            raise ValueError(f"resource_type, '{resource_type} is not a valid resource type. Available options include: {resource_list}")
        self.resource_type = resource_type 
        self.key = key 
        self.domain = domain
        self.id = id 
        self.object_id = object_id 
        self._id = _id 

        resource = GlobalID.find(resource_type, key=key, domain=domain, return_instance=False)

        if resource is not None:
            if id is None:
                self.id = resource['id'] 
            
            if _id is None:
                self._id = resource['_id']

            if object_id is None:
                self.object_id = resource['object_id']

        if self.id is None:
            self.id = f"{locutus.model.resource_types[resource_type]._id_prefix}-{generate()}"
            self.save()

    def save(self):
        # commit the data to persistent storage
        if self._id is None:
            id_matches = self.__class__.find(resource_type=self.resource_type, key=self.key)
            if id_matches is not None and len(id_matches) > 0:
                self._id = id_matches[0]['_id']
        self._id = locutus.persistence().collection(self.__class__.__name__).document(self._id).set(self.dump())

    def dump(self):
        return self.__class__._get_schema().dump(self)

    @classmethod
    def load(self, resource):
        # We probably will want to use the schema to validate this first
        self.__init__(**resource)

    @classmethod
    def find(cls, resource_type, key=None, domain="", return_instance=True):
        params = {
            "resource_type": resource_type,
            "domain": domain
        }

        if key is not None:
            params["key"] = key

        cref = locutus.persistence().collection(cls.__name__)
        search_results = []
        for item in cref.find(params, return_instance=return_instance):
            if type(item) is not dict:
                item = item.to_dict()
            if return_instance:
                search_results.append(cls(**item))
            else:
                search_results.append(item)
        if len(search_results) == 1:
            return search_results[0]
        elif len(search_results) > 1:
            return search_results
        
        return None

    @classmethod
    def index_list(cls):
        "For codings, we must have either a terminology or system and the code"
        return [
            [("resource_type", 1), ("domain", 1), ('key', 1)]
        ]

    class _Schema(Schema):
        id = fields.Str()
        resource_type = fields.Str(required=True)
        key = fields.Str(required=True)
        domain = fields.Str(required=True)
        # This is the stringfied id
        object_id = fields.Str()

        @post_load
        def build_object(self, data, **kwargs):
            return GlobalID(**data)
    
    @classmethod
    def _get_schema(cls):
        if cls._schema is None:
            cls._schema = cls._Schema()
            cls._schema._parent = cls
        return cls._schema
