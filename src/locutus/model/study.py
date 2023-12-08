from . import Serializable
from marshmallow import Schema, fields, post_load

from locutus.model.datadictionary import DataDictionary
from locutus.model.reference import Reference

"""
A Study represents a research study which will likely contain one or more
datasets which conform to a single data-dictionary. 

The study objects will live within their own collection and will, therefore, 
have their own id. 

Id:
This should be generated by the system, but can be provided by the user. 

Name (required):
A Human friendly name associated with the study. 

Title (required):
The study's formal title

URL (required):
The study's "system" identifier. 

Description:
An optional block of text that is used to provide context for understanding the
study's purpose.

Identifier-Prefix:
This is used when generating FHIR systems for identifiers. 

Data-Dictionary:
This will be references to the data-dictionaries associated with the study




"""


class Study(Serializable):
    _id_prefix = "st"

    def __init__(
        self,
        id=None,
        name=None,
        description=None,
        identifier_prefix="",
        title=None,
        url="",
        datadictionary=None,
    ):
        super().__init__(id=id, collection_type="Study", resource_type="Study")
        self.name = name
        self.description = description
        self.identifier_prefix = identifier_prefix
        self.title = title
        self.url = url
        self.datadictionary = Reference(reference=datadictionary)

        super().identify()

    def keys(self):
        return [self.title, self.url, self.name]

    class _Schema(Schema):
        id = fields.Str()
        name = fields.Str(required=True)
        description = fields.Str()
        identifier_prefix = fields.URL()
        title = fields.Str(required=True)
        url = fields.URL()
        resource_type = fields.Str()

        # For now, we'll just cache the reference ID
        datadictionary = fields.Nested(Reference._Schema)

        @post_load
        def build_terminology(self, data, **kwargs):
            return Study(**data)
