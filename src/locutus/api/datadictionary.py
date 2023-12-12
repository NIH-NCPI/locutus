from flask_restful import Resource
from locutus import persistence
from locutus.model.datadictionary import DataDictionary as DD
from locutus.api import default_headers


class DataDictionaries(Resource):
    def get(self):
        return (
            [x.dump() for x in persistence().collection("DataDictionary").documents()],
            200,
            default_headers,
        )

    def post(self):
        dd = request.get_json()
        del dd["resource_type"]

        d = dd(**dd)
        d.save()
        return d.dump(), 201, default_headers


class DataDictionary(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("DataDictionary").document(id)
        return t

    def put(self, study):
        dd = request.get_json()
        if "id" not in dd:
            dd["id"] = id

        del dd["resource_type"]

        d = dd(**dd)
        d.save()
        return d.dump(), 201, default_headers

    def delete(self, id):
        t = persistence().collection("DataDictionary").delete(id)

        if t is not None:
            persistence().save()

        return t, 200, default_headers
