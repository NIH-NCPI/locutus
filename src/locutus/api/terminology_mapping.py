import json

from bson import json_util
from flask import request
from flask_restful import Resource

from locutus import (
    normalize_ftd_placeholders,
)
from locutus.api import default_headers, get_editor
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.auth import require_read_access, require_write_access
from locutus.model.coding import CodingMapping
from locutus.model.exceptions import (
    APIError,
    CodeNotPresent,
    LackingRequiredParameter,
    LackingUserID,
)
from locutus.model.terminology import (
    MappingUserInputModel,
)
from locutus.model.terminology import (
    Terminology as Term,
)
from locutus.model.terminology_mapping import MappingRelationshipModel


class TerminologyMapping(Resource):
    @require_read_access("Terminology", "id")
    def get(self, id: str, code: str):
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

            # require_read_access already confirmed this id exists.
            t = Term.get(id)
            assert t is not None

            mappings = t.mappings(code)
            response = {"code": code, "mappings": []}

            # We should recieve a dictionary with a single key
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    # user_input_param truthy + no LackingUserID raised
                    # above together guarantee editor is set.
                    assert editor is not None
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid:
                    response["mappings"].append(codingmapping.to_dict())

            return (json.loads(json_util.dumps(response)), 200, default_headers)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

    @require_write_access("Terminology", "id")
    def delete(self, id: str, code: str):
        """Soft deletes all mappings for the identified terminology code."""
        # silent=True: a DELETE commonly carries no body at all (by REST
        # convention, and in practice from this frontend) -- body here is
        # only ever used for the optional legacy editor fallback below, so
        # a missing/empty body must not crash the request before that
        # fallback (the active session) gets a chance to supply it.
        body = request.get_json(silent=True)
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # require_write_access already confirmed this id exists.
            t = Term.get(id)
            assert t is not None
            t.delete_mappings(editor=editor, code=code)

            response = TerminologyMappings.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 200, default_headers)

    @require_write_access("Terminology", "id")
    def put(self, id: str, code: str):
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
                    raise LackingRequiredParameter(
                        f"Missing required parameter 'system' in mapping at index {i}"
                    )

            codingmapping = [CodingMapping(**x) for x in mappings]

            # require_write_access already confirmed this id exists.
            t = Term.get(id)
            assert t is not None

            # Raise error if the code is not in the terminology
            if not t.has_code(code):
                raise CodeNotPresent(code, id)

            t.set_mapping(code, codingmapping, editor=editor)

            response = TerminologyMappings.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 201, default_headers)


class MappingRelationship(Resource):
    @require_write_access("Terminology", "id")
    def put(self, id: str, code: str, mapped_code: str):
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

            # require_write_access already confirmed this id exists.
            t = Term.get(id)
            assert t is not None

            # Raise error if the code is not in the terminology
            if not t.has_code(code):
                raise CodeNotPresent(code, id)

            response = MappingRelationshipModel.add_mapping_relationship(
                editor, id, code, mapped_code, mapping_relationship
            )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (json.loads(json_util.dumps(response)), 200, default_headers)
