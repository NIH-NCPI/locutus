from flask_restful import Resource
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
                    mapping["mappings"].append(coding.to_dict())

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
        mapping_count = t.dereference().delete_mappings(editor=editor)

        response = {"terminology_id": id, "mappings_removed": mapping_count}

        return (response, 200, default_headers)

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
