from flask_restful import Resource
from flask import request
from locutus import persistence, FTD_PLACEHOLDERS, normalize_ftd_placeholders
from locutus.model.table import Table
from locutus.model.terminology import Terminology, Coding, CodingMapping, MappingUserInputModel
from locutus.api.terminology_mappings import TerminologyMappings
from flask_cors import cross_origin
from locutus.model.exceptions import *
from locutus.api import default_headers, delete_collection, get_editor


class TableMappings(Resource):
    @classmethod
    def get_mappings(cls, id):
        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)
        try:
            editor = get_editor(body=None, editor=editor_param)
            if user_input_param is not None and editor is None:
                raise LackingUserID(editor)
            
            table = Table.get(id)
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
                        user_input_data = (
                            MappingUserInputModel.generate_mapping_user_input(
                                term.id, code, codingmapping.code, editor
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

            table = Table.get(id)
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
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)


class TableMapping(Resource):
    def get(self, id, code):

        user_input_param = request.args.get("user_input", default=None)
        editor_param = request.args.get("user", default=None)

        try:
            editor = get_editor(body=None, editor=editor_param)
            if user_input_param is not None and editor is None:
                raise LackingUserID(editor)

            table = Table.get(id)
            term = table.terminology.dereference()

            # Ensure codes are not placeholders at this point.
            code = normalize_ftd_placeholders(code)

            mappings = term.mappings(code)
            response = {"code": code, "mappings": []}

            # We should recieve a dictionary with a single key
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        term.id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid != False:
                    response["mappings"].append(codingmapping.to_dict())

            return (response, 200, default_headers)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

            # We should recieve a dictionary with a single key
            for codingmapping in mappings.get(code, []):
                if user_input_param:
                    user_input_data = MappingUserInputModel.generate_mapping_user_input(
                        term.id, code, codingmapping.code, editor
                    )
                    codingmapping.user_input = user_input_data
                # Returns valid=true mappings or mappings without the 'valid' attribute.
                if codingmapping.valid != False:
                    response["mappings"].append(codingmapping.to_dict())

            return (response, 200, default_headers)

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
    def delete(self, id, code):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            table = Table.get(id)
            mapping_count = table.terminology.dereference().delete_mappings(
                editor=editor, code=code
            )

            response = TerminologyMappings.get_mappings(
                table.terminology.reference_id()
            )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            mappings = request.get_json()["mappings"]
            codingmapping = [CodingMapping(**x) for x in mappings]

            table = Table.get(id)
            term = table.terminology.dereference()

            term.set_mapping(code, codingmapping, editor)

            response = TerminologyMappings.get_mappings(term.id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return (response, 201, default_headers)
