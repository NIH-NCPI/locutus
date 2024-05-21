from flask_restful import Resource
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection
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
        mapref = (
            persistence().collection("Terminology").document(id).collection("mappings")
        )
        mapping_count = delete_collection(mapref)

        response = {"terminology_id": id, "mappings_removed": mapping_count}

        return (response, 200, default_headers)

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
