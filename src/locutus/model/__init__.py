# Follow KF with the use of nanoid for ID generation.
from copy import deepcopy

from marshmallow import Schema, fields, post_load
from nanoid import generate
from pymongo import ASCENDING

from .datadictionary import DataDictionary
from .global_id import GlobalID
from .reference import Reference
from .serializable import Serializable
from .simple import Simple
from .study import Study
from .table import Table
from .terminology import Terminology

resource_types = {
    str(item.__name__): item for k, item in Serializable._factory_workers.items()
}


simple_types = [
    "GlobalID",
    "Coding",
    "Provenance",
    "Mapping",
    "MappingConversation",
    "MappingVote",
]
