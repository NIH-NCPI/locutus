from . import Serializable
from marshmallow import Schema, fields, post_load

from locutus.model.variable import Variable

import pdb

"""
A Table represents a collection of dataset "variables", typically organized
as a list, such as one might find inside a CSV file. 

Tables will exist in their own collection and have an id which can be used to
reference them from within a data-dictionary. 

Id:
This should be generated by the system, but can be provided by the user. 

Name (required):
A Human friendly name associated with the table. 

URL (required):
The table's "system" identifier. 

filename:
This is a bit of a relic that is used to refer back to the initial source from
which the table was defined. 

Description:
An optional block of text that is used to provide context for understanding the
table's purpose.
"""


class Table(Serializable):
    _id_prefix = "tb"

    def __init__(
        self,
        id=None,
        name=None,
        url=None,
        description=None,
        filename=None,
        variables=[],
    ):
        super().__init__(id=id, collection_type="Table", resource_type="Table")
        self.id = id
        self.name = name
        self.description = description
        self.filename = filename
        self.url = url
        self.variables = []

        for var in variables:
            if type(var) is dict:
                v = Variable.deserialize(var)
                # pdb.set_trace()
                self.variables.append(v)
            else:
                self.variables.append(var)

        super().identify()

    def build_harmony_row(self, local_coding, mapped_coding):

        return {
            "local code": local_coding.code,
            "text": local_coding.display,
            "table_name": self.name,
            "parent_varname": "",  # I'm not sure if we can get this ATM
            "local code system": local_coding.system,
            "code": mapped_coding.code,
            "display": mapped_coding.display,
            "code system": mapped_coding.system,
            "comment": "",
        }

    def as_harmony(self):
        # Iterate over each table
        harmony_mappings = []
        for var in self.variables:
            if var.data_type == Variable.DataType.ENUMERATION:
                term = var.get_terminology()

                # Capture a dictionary with code=>coding
                codings = term.build_code_dict()

                mappings = var.get_mappings()
                for code in mappings:

                    if code not in codings:
                        allowed_codes = "'" + "','".join(codings.keys()) + "'"
                        raise KeyError(
                            f"The code, {code}, doesn't match any of the available codes: {allowed_codes}"
                        )
                    coding = codings[code]

                    mapped_codings = mappings[code]

                    for mc in mapped_codings:
                        harmony_row = self.build_harmony_row(coding, mc)
                        if harmony_row is not None:
                            harmony_mappings.append(harmony_row)
        return harmony_mappings

    def keys(self):
        return [self.url, self.name]

    class _Schema(Schema):
        id = fields.Str()
        name = fields.Str(required=True)
        url = fields.URL(required=True)
        filename = fields.Str()
        description = fields.Str()
        variables = fields.List(fields.Nested(Variable._Schema))
        resource_type = fields.Str()

        @post_load
        def build_terminology(self, data, **kwargs):
            return Table(**data)

    def dump(self):
        content = self.__class__._get_schema().dump(self)
        content["variables"] = [v.dump() for v in self.variables]
        # pdb.set_trace()

        return content
