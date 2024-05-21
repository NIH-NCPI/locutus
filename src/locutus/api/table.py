from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.api import default_headers
from locutus.api.datadictionary import DataDictionaries

import pdb


class TableRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        varname_updates = body.get("variable")
        description_updates = body.get("description")

        table = mTable.get(id)
        print(f"Variable name updates requested: {varname_updates}")
        print(f"Description updates requested: {description_updates}")

        # We MUST have at least a code or a display component to be a valid
        # PATCH
        if varname_updates is None and description_updates is None:
            return (
                "Must provide variable names and/or descriptions to be PATCHed.",
                400,
                default_headers,
            )

        if varname_updates is None:
            varname_updates = {}
        if description_updates is None:
            description_updates = {}

        var_list = sorted(
            list(set(list(varname_updates.keys()) + list(description_updates.keys())))
        )

        for var in var_list:
            original_code = var
            new_code = varname_updates.get(original_code)

            if new_code is None:
                new_code = original_code

            if not table.rename_var(
                original_varname=original_code,
                new_varname=new_code,
                new_description=description_updates.get(original_code),
            ):
                return (
                    f"{original_code} was not found in the terminology.",
                    404,
                    default_headers,
                )

        return table.dump(), 201, default_headers


class TableEdit(Resource):
    def put(self, id, code):
        """Add a new variable to an existing table"""

        table = mTable.get(id)
        body = request.get_json()

        table.add_variable(
            {
                "name": code,
                "description": body["description"],
                "data_type": body["data_type"],
            }
        )
        table.save()
        return table.dump(), 201, default_headers

    def delete(self, id, code):
        """Add a new variable to an existing table"""

        table = mTable.get(id)

        try:
            table.remove_variable(code)
            table.save()
        except KeyError as e:
            return str(e), 404, default_headers

        return table.dump(), 200, default_headers


class Tables(Resource):
    def get(self):
        """
        TODO: Paginate these ResourceType/get calls
        Technically, this will probably not get so big as to be a problem
        but it's technically not wise to pull these into a single response.
        We should plan on paginating this at some point."""
        return (
            [x.to_dict() for x in persistence().collection("Table").stream()],
            200,
            default_headers,
        )

    def post(self):
        tbl = request.get_json()

        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return t.dump(), 201, default_headers


class Table(Resource):
    def get(self, id):
        # pdb.set_trace()
        return mTable.get(id, return_instance=False)

    def put(self, id):
        tbl = request.get_json()
        if "id" not in tbl:
            tbl["id"] = id

        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return t.dump(), 200, default_headers

    def delete(self, id):
        dref = persistence().collection("Table").document(id)

        # Delete any references to the table from any data-dictionaries:
        DataDictionaries().delete_table_references(id)

        t = dref.get().to_dict()
        print(f"{id} : {t}")
        time_of_delete = dref.delete()
        # if t is not None:
        #    persistence().save()

        return t, 200, default_headers


class HarmonyCSV(Resource):
    def get(self, id):
        t = mTable.get(id)

        try:
            harmony = t.as_harmony()
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return harmony, 200, default_headers
