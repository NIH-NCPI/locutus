from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers, get_editor
from locutus.model.variable import Variable, InvalidVariableDefinition

import rich

from locutus import clean_varname

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

        # pdb.set_trace()

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

        t = mTable(**tbl)
        t.save()
        editor = get_editor(body=tblData, editor=None)

        # Iterate over the csvContent to build up the list of variables and
        # optionally, the enumerations if that is appropriate.
        return TableLoader.load_table(id=t.id, filename=t.filename, csvContents=tblData["csvContents"], editor=editor)
    
    @classmethod
    def load_table(cls, id, filename, csvContents, editor):
        tbl = mTable.get(id)

        if len(tbl.variables) > 0:
            return {"message_to_user": "The table already has variables."}, 400, default_headers
        
        tbl.filename = filename
        tbl.variables = []
        
        if len(csvContents) < 1:
            change_type = Term.ChangeType.CreateTable
        else:
            change_type = Term.ChangeType.AddVariables

        try:
            for varData in csvContents:
                if "data_type" not in varData:
                    print(
                        f"The property, 'data_type', is missing from CSV row. {varData['variable_name']}"
                    )

                varname = varData["variable_name"]
                code = clean_varname(varname)
                var = {
                    "code": code,
                    "name": varname,
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

                url = tbl.url

                if "enumerations" in varData and varData["enumerations"].strip() != "":
                    var["data_type"] = "ENUMERATION"
                    terminology = {
                        "name": varname,
                        "url": f"{url}/{code}",
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

                    rich.print(terminology)
                    t = Term(**terminology)
                    t.save()
                    var["enumerations"] = {"reference": f"Terminology/{t.id}"}
                # maybe do try except here to catch errors
                try:
                    tbl.add_variable(var)
                except InvalidVariableDefinition as e:
                    return (
                    {"message_to_user": e.message(), "data": e.variable},
                    400,
                    default_headers,
                )
            tbl.save()
            tbl.terminology.dereference().add_provenance(
                change_type=change_type,
                target="self",
                editor=editor,
            )
            return tbl.dump(), 201, default_headers
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
    
class TableLoader2(Resource):
    def put(self, id):
        tblData = request.get_json()

        # pdb.set_trace()
        tbl = mTable.get(id)
        editor = get_editor(body=tblData, editor=None)

      
        # check if csvContents exist. Otherwise, return error
        if not tblData.get("csvContents") or (len(tblData["csvContents"]) < 1):
            return {"message_to_user": "No variables provided."}, 400, default_headers
        else: 
            return TableLoader.load_table(id, filename=tblData.get("filename", tbl.filename), csvContents=tblData.get("csvContents"), editor=editor)

    