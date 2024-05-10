from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Coding, Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection

import pdb


class TerminologyRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        term = persistence().collection("Terminology").document(id).get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

        # pdb.set_trace()
        code_updates = body.get("code")
        display_updates = body.get("display")

        # We MUST have at least a code or a display component to be a valid
        # PATCH
        if code_updates is None and display_updates is None:
            return (
                "Must provide codes and/or displays to be PATCHed.",
                400,
                default_headers,
            )

        if code_updates is None:
            code_updates = {}
        if display_updates is None:
            display_updates = {}

        code_list = sorted(
            list(set(list(code_updates.keys()) + list(display_updates.keys())))
        )

        for code in code_list:
            original_code = code
            new_code = code_updates.get(original_code)

            if new_code is None:
                new_code = original_code

            if not t.rename_code(
                original_code=original_code,
                new_code=new_code,
                new_display=display_updates.get(original_code),
            ):
                return (
                    f"{original_code} was not found in the terminology.",
                    404,
                    default_headers,
                )

        mappings = t.mappings()
        response = {
            "terminology": {
                "Reference": f"Terminology/{t.id}",
            },
            "codes": [],
        }
        for code in mappings:
            mapping = {"code": code, "mappings": []}
            for coding in mappings[code]:
                mapping["mappings"].append(coding.to_dict())

            response["codes"].append(mapping)
        return (response, 200, default_headers)


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
