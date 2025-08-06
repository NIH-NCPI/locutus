
from . import Simple
from marshmallow import Schema, fields, post_load
from pymongo import ASCENDING


from locutus import (
    normalize_ftd_placeholders,
    persistence
)

class Coding(Simple):
    def __init__(self, terminology_id, code, display="", system=None, description="", rank=0, valid=None, id=None, resource_type=None, editor=None, _id=None ):
        if not isinstance(terminology_id, str) or not terminology_id.strip():
            raise ValueError("Term ID is required for all Codings.")
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Code is a required string and cannot be empty.")
        if not isinstance(system, str) or not system.strip():
            raise ValueError("System is a required string and cannot be empty.")

        super().__init__(id=id,
                         _id=_id, 
                         collection_type="Coding", 
                         resource_type="Coding")
        if editor is not None:
            self.save()
            self.add_provenance()

        code = normalize_ftd_placeholders(code)
        self.terminology_id = terminology_id.strip() 
        self.code = code.strip()
        self.display = display.strip() if isinstance(display, str) else display
        self.system = system.strip()
        self.description = description.strip() if isinstance(description, str) else description
        self.rank = rank
        self.valid = valid

    @classmethod 
    def get(cls, _id=None, terminology_id=None, code=None, system=None, return_instance=True):

        if _id is not None:
            return Coding.find({"_id": _id}).sort([("rank", ASCENDING)])[0]

        if (not isinstance(terminology_id, str) or not terminology_id.strip()) and (not isinstance(system, str) or not system.strip()):
            raise ValueError("Terminology ID or system is required to get a coding without an _id.")
        
        params = {}
        if isinstance(code, str) and code.strip():
            params["code"] = code 
        
        if isinstance(terminology_id, str) and terminology_id.strip():
            params["terminology_id"] = terminology_id.strip()
        
        if isinstance(system, str) and system.strip():
            params["system"] = system.strip()


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

        @post_load
        def build_coding(self, data, **kwargs):
            return Coding(**data)

    def to_dict(self):
        obj = {"code": self.code, "display": self.display}

        if self.description != "":
            obj["description"] = self.description

        if self.system is not None:
            obj["system"] = self.system

        return obj

    def delete(self, hard_delete=True):
        if not hard_delete:
            self.valid =False 
            self.save()
            t = self.to_dict()
        else:
            dref = persistence().collection("Coding").document(self._id)
            t = dref.get().to_dict()

            time_of_delete = dref.delete()
        return t