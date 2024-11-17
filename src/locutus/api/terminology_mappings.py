from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection, get_editor
import pdb


class TerminologyMappings(Resource):
    @classmethod
    def get_mappings(cls, id):

        termref = persistence().collection("Terminology").document(id)
        term = termref.get().to_dict()

        if term is not None:
            if "resource_type" in term:
                del term["resource_type"]

            t = Term(**term)

            response = {
                "terminology": {
                    "Reference": f"Terminology/{t.id}",
                },
                "codes": [],
            }
            mappings = t.mappings()

            for code in mappings:
                mapping = {"code": code, "mappings": []}
                for coding in mappings[code]:
                    print(f"Raw coding data: {coding.__dict__}")
                    if not hasattr(coding, 'valid') or coding.valid:
                        coding_dict = {
                            "code": coding.code,
                            "display": coding.display,
                            "system": coding.system,
                            "valid": coding.valid if hasattr(coding, 'valid') else None
                        }
                        
                        mapping["codes"].append(coding_dict)

            if mapping["codes"]:
                response["codes"].append(mapping)

            return response
        return None

    @classmethod
    def delete(cls, id):
        body = request.get_json()
        editor = get_editor(body)
        if editor is None:
            return ("Terminology DELETE requires an editor!", 400, default_headers)

        t = Term.get(id)
        t.soft_delete_mappings(editor=editor)

        response = TerminologyMappings.get_mappings(id)

        return (response, 200, default_headers)

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
