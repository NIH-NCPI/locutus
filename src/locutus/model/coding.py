
from .simple import Simple
from marshmallow import Schema, fields, post_load
from pymongo import ASCENDING
from locutus.model.lookups import FTDConceptMapTerminology, FTDOntologyLookup
# from locutus.model.onto_api_preference import OntoApiPreference

from bson import ObjectId
from collections import defaultdict 

import pdb

import locutus 
"""import (
    normalize_ftd_placeholders,
    persistence
)"""

class BasicCoding:
    def __init__(self, code, display, system, description=""):

        if display is None:
            display = ""
        if description is None:
            description = ""
        self.code = code.strip()
        self.display = display.strip()
        self.system = system.strip()
        self.description = description.strip()

    class _Schema(Schema):
        code = fields.Str(
            required=True, error_messages={"required": "Codings *must* have a code "}
        )
        display = fields.Str()
        system = fields.URL()
        description = fields.Str()

        @post_load
        def build_coding(self, data, **kwargs):
            return BasicCoding(**data)

    def to_dict(self):
        obj = {"code": self.code, "display": self.display}

        if self.description != "":
            obj["description"] = self.description

        if self.system is not None:
            obj["system"] = self.system

        return obj


class CodingMapping(BasicCoding):
    """
    Inherits Terminonlogy.Coding. Adds mapping specific attributes.
    Note: Placed here to avoid circular imports. Move only with refactor.
    """

    def __init__(
        self,
        code,
        display=None,
        system=None,
        description="",
        valid=None,
        rank=None,
        mapping_relationship=None,
        user_input=None,
        ftd_code=None
    ):
        super().__init__(code=code, display=display, system=system, description=description)
        self.rank = rank
        self.valid = valid
        self.user_input = user_input
        self.ftd_code = code # Default to given code, updated if necessary. 

        FTDConceptMapTerminology().validate_codes_against(mapping_relationship, additional_enums=[""])
        self.mapping_relationship = mapping_relationship

    class _Schema(Schema):
        code = fields.Str(
            required=True, error_messages={"required": "CodingMappings *must* have a code "}
        )
        display = fields.Str()
        system = fields.URL(
            required=True, error_messages={"required": "CodingMappings *must* have a system "}
        )
        description = fields.Str()
        valid = fields.Bool()
        mapping_relationship = fields.Str()
        user_input = fields.Dict(keys=fields.Str(), values=fields.Raw())
        ftd_code = fields.Str( 
            required=True, error_messages={"required": "CodingMappings *must* have a ftd_code "}
        )

        @post_load
        def build_coding_mapping(self, data, **kwargs):
            return CodingMapping(**data)

    def to_dict(self):
        """Inherits Terminonlogy.Coding. Adds mapping specific attributes."""
        obj = super().to_dict()

        # Marks the mapping valid if the attribute does not exist in the database
        if self.valid is not None:
            obj["valid"] = self.valid
        else:
            self.valid = True

        # Formatted version of a code for MD to display.
        formatted = locutus.format_ftd_code(self.ftd_code, FTDOntologyLookup.get_mapped_curie(self.system))
        self.ftd_code = formatted
        obj["ftd_code"] = self.ftd_code

        # Returns the mapping_relationship as "" if the attribute does not exist in database
        if self.mapping_relationship is not None:
            obj["mapping_relationship"] = self.mapping_relationship
        else:
            obj["mapping_relationship"] = ""

        # Returns the user_input for a mapping if requested
        if self.user_input is not None:
            obj["user_input"] = self.user_input

        return obj


