from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.api import default_headers


class Tables(Resource):
    def get(self):
        return (
            [x.dump() for x in persistence().collection("Table").documents()],
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
        t = persistence().collection("Table").document(id)
        return t

    def put(self, id):
        tbl = request.get_json()
        if "id" not in tbl:
            tbl["id"] = id

        del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return t.dump(), 200, default_headers

    def delete(self, id):
        t = persistence().collection("Table").delete(id)

        if t is not None:
            persistence().save()

        return t, 200, default_headers
