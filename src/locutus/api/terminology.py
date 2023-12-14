from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers

import pdb


class Terminologies(Resource):
    def get(self):
        return (
            [x.dump() for x in persistence().collection("Terminology").documents()],
            200,
            default_headers,
        )

    @cross_origin(allow_headers=["Content-Type"])
    def post(self):
        term = request.get_json()
        if "resource_type" in term:
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
        if "id" not in term:
            term["id"] = id

        if "resource_type" in term:
            del term["resource_type"]
        t = Term(**term)
        t.save()
        return t.dump(), 200, default_headers

    # @cross_origin()
    def delete(self, id):
        t = persistence().collection("Terminology").delete(id)

        if t is not None:
            persistence().save()

        return t, 200, default_headers
