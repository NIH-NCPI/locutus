from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Terminology as Term, Coding, CodingMapping
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.model.terminology_mapping import MappingRelationshipModel
from sessions import SessionManager
from flask_cors import cross_origin
from locutus.api import default_headers, get_editor
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
        for codingmapping in mappings[code]:
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
            return ("mappings DELETE requires an editor!", 400, default_headers)

        t = Term.get(id)
        t.delete_mappings(editor=editor, code=code)

        response = TerminologyMappings.get_mappings(id)

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        body = request.get_json()
        editor = get_editor(body)
        if editor is None:
            return ("This action requires an editor!", 400, default_headers)

        mappings = body["mappings"]
        codingmapping = [CodingMapping(**x) for x in mappings]

        tref = persistence().collection("Terminology").document(id)

        term = tref.get().to_dict()
        if "resource_type" in term:
            del term["resource_type"]

        t = Term(**term)

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

        # Return session user, editor(request body), or None 
        user_id = get_editor(body)

        # Get the session id, or fallback to use the editor as the user_id
        if not user_id:
            raise ValueError (f"This task requires an editor")

        response = MappingRelationshipModel.add_mapping_relationship(
            user_id, id, code, mapped_code, mapping_relationship
        )

        return (response, 200, default_headers)
