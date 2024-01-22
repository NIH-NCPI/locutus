from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.datadictionary import DataDictionary as DD
from locutus.api import default_headers

import pdb


class DataDictionaries(Resource):
    def get(self):
        return (
            [x.to_dict() for x in persistence().collection("DataDictionary").stream()],
            200,
            default_headers,
        )

    def post(self):
        dd = request.get_json()
        if "resource_type" in dd:
            del dd["resource_type"]

        d = DD(**dd)
        d.save()
        return d.dump(), 201, default_headers


class DataDictionary(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("DataDictionary").document(id).get()
        return t.to_dict()

    def put(self, id):
        dd = request.get_json()
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
        time_of_delete = dref.delete()

        # if t is not None:
        #    persistence().save()

        return t, 200, default_headers
