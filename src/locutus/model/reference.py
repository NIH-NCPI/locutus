from . import Serializable
from marshmallow import Schema, fields, post_load

"""
The reference just represents a placeholder for an entity from another table
"""


class Reference(Serializable):
    def __init__(self, reference=None):
        self.reference = reference

    class _Schema(Schema):
        reference = fields.Str()
        resource_type = fields.Str()

        @post_load
        def build_reference(self, data, **kwargs):
            return Reference(**data)
