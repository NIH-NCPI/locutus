from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers
from locutus.model.variable import Variable, InvalidVariableDefinition

from locutus import fix_varname

import pdb

# Eventually, these should either live in the dataset or in a top level table
# so that the user can edit them. But, for now, we'll just maintain a static
# set of variable representations for data type.
_data_types = {"int": "integer", "number": "quantity", "numeric": "quantity"}


def get_data_type(data_type):
    global _data_types

    dtype = data_type.lower()
    if dtype in _data_types:
        print(f"Swapping {dtype} out for {_data_types[dtype]}")
        dtype = _data_types[dtype]

    valid_types = Variable._factory_workers.keys()
    if dtype not in valid_types:
        valid_types = ", ".join(valid_types)
        msg = (
            f"The data_type, {data_type}, isn't one of the valid types: {valid_types}."
        )
        print(msg)
        raise KeyError(msg)

    return dtype


class TableLoader(Resource):
    def post(self):
        tblData = request.get_json()

        tbl = {
            "name": tblData["name"],
            "url": tblData["url"],
            "filename": tblData["filename"],
            "variables": [],
        }

        if "description" in tblData:
            tbl["description"] = tblData["description"]

        if "resource_type" in tblData:
            del tblData["resource_type"]

        # Iterate over the csvContent to build up the list of variables and
        # optionally, the enumerations if that is appropriate.
        try:
            for varData in tblData["csvContents"]:
                if "data_type" not in varData:
                    print(varData)
                    print(varData["variable_name"])
                    print(sorted(varData.keys()))

                var = {
                    "name": varData["variable_name"],
                    "data_type": get_data_type(varData["data_type"]),
                }
                if "description" in varData:
                    var["description"] = varData["description"]
                if "min" in varData and varData["min"].strip() != "":
                    var["min"] = varData["min"]
                if "max" in varData and varData["max"].strip() != "":
                    var["max"] = varData["max"]
                if "units" in varData and varData["units"].strip() != "":
                    var["units"] = varData["units"]

                url = tblData["url"]

                varname = fix_varname(varData["variable_name"])

                if "enumerations" in varData and varData["enumerations"].strip() != "":
                    var["data_type"] = "ENUMERATION"
                    terminology = {
                        "name": varname,
                        "url": f"{url}/{varname}",
                        "codes": [],
                    }

                    for code in [
                        x.strip() for x in varData["enumerations"].strip().split(";")
                    ]:
                        description = None

                        if "=" in code:
                            code, description = code.split("=")
                        term = {"code": code, "system": url}
                        if description is not None:
                            term["display"] = description

                        terminology["codes"].append(term)

                    t = Term(**terminology)
                    t.save()
                    var["enumerations"] = {"reference": f"Terminology/{t.id}"}

                tbl["variables"].append(var)

            try:
                t = mTable(**tbl)
            except InvalidVariableDefinition as e:
                return (
                    {"message_to_user": e.message(), "data": e.variable},
                    400,
                    default_headers,
                )
            t.save()
            return t.dump(), 201, default_headers
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
