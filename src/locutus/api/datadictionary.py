import json

from bson import json_util
from flask import g, request
from flask_cors import cross_origin
from flask_restful import Resource

from locutus.api import default_headers
from locutus.api.study import Studies
from locutus.auth import (
    filter_readable,
    new_resource_access_fields,
    require_auth,
    require_read_access,
    require_write_access,
    require_write_access_or_create,
)
from locutus.model.datadictionary import DataDictionary as DD
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat


class DataDictionaries(Resource):
    @require_auth
    def get(self):
        dds = filter_readable(DD.get(return_instance=False), g.current_user)
        return (json.loads(json_util.dumps(dds)), 200, default_headers)

    def save_dd(self, dd):
        if "resource_type" in dd:
            del dd["resource_type"]

        d = DD(**dd)
        d.save()
        return d

    @cross_origin(allow_headers=["Content-Type"])
    @require_auth
    def post(self):
        dd = request.get_json()
        # owner_id/access are always derived from the authenticated caller,
        # never trusted from the request body (M4).
        dd.update(new_resource_access_fields(g.current_user))
        d = self.save_dd(dd)
        return json.loads(json_util.dumps(d.dump())), 201, default_headers

    def delete_table_references(self, table_id):
        # Does this need to be batched. I'm assuming we'll end up using a
        # different database before we get enough of these to matter

        affected_dds = 0
        for d in DD.get(return_instance=True):
            matched_references = d.remove_table(table_id)

            if matched_references > 0:
                d.save()

                affected_dds += 1

        return affected_dds


class DataDictionary(Resource):
    @require_read_access("DataDictionary", "id")
    def get(self, id: str):
        # require_read_access already confirmed this id exists.
        t = DD.get(id, return_instance=False)
        assert t is not None
        return json.loads(json_util.dumps(t)), 200, default_headers

    @cross_origin(allow_headers=["Content-Type"])
    @require_write_access_or_create("DataDictionary", "id")
    def put(self, id: str):
        dd = request.get_json()
        if "id" not in dd:
            dd["id"] = id

        if "resource_type" in dd:
            del dd["resource_type"]

        # PUT fully replaces the object from the request body, so
        # owner_id/access must be resolved explicitly rather than trusted
        # from the client either way: preserve the existing resource's
        # values on an update, or stamp fresh ones from the authenticated
        # caller if this PUT is actually creating a new data dictionary at
        # this id (require_write_access_or_create already confirmed either
        # is allowed before this handler runs).
        existing = DD.get(id, return_instance=False)
        if existing is not None:
            dd["owner_id"] = existing.get("owner_id")
            dd["access"] = existing.get("access")
        else:
            dd.update(new_resource_access_fields(g.current_user))

        d = DD(**dd)
        d.save()
        return json.loads(json_util.dumps(d.dump())), 201, default_headers

    @require_write_access("DataDictionary", "id")
    def delete(self, id: str):
        # require_write_access already confirmed this id exists.
        dd = DD.get(id)
        assert dd is not None
        d = dd.dump()

        # Delete any references to the data dictionary from any studies:
        Studies().delete_dd_references(id)
        dd.delete()

        return json.loads(json_util.dumps(d)), 200, default_headers


class DataDictionaryTable(Resource):
    @cross_origin()
    @require_write_access("DataDictionary", "id")
    def delete(self, id: str, table_id: str):
        # require_write_access already confirmed this id exists.
        d = DD.get(id)
        assert d is not None

        refs_removed = d.remove_table(table_id)
        if refs_removed > 0:
            d.save()

        dd = d.dump()

        return json.loads(json_util.dumps(dd)), 200, default_headers


class DataDictionaryHarmony(Resource):
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

        t = DD.get(id)

        try:
            harmony = t.as_harmony(
                harmony_format=data_format, harmony_output_format=file_format
            )
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return json.loads(json_util.dumps(harmony)), 200, default_headers
