import json

from bson import json_util
from flask import request
from flask.typing import ResponseReturnValue
from flask_restful import Resource

from locutus import normalize_ftd_placeholders
from locutus.api import default_headers, get_editor
from locutus.auth import require_read_access, require_write_access
from locutus.model.exceptions import APIError, LackingUserID
from locutus.model.terminology import MappingUserInputModel
from locutus.model.terminology import Terminology as Term


class TerminologyMappings(Resource):
    @classmethod
    def get_mappings(cls, id: str) -> dict:
        """
        Retrieves all mappings for a given terminology, optionally including
        user input details. Raises APIError rather than catching it --
        callers are responsible for turning that into a response. Catching
        it here and returning an (error_dict, status, headers) tuple instead
        used to be indistinguishable from a real success dict to a caller's
        `if response is not None` check, so a LackingUserID (or any other
        APIError) silently came back as a 200/201 wrapping the error tuple
        as its body.
        """
        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)

        editor = get_editor(body=None, editor=editor_param)
        if user_input_param is not None and editor is None:
            raise LackingUserID(editor)

        # require_read_access/require_write_access (on this class's and
        # TerminologyMapping's decorated public methods) already confirmed
        # this id exists.
        term = Term.get(id)
        assert term is not None

        response = {
            "terminology": {
                "Reference": f"Terminology/{term.id}",
            },
            "codes": [],
        }
        mappings = term.mappings()

        for code in mappings:
            # Ensure codes are not placeholders at this point.
            code = normalize_ftd_placeholders(code)

            mapping = {"code": code, "mappings": []}
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
                    mapping["mappings"].append(codingmapping.to_dict())

            response["codes"].append(mapping)

        return json.loads(json_util.dumps(response))

    @classmethod
    @require_write_access("Terminology", "id")
    def delete(cls, id: str) -> ResponseReturnValue:
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # require_write_access already confirmed this id exists.
            t = Term.get(id)
            assert t is not None
            t.delete_mappings(editor=editor)

            response = cls.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        return (response, 200, default_headers)

    @classmethod
    @require_read_access("Terminology", "id")
    def get(cls, id: str) -> ResponseReturnValue:
        try:
            response = cls.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        return (response, 200, default_headers)
