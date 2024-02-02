from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers

from locutus import fix_varname

import pdb


class TableLoader(Resource):
    def post(self):
        tblData = request.get_json()

        tbl = {
            "name": tblData["name"],
            "description": tblData["description"],
            "url": tblData["url"],
            "filename": tblData["filename"],
            "variables": [],
        }

        if "resource_type" in tblData:
            del tblData["resource_type"]

        # Iterate over the csvContent to build up the list of variables and
        # optionally, the enumerations if that is appropriate.
        for varData in tblData["csvContents"]:
            if "data_type" not in varData:
                print(varData)
                print(varData["variable_name"])
                print(sorted(varData.keys()))

            var = {"name": varData["variable_name"], "data_type": varData["data_type"]}
            if "description" in varData:
                var["description"] = varData["data_type"]
            if "min" in varData:
                var["min"] = varData["min"]
            if "max" in varData:
                var["max"] = varData["max"]
            if "units" in varData:
                var["units"] = varData["units"]

            url = tblData["url"]

            varname = fix_varname(varData["variable_name"])

            if "enumerations" in varData and varData["enumerations"].strip() != "":
                var["data_type"] = "ENUMERATION"
                terminology = {"name": varname, "url": f"{url}/{varname}", "codes": []}

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

        t = mTable(**tbl)
        t.save()
        return t.dump(), 201, default_headers
