from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import (
    Terminology as Term,
    Coding,
    CodingMapping,
    MappingUserInputModel,
)
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.model.terminology_mapping import MappingRelationshipModel
from locutus.model.exceptions import *
from sessions import SessionManager
from flask_cors import cross_origin
from locutus.api import default_headers, get_editor
import pdb


class TerminologyMapping(Resource):
    @cross_origin()
    def get(self, id, code):
        """
        Retrieves terminology mappings for a given code, optionally including user input details.
        """

        user_input_param = request.args.get("user_input", default=None)
        user_id = get_editor()  # Retrieves the user_id or sets to None

        term = persistence().collection("Terminology").document(id).get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

        mappings = t.mappings(code)
        response = {"code": code, "mappings": []}

        # We should recieve a dictionary with a single key
        for codingmapping in mappings.get(code, []):
            if user_input_param:
                user_input_data = MappingUserInputModel.generate_mapping_user_input(
                    id, code, codingmapping.code, user_id
                )
                codingmapping.user_input = user_input_data
            # Returns valid=true mappings or mappings without the 'valid' attribute.
            if not hasattr(codingmapping, 'valid') or codingmapping.valid:
                response["mappings"].append(codingmapping.to_dict())

        return (response, 200, default_headers)

    def delete(self, id, code):
        """Soft deletes all mappings for the identified terminology code.
        """
        body = request.get_json()
        editor = get_editor(body)
        if editor is None:
            raise LackingUserID(editor)

        t = Term.get(id)
        t.delete_mappings(editor=editor, code=code)

        response = TerminologyMappings.get_mappings(id)

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        body = request.get_json()
        editor = get_editor(body)
        if editor is None:
            raise LackingUserID(editor)

        mappings = body["mappings"]
        codingmapping = [CodingMapping(**x) for x in mappings]

        tref = persistence().collection("Terminology").document(id)

        term = tref.get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

        # Raise error if the code is not in the terminology
        if not t.has_code(code): 
            raise CodeNotPresent(code, id)

        t.set_mapping(code, codingmapping, editor=editor)

        response = TerminologyMappings.get_mappings(t.id)

        return (response, 201, default_headers)

class MappingRelationship(Resource):

    def put(self, id, code, mapped_code):
        body = request.get_json()

        mapping_relationship = body.get("mapping_relationship")
        if mapping_relationship is None:
            return (
                "This endpoint requires mapping_relationship!",
                400,
                default_headers,
            )

        editor = get_editor(body)
        if editor is None:
            raise LackingUserID(editor)

        # Raise error if the code is not in the terminology
        t = Term.get(id)
        if not t.has_code(code): 
            raise CodeNotPresent(code, id)
        
        response = MappingRelationshipModel.add_mapping_relationship(
            editor, id, code, mapped_code, mapping_relationship
        )

        return (response, 200, default_headers)
