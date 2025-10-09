# Follow KF with the use of nanoid for ID generation.
from nanoid import generate
from copy import deepcopy

from pymongo import ASCENDING
from marshmallow import Schema, fields, post_load

from .global_id import GlobalID
from .simple import Simple
from .serializable import Serializable 
from .datadictionary import DataDictionary 
from .reference import Reference 
from .study import Study 
from .table import Table 
from .terminology import Terminology 

import pdb

resource_types = dict([(str(item.__name__), item) for k, item in Serializable._factory_workers.items()])


simple_types = [
    "GlobalID", 
    "Coding",
    "Provenance",
    "Mapping",
    "MappingConversation",
    "MappingVote"
]

