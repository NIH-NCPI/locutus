from flask_restful import Resource
from flask import request
from locutus.model.datadictionary import DataDictionary as DD
from locutus.api.study import Studies
from locutus.api import default_headers

from flask_cors import cross_origin

from bson import json_util 
import json

class DataDictionaries(Resource):
    def get(self):
        return (
            json.loads(json_util.dumps(DD.get(return_instance=False))),
            200,
            default_headers,
        )

    def save_dd(self, dd):
        if "resource_type" in dd:
            del dd["resource_type"]

        d = DD(**dd)
        d.save()
        return d

    @cross_origin(allow_headers=["Content-Type"])
    def post(self):
        dd = request.get_json()
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

    def get(self, id):
        t = DD.get(id, return_instance=False)
        if t is not None:
            return json.loads(json_util.dumps(t)), 200, default_headers
        else:
            return f"No DataDictionary with id, {id}, was found", 404, default_headers

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id):
        dd = request.get_json()
        if "id" not in dd:
            dd["id"] = id

        if "resource_type" in dd:
            del dd["resource_type"]

        d = DD(**dd)
        d.save()
        return json.loads(json_util.dumps(d.dump())), 201, default_headers

    def delete(self, id):
        dd = DD.get(id)
        d = dd.dump()

        # Delete any references to the data dictionary from any studies:
        Studies().delete_dd_references(id)
        dd.delete()

        return json.loads(json_util.dumps(d)), 200, default_headers


class DataDictionaryTable(Resource):
    @cross_origin()
    def delete(self, id, table_id):
        d = DD.get(id)

        refs_removed = d.remove_table(table_id)
        if refs_removed > 0:
            d.save()

        dd = d.dump()

        return json.loads(json_util.dumps(dd)), 200, default_headers
