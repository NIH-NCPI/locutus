from flask_restful import Resource, reqparse
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term

import pdb


class Terminologies(Resource):
    def get(self):
        return [x.dump() for x in persistence().collection("Terminology").documents()]

    def post(self):
        term = request.get_json()
        del term["resource_type"]

        t = Term(**term)
        t.save()
        return t.dump()


class Terminology(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("Terminology").document(id)
        return t

    def put(self, id):
        term = request.get_json()
        print(term)
        if "id" not in term:
            term["id"] = id

        del term["resource_type"]
        t = Term(**term)
        t.save()

    def delete(self, id):
        pass
