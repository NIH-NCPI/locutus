from flask import request
from flask.typing import ResponseReturnValue
from flask_cors import cross_origin
from flask_restful import Resource

from locutus import normalize_ftd_placeholders
from locutus.api import default_headers, get_editor
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.auth import require_read_access, require_write_access
from locutus.model.coding import CodingMapping
from locutus.model.exceptions import APIError, LackingUserID
from locutus.model.table import Table
from locutus.model.terminology import MappingUserInputModel


class TableMappings(Resource):
    @classmethod
    def get_mappings(cls, id: str) -> dict:
        """Raises APIError rather than catching it -- callers (just .get()
        below) are responsible for turning that into a response. Catching it
        here and returning an (error_dict, status, headers) tuple instead
        used to be indistinguishable from a real success dict to the caller's
        `if response is not None` check, so a LackingUserID (or any other
        APIError) silently came back as a 200 wrapping the error tuple as its
        body."""
        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)

        editor = get_editor(body=None, editor=editor_param)
        if user_input_param is not None and editor is None:
            raise LackingUserID(editor)

        # require_read_access (on the public .get() this backs) already
        # confirmed this id exists.
        table = Table.get(id)
        assert table is not None
        term = table.terminology.dereference()

        response = {
            "terminology": {
                "Reference": f"Terminology/{term.id}",
            },
            "codes": [],
        }
        mappings = term.mappings()

        for code in mappings:
            mapping = {"code": code, "mappings": []}
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    # user_input_param truthy + no LackingUserID raised
                    # above together guarantee editor is set.
                    assert editor is not None
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        term.id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid:
                    mapping["mappings"].append(codingmapping.to_dict())

            response["codes"].append(mapping)

        return response

    @classmethod
    @require_write_access("Table", "id")
    def delete(cls, id: str) -> ResponseReturnValue:
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # require_write_access already confirmed this id exists.
            table = Table.get(id)
            assert table is not None
            mapping_count = table.terminology.dereference().delete_mappings(
                editor=editor
            )

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        response = {
            "terminology_id": table.terminology.dereference().id,
            "mappings_removed": mapping_count,
        }

        return (response, 200, default_headers)

    @classmethod
    @require_read_access("Table", "id")
    def get(cls, id: str) -> ResponseReturnValue:
        try:
            response = cls.get_mappings(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        return (response, 200, default_headers)


class TableMapping(Resource):
    @require_read_access("Table", "id")
    def get(self, id: str, code: str) -> ResponseReturnValue:

        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)

        try:
            editor = get_editor(body=None, editor=editor_param)
            if user_input_param is not None and editor is None:
                raise LackingUserID(editor)

            # require_read_access already confirmed this id exists.
            table = Table.get(id)
            assert table is not None
            term = table.terminology.dereference()

            # Ensure codes are not placeholders at this point.
            code = normalize_ftd_placeholders(code)

            mappings = term.mappings(code)
            response = {"code": code, "mappings": []}

            # We should recieve a dictionary with a single key
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    # user_input_param truthy + no LackingUserID raised
                    # above together guarantee editor is set.
                    assert editor is not None
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        term.id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid:
                    response["mappings"].append(codingmapping.to_dict())

            return (response, 200, default_headers)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

    @require_write_access("Table", "id")
    def delete(self, id: str, code: str) -> ResponseReturnValue:
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            # require_write_access already confirmed this id exists.
            table = Table.get(id)
            assert table is not None
            table.terminology.dereference().delete_mappings(editor=editor, code=code)

            response = TerminologyMappings.get_mappings(
                table.terminology.reference_id()
            )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    @require_write_access("Table", "id")
    def put(self, id: str, code: str) -> ResponseReturnValue:
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            mappings = request.get_json()["mappings"]

            codingmapping = [CodingMapping(**x) for x in mappings]
            # require_write_access already confirmed this id exists.
            table = Table.get(id)
            assert table is not None
            term = table.terminology.dereference()

            term.set_mapping(code, codingmapping, editor)

            response = TerminologyMappings.get_mappings(term.id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (response, 201, default_headers)
