from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table
from locutus.model.terminology import Terminology, Coding
from locutus.api.terminology_mappings import TerminologyMappings
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection


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
            for coding in mappings[code]:
                mapping["mappings"].append(coding.to_dict())

            response["codes"].append(mapping)

        return response

    @classmethod
    def delete(cls, id):
        table = Table.get(id)
        term_id = table.terminology.reference_id()

        mapref = (
            persistence()
            .collection("Terminology")
            .document(term_id)
            .collection("mappings")
        )
        mapping_count = delete_collection(mapref)

        response = {"terminology_id": term_id, "mappings_removed": mapping_count}

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

        for coding in mappings[code]:
            response["mappings"].append(coding.to_dict())

        return (response, 200, default_headers)

    def delete(self, id, code):
        table = Table.get(id)
        term_id = table.terminology.reference_id()
        tmref = (
            persistence()
            .collection("Terminology")
            .document(term_id)
            .collection("mappings")
            .document(code)
        )

        time_of_delete = tmref.delete()

        response = TerminologyMappings.get_mappings(term_id)

        return (response, 200, default_headers)

    @cross_origin(allow_headers=["Content-Type"])
    def put(self, id, code):
        mappings = request.get_json()["mappings"]
        codings = [Coding(**x) for x in mappings]

        table = Table.get(id)
        term = table.terminology.dereference()

        term.set_mapping(code, codings)

        response = TerminologyMappings.get_mappings(term.id)

        return (response, 201, default_headers)
