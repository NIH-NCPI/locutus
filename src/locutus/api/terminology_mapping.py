from flask_restful import Resource
from flask import request
from locutus import (
    get_code_index,
    FTD_PLACEHOLDERS,
    normalize_ftd_placeholders,
)
from locutus.model.terminology import (
    Terminology as Term,
    MappingUserInputModel,
)
from locutus.model.coding import (
    Coding, 
    CodingMapping
)
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.model.terminology_mapping import MappingRelationshipModel
from locutus.model.exceptions import *
from locutus.sessions import SessionManager
from flask_cors import cross_origin
from locutus.api import default_headers, get_editor
from bson import json_util 
import json


class TerminologyMapping(Resource):
    @cross_origin()
    def get(self, id, code):
        """
        Retrieves terminology mappings for a given code, optionally including user input details.
        """

        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)

        # Ensure codes are not placeholders at this point.
        code = normalize_ftd_placeholders(code)

        try:
            editor = get_editor(body=None, editor=editor_param)
            if user_input_param is not None and editor is None:
                raise LackingUserID(editor)

            t = Term.get(id)

            mappings = t.mappings(code)
            response = {"code": code, "mappings": []}

            # We should recieve a dictionary with a single key
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid != False:
                    response["mappings"].append(codingmapping.to_dict())

            return (json.loads(json_util.dumps(response)), 200, default_headers)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

    def delete(self, id, code):
        """Soft deletes all mappings for the identified terminology code."""
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            t = Term.get(id)
            t.delete_mappings(editor=editor, code=code)

            response = TerminologyMappings.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        body = request.get_json()

        # Ensure codes are not placeholders at this point.
        code = normalize_ftd_placeholders(code)

        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
            
            mappings = body["mappings"]

            # Ensure each mapping has a 'system' key
            for i, mapping in enumerate(mappings):
                if "system" not in mapping or mapping["system"] is None:
                    raise LackingRequiredParameter(f"Missing required parameter 'system' in mapping at index {i}")

            codingmapping = [CodingMapping(**x) for x in mappings]

            t = Term.get(id)

            # Raise error if the code is not in the terminology
            if not t.has_code(code):
                raise CodeNotPresent(code, id)

            t.set_mapping(code, codingmapping, editor=editor)

            response = TerminologyMappings.get_mappings(t.id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 201, default_headers)


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
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # Raise error if the code is not in the terminology
            t = Term.get(id)
            if not t.has_code(code):
                raise CodeNotPresent(code, id)

            response = MappingRelationshipModel.add_mapping_relationship(
                editor, id, code, mapped_code, mapping_relationship
            )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 200, default_headers)
