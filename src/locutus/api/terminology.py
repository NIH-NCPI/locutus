from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers

import pdb


class Terminologies(Resource):
    def get(self):
        return (
            [x.dump() for x in persistence().collection("Terminology").documents()],
            200,
            default_headers,
        )

    def post(self):
        term = request.get_json()
        del term["resource_type"]

        t = Term(**term)
        t.save()
        return t.dump(), 201, default_headers


class Terminology(Resource):
    def get(self, id):
        t = persistence().collection("Terminology").document(id)
        return t, 200, default_headers

    def put(self, id):
        term = request.get_json()
        print(term)
        if "id" not in term:
            term["id"] = id

        del term["resource_type"]
        t = Term(**term)
        t.save()
        return t.dump(), 200, default_headers

    def delete(self, id):
        pass
