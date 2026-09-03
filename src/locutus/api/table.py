import json
from copy import deepcopy

from bson import json_util
from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers, get_editor
from locutus.api.datadictionary import DataDictionaries
from locutus.auth import (
    filter_readable,
    new_resource_access_fields,
    require_auth,
    require_read_access,
    require_write_access,
    require_write_access_or_create,
)
from locutus.model.exceptions import APIError, LackingUserID
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat
from locutus.model.provenance import Provenance
from locutus.model.table import Table as mTable


class TableRenameCode(Resource):
    @require_write_access("Table", "id")
    def patch(self, id: str):
        body = request.get_json()
        varname_updates = body.get("variable")
        description_updates = body.get("description")

        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        # require_write_access already confirmed this id exists (404s
        # before this handler runs otherwise).
        table = mTable.get(id)
        assert table is not None
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
            set(list(varname_updates.keys()) + list(description_updates.keys()))
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
    @require_write_access("Table", "id")
    def put(self, id: str, code: str):
        """Add a new variable to an existing table"""

        # require_write_access already confirmed this id exists.
        table = mTable.get(id)
        assert table is not None
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

    @require_write_access("Table", "id")
    def delete(self, id: str, code: str):
        """Delete a Table Variable"""

        # require_write_access already confirmed this id exists.
        table = mTable.get(id)
        assert table is not None
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
    @require_auth
    def get(self):
        """
        TODO: Paginate these ResourceType/get calls
        Technically, this will probably not get so big as to be a problem
        but it's technically not wise to pull these into a single response.
        We should plan on paginating this at some point."""

        tables = filter_readable(mTable.get(return_instance=False), g.current_user)
        return (
            json.loads(json_util.dumps(tables)),
            200,
            default_headers,
        )

    @require_auth
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

        # owner_id/access are always derived from the authenticated caller,
        # never trusted from the request body (M4) -- overwrites anything
        # a client sent for these keys.
        tbl.update(new_resource_access_fields(g.current_user))

        t = mTable(**tbl)
        t.save()
        return json.loads(json_util.dumps(t.dump())), 201, default_headers


class Table(Resource):
    @require_read_access("Table", "id")
    def get(self, id: str):
        return json.loads(json_util.dumps(mTable.get(id, return_instance=False)))

    @require_write_access_or_create("Table", "id")
    def put(self, id: str):
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

        # PUT fully replaces the object from the request body, so
        # owner_id/access must be resolved explicitly rather than trusted
        # from the client either way: preserve the existing resource's
        # values on an update, or stamp fresh ones from the authenticated
        # caller if this PUT is actually creating a new table at this id
        # (require_write_access_or_create already confirmed either is
        # allowed before this handler runs).
        existing = mTable.get(id, return_instance=False)
        if existing is not None:
            tbl["owner_id"] = existing.get("owner_id")
            tbl["access"] = existing.get("access")
        else:
            tbl.update(new_resource_access_fields(g.current_user))

        t = mTable(**tbl)
        t.save()
        return json.loads(json_util.dumps(t.dump())), 200, default_headers

    @require_write_access("Table", "id")
    def delete(self, id: str):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # This is a bit "out of band"
            # require_write_access already confirmed this id exists.
            t = mTable.get(id)
            assert t is not None
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


class HarmonyTableCSV(Resource):
    def get(self, id: str):
        data_format = request.args.get("format", "Whistle")
        file_format = request.args.get("file-format", "JSON")

        try:
            if data_format:
                data_format = HarmonyFormat(data_format)
            if file_format:
                file_format = HarmonyOutputFormat(file_format)
        except ValueError as e:
            return {"message_to_user": str(e)}, 400, default_headers

        t = mTable.get(id)

        try:
            print(f"Harmony Format: {data_format}")
            print(f"Output Format: {file_format}")

            harmony = t.as_harmony(
                harmony_format=data_format, harmony_output_format=file_format
            )

        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return json.loads(json_util.dumps(harmony)), 200, default_headers
