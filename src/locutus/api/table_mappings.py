from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table
from locutus.model.terminology import Terminology, Coding, CodingMapping
from locutus.api.terminology_mappings import TerminologyMappings
from flask_cors import cross_origin
from locutus.model.exceptions import *
from locutus.api import default_headers, delete_collection, get_editor


class TableMappings(Resource):
    @classmethod
    def get_mappings(cls, id):
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
            for codingmapping in mappings[code]:
                mapping["mappings"].append(codingmapping.to_dict())

            response["codes"].append(mapping)

        return response

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
        table = Table.get(id)
        term = table.terminology.dereference()

        mappings = term.mappings(code)
        response = {"code": code, "mappings": []}

        for codingmapping in mappings[code]:
            response["mappings"].append(codingmapping.to_dict())

        return (response, 200, default_headers)

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
