from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term, Coding
from locutus.api.terminology_mappings import TerminologyMappings
from flask_cors import cross_origin
from locutus.api import default_headers
import pdb


class TerminologyMapping(Resource):
    @cross_origin()
    def get(self, id, code):
        term = persistence().collection("Terminology").document(id).get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

        mappings = t.mappings(code)
        response = {"code": code, "mappings": []}

        # We should recieve a dictionary with a single key
        for coding in mappings[code]:
            response["mappings"].append(coding.to_dict())

        return (response, 200, default_headers)

    def delete(self, id, code):
        tmref = (
            persistence()
            .collection("Terminology")
            .document(id)
            .collection("mappings")
            .document(code)
        )

        time_of_delete = tmref.delete()

        response = TerminologyMappings.get_mappings(id)

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        mappings = request.get_json()["mappings"]
        codings = [Coding(**x) for x in mappings]

        tref = persistence().collection("Terminology").document(id)

        term = tref.get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

        t.set_mapping(code, codings)

        response = TerminologyMappings.get_mappings(t.id)

        return (response, 201, default_headers)
