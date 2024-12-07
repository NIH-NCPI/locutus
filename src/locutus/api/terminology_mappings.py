from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term, MappingUserInputModel
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection, get_editor
from sessions import SessionManager
import pdb


class TerminologyMappings(Resource):
    @classmethod
    def get_mappings(cls, id):
        """
        Retrieves all mappings for a given terminology, optionally including user input details.
        """
        user_input_param = request.args.get("user_input", default=None)
        user_id = (
            SessionManager.create_user_id()
        )  # Retrieves the user_id or sets to None

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
                for codingmapping in mappings.get(code, []):
                    if user_input_param:
                        user_input_data = (
                            MappingUserInputModel.generate_mapping_user_input(
                                id, code, codingmapping.code, user_id
                            )
                        )
                        codingmapping.user_input = user_input_data
                    # Returns valid=true mappings or mappings without the 'valid' attribute.
                    if not hasattr(codingmapping, "valid") or codingmapping.valid:
                        mapping["mappings"].append(codingmapping.to_dict())

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
        t.delete_mappings(editor=editor)

        response = TerminologyMappings.get_mappings(id)

        return (response, 200, default_headers)

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
