from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.datadictionary import DataDictionary as DD
from locutus.api.study import Studies
from locutus.api import default_headers

from flask_cors import cross_origin


class DataDictionaries(Resource):
    def get(self):
        return (
            [doc.to_dict() for doc in persistence().collection("DataDictionary").stream()],
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
        return d.dump(), 201, default_headers

    def delete_table_references(self, table_id):
        # Does this need to be batched. I'm assuming we'll end up using a
        # different database before we get enough of these to matter        affected_dds = 0
        for dd in persistence().collection("DataDictionary").stream():
            dd = dd.to_dict()

            if "resource_type" in dd:
                del dd["resource_type"]
            if "_id" in dd:
                del dd["_id"]
            d = DD(**dd)

            matched_references = d.remove_table(table_id)

            if matched_references > 0:
                d.save()

                affected_dds += 1

        return affected_dds


class DataDictionary(Resource):

    def get(self, id):
        # pdb.set_trace()
        dref = persistence().collection("DataDictionary").document(id).get()
        if dref.exists:
            dref_dict = dref.to_dict()
            dref_dict.pop("_id", None)
            return dref_dict, 200, default_headers
        return {"message": "Data dictionary not found"}, 404, default_headers

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id):
        dd = request.get_json()
        if "_id" in dd:
            del dd["_id"]
        if "id" not in dd:
            dd["id"] = id

        if "resource_type" in dd:
            del dd["resource_type"]

        d = DD(**dd)
        d.save()
        return d.dump(), 201, default_headers

    def delete(self, id):
        dref = persistence().collection("DataDictionary").document(id)
        t = dref.get().to_dict()
        print(f"{id} : {t}")

        # Delete any references to the data dictionary from any studies:
        Studies().delete_dd_references(id)

        time_of_delete = dref.delete()

        # if t is not None:
        #    persistence().save()

        return t, 200, default_headers


class DataDictionaryTable(Resource):
    @cross_origin()
    def delete(self, id, table_id):
        ddref = persistence().collection("DataDictionary").document(id).get().to_dict()

        if "resource_type" in ddref:
            del ddref["resource_type"]
        if "_id" in ddref:
            del ddref["_id"]
        # We'll realize the data-dictionary and delete the id from there
        d = DD(**ddref)

        refs_removed = d.remove_table(table_id)
        if refs_removed > 0:
            d.save()

        dd = d.dump()

        return dd, 200, default_headers
