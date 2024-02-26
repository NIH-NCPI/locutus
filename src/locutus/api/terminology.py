from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Coding, Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection

import pdb


# class TerminologyMappings(Resource):
#     @classmethod
#     def get_mappings(cls, id):
#         term = persistence().collection("Terminology").document(id).get().to_dict()
#         if "resource_type" in term:
#             del term["resource_type"]

#         t = Term(**term)

#         response = {
#             "terminology": {
#                 "Reference": f"Terminology/{t.id}",
#             },
#             "codes": [],
#         }
#         mappings = t.mappings()

#         for code in mappings:
#             mapping = {"code": code, "mappings": []}
#             for coding in mappings[code]:
#                 mapping["mappings"].append(coding.to_dict())

#             response["codes"].append(mapping)

#         return response

#     @classmethod
#     def get(cls, id):
#         response = cls.get_mappings(id)
#         return (response, 200, default_headers)


# class TerminologyMap(Resource):
#     def get(self, id, code):
#         term = persistence().collection("Terminology").document(id).get().to_dict()
#         if "resource_type" in term:
#             del term["resource_type"]

#         t = Term(**term)

#         mappings = t.mappings(code)
#         response = {"code": code, "mappings": []}

#         # We should recieve a dictionary with a single key
#         for coding in mappings[code]:
#             response["mappings"].append(coding.to_dict())

#         return (response, 200, default_headers)

#     def put(self, id, code):
#         mappings = request.get_json()["mappings"]
#         codings = [Coding(**x) for x in mappings]

#         term = persistence().collection("Terminology").document(id).get().to_dict()
#         if "resource_type" in term:
#             del term["resource_type"]

#         t = Term(**term)

#         t.set_mapping(code, codings)

#         response = TerminologyMappings.get_mappings(t.id)

#         return (response, 201, default_headers)


class Terminologies(Resource):
    def get(self):
        return (
            [x.to_dict() for x in persistence().collection("Terminology").stream()],
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
        t = persistence().collection("Terminology").document(id).get()
        response = t.to_dict()

        if response is not None:
            return response, 200, default_headers
        return (response, 404, default_headers)

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
        mapref = (
            persistence().collection("Terminology").document(id).collection("mappings")
        )
        delete_collection(mapref)
        dref = persistence().collection("Terminology").document(id)
        t = dref.get().to_dict()

        time_of_delete = dref.delete()

        return t, 200, default_headers
