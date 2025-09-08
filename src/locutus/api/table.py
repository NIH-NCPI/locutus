from flask_restful import Resource
from flask import request
from locutus.model.table import Table as mTable
from locutus.model.provenance import Provenance 
from locutus.model.terminology import Terminology
from locutus.api import default_headers, get_editor
from locutus.api.datadictionary import DataDictionaries
from locutus.model.exceptions import *
from copy import deepcopy

from bson import json_util 
import json

class TableRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        varname_updates = body.get("variable")
        description_updates = body.get("description")

        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        table = mTable.get(id)
        # print(f"Variable name updates requested: {varname_updates}")
        # print(f"Description updates requested: {description_updates}")

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
                editor=editor,
            ):
                return (
                    f"{original_code} was not found in the terminology.",
                    404,
                    default_headers,
                )

        return json.loads(json_util.dumps(table.dump())), 201, default_headers


class TableEdit(Resource):
    def put(self, id, code):
        """Add a new variable to an existing table"""

        table = mTable.get(id)
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            vardef = deepcopy(body)
            vardef["name"] = code

            table.add_variable(vardef, editor=editor)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        table.save()
        return json.loads(json_util.dumps(table.dump())), 201, default_headers

    def delete(self, id, code):
        """Delete a Table Variable"""

        table = mTable.get(id)
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            table.remove_variable(code, editor=editor)
            table.save()
        except KeyError as e:
            return str(e), 404, default_headers
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return json.loads(json_util.dumps(table.dump())), 200, default_headers


class Tables(Resource):
    def get(self):
        """
        TODO: Paginate these ResourceType/get calls
        Technically, this will probably not get so big as to be a problem
        but it's technically not wise to pull these into a single response.
        We should plan on paginating this at some point."""

        return (
            json.loads(json_util.dumps(mTable.get(return_instance = False))),
            200,
            default_headers,
        )

    def post(self):
        tbl = request.get_json()
        try:
            editor = get_editor(body=tbl, editor=None)
            if editor is None:
                raise LackingUserID(editor)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return json.loads(json_util.dumps(t.dump())), 201, default_headers


class Table(Resource):

    def get(self, id):
        return json.loads(json_util.dumps(mTable.get(id, return_instance=False)))

    def put(self, id):
        tbl = request.get_json()
        try:
            editor = get_editor(body=tbl, editor=None)
            if editor is None:
                raise LackingUserID(editor)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        if "id" not in tbl:
            tbl["id"] = id

        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return json.loads(json_util.dumps(t.dump())), 200, default_headers

    def delete(self, id):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # This is a bit "out of band"
            t = mTable.get(id)
            t.terminology.dereference().add_provenance(
                change_type=Provenance.ChangeType.RemoveTable,
                target="self",
                old_value=f"Table Name: {t.name}",
                editor=editor,
            )

            # Delete any references to the table from any data-dictionaries:
            DataDictionaries().delete_table_references(id)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        table_content = t.dump()
        t.delete()

        return json.loads(json_util.dumps(table_content)), 200, default_headers


class HarmonyCSV(Resource):
    def get(self, id):
        t = mTable.get(id)

        try:
            harmony = t.as_harmony()
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return json.loads(json_util.dumps(harmony)), 200, default_headers
