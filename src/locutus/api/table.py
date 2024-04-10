from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.api import default_headers
from locutus.api.datadictionary import DataDictionaries

import pdb


class Tables(Resource):
    def get(self):
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
        t = persistence().collection("Table").document(id).get()

        return t.to_dict()

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
        tbl = persistence().collection("Table").document(id).get().to_dict()

        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        try:
            harmony = t.as_harmony()
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return harmony, 200, default_headers
