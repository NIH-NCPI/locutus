from flask_restful import Resource
from flask import request
from locutus import persistence, FTD_PLACEHOLDERS, normalize_ftd_placeholders
from locutus.model.terminology import Terminology as Term, MappingUserInputModel
from locutus.model.exceptions import *
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection, get_editor
from locutus.sessions import SessionManager
import pdb


class TerminologyMappings(Resource):
    @classmethod
    def get_mappings(cls, id):
        """
        Retrieves all mappings for a given terminology, optionally including user input details.
        """
        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)
        
        try:
            editor = get_editor(body=None, editor=editor_param)
            if user_input_param is not None and editor is None:
                raise LackingUserID(editor)
            
            termref = persistence().collection("Terminology").document(id)
            term = termref.get().to_dict()

            if term is not None:
                # Remove MongoDB-specific fields before passing to constructor
                if "resource_type" in term:
                    del term["resource_type"]
                if "_id" in term:
                    del term["_id"]

                t = Term(**term)

                response = {
                    "terminology": {
                        "Reference": f"Terminology/{t.id}",
                    },
                    "codes": [],
                }
                mappings = t.mappings()

                for code in mappings:

                    # Ensure codes are not placeholders at this point.
                    code = normalize_ftd_placeholders(code)

                    mapping = {"code": code, "mappings": []}
                    for codingmapping in mappings.get(code, []):
                        if user_input_param:
                            user_input_data = (
                                MappingUserInputModel.generate_mapping_user_input(
                                    id, code, codingmapping.code, editor
                                )
                            )
                            codingmapping.user_input = user_input_data
                        # Returns valid=true mappings or mappings without the 'valid' attribute.
                        if codingmapping.valid != False:
                            mapping["mappings"].append(codingmapping.to_dict())

                    response["codes"].append(mapping)

            return response

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

    @classmethod
    def delete(cls, id):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            t = Term.get(id)
            t.delete_mappings(editor=editor)

            response = TerminologyMappings.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        return (response, 200, default_headers)

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
