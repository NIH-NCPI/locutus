from . import Serializable
from marshmallow import Schema, fields, post_load

from locutus.model.reference import Reference


"""
A data-dictionary is a collection of tables that, together, describe the 
complete data format for a study's datasets. 

Id:
This should be generated by the system, but can be provided by the user. 

Name (required):
A Human friendly name associated with the data-dictionary. 

Description:
An optional block of text that is used to provide context for understanding the
data-dictionary's purpose.

Tables:
references to the various tables that comprise the data-dictionary


"""


class DataDictionary(Serializable):
    _id_prefix = "dd"

    def __init__(self, id=None, name=None, description=None, tables=None):
        super().__init__(
            id, collection_type="DataDictionary", resource_type="DataDictionary"
        )
        self.id = id
        self.name = name
        self.description = description

        self.tables = []
        super().identify()

        if tables is not None:
            for t in tables:
                self.tables.append(Reference(reference=t["reference"]))

    def remove_table(self, table_id):
        matching_references = []

        treference = f"Table/{table_id}"

        idx = 0
        for tblref in self.tables:
            if tblref.reference == treference:
                matching_references.append(idx)
            idx += 1

        if len(matching_references) > 0:
            for ref in matching_references:
                del self.tables[ref]

        return len(matching_references)

    def keys(self):
        return [self.name]

    class _Schema(Schema):
        id = fields.Str()
        name = fields.Str(required=True)
        description = fields.Str()

        tables = fields.List(fields.Nested(Reference._Schema))
        resource_type = fields.Str()

        @post_load
        def build_terminology(self, data, **kwargs):
            return DataDictionary(**data)