class Coding(Simple, BasicCoding):
    def __init__(self, 
                    terminology_id, 
                    code, 
                    display="", 
                    system=None, 
                    description="", 
                    rank=0, 
                    valid=True, 
                    id=None, 
                    resource_type=None, 
                    editor=None, 
                    _id=None, 
                    mappings=[],
                    api_preferences=None):
        if not isinstance(terminology_id, str) or not terminology_id.strip():
            raise ValueError("Term ID is required for all Codings.")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Code is a required string and cannot be empty.")
        if not isinstance(system, str) or not system.strip():
            raise ValueError("System is a required string and cannot be empty.")


        if _id is None:
            prev = self.__class__.get(_id=_id, terminology_id=terminology_id, code=code, system=system, return_instance=False)
            if prev != []:
                _id = prev['_id']

                if id is None:
                    id = prev['id']
                if mappings == []:
                    mappings = prev['mappings']
                if api_preferences is None:
                    api_preferences = prev['api_preferences']

        Simple.__init__(self, id=id,
                         _id=_id, 
                         collection_type="Coding", 
                         resource_type="Coding")

        code = locutus.normalize_ftd_placeholders(code)
        
        BasicCoding.__init__(self, code=code, system=system, display=display, description=description)
        if editor is not None:
            self.save()

        self.terminology_id = terminology_id.strip() 
        self.rank = rank
        self.valid = valid

        self.mappings = mappings

        self.api_preferences = api_preferences

        """
        if api_preferences is None:
            self.api_preferences = OntoApiPreference(api_preferences)
        else:
            self.api_preferences = OntoApiPreference(api_preferences)
        """

    @classmethod 
    def get(cls, _id=None, terminology_id=None, code=None, system=None, valid_only=True, return_instance=True):
        if _id is not None:
            return Coding.find({"_id": ObjectId(_id)}, sorting="rank")[0]

        if (not isinstance(terminology_id, str) or not terminology_id.strip()) and (not isinstance(system, str) or not system.strip()):
            raise ValueError("Terminology ID or system is required to get a coding without an _id.")
        
        params = {}
        if isinstance(code, str) and code.strip():
            params["code"] = code 
        
        if isinstance(terminology_id, str) and terminology_id.strip():
            params["terminology_id"] = terminology_id.strip()
        
        if isinstance(system, str) and system.strip():
            params["system"] = system.strip()

        if valid_only:
            params['valid'] = True

        codings = Coding.find(params, sorting="rank", return_instance=return_instance)
        if len(codings) == 1:
            return codings[0]

        return codings

    class _Schema(Schema):
        code = fields.Str(
            required=True, error_messages={"required": "Codings *must* have a code "}
        )
        id = fields.Str()
        display = fields.Str()
        system = fields.URL()
        description = fields.Str()
        terminology_id = fields.Str()
        valid = fields.Bool()
        rank = fields.Integer()
        mappings = fields.List(fields.Nested(CodingMapping._Schema))
        # api_preferences = fields.Nested(OntoApiPreference._Schema)
        api_preferences = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))
        @post_load
        def build_coding(self, data, **kwargs):
            return Coding(**data)

    def get_api_preferences(self):
        return {
            "api_preference":  self.api_preferences
        }


    def add_api_preferences(self, api, preferences):
        if len(preferences) > 0:
            self.api_preferences[api] = preferences
            #self.api_preferences.set_preference(api, preferences)

    def remove_api_preferences(self):
        self.api_preferences = {}

    def to_dict(self, show_valid=False):
        obj = BasicCoding.to_dict(self)

        if show_valid and self.valid is not None:
            obj['valid'] = self.valid 

        return obj

    @classmethod
    def index_list(cls):
        "For codings, we must have either a terminology or system and the code"
        return [
            [("terminology_id", 1), ("code", 1), ('rank', 1), ("valid", 1)],
            [("terminology_id", 1), ('rank', 1), ("valid", 1)],
            [("system", 1), ("code", 1), ('rank', 1), ("valid", 1)],
            [("system", 1), ('rank', 1), ("valid", 1)]
        ]

    def delete(self, hard_delete=True):
        if not hard_delete:
            self.valid =False 
            self.save()
            t = self.to_dict()
        else:
            t = Simple.delete(self, hard_delete=hard_delete)
        return t

    def delete_mappings(self):
        codes = []
        for mapping in self.mappings:
            codes.append(mapping.to_dict())
            mapping.valid=False

        self.mappings = []
        self.save()

        return codes