from flask_restful import Resource
from flask import request
from locutus.model.table import Table
from locutus.model.terminology import Terminology, Coding
from locutus.api.terminology_mappings import TerminologyMappings
from flask_cors import cross_origin
from locutus.api import default_headers


class TableProvenance(Resource):
    def get(self, id):
        table = Table.get(id)
        term = table.terminology.dereference()

        prov = term.get_provenance(code="self")

        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}
        return (response, 200, default_headers)


class TableVarProvenance(Resource):
    def get(self, id, code):
        table = Table.get(id)
        term = table.terminology.dereference()

        if code == "ALL":
            code = None
        prov = term.get_provenance(code=code)
        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}

        return (response, 200, default_headers)


class TerminologyProvenance(Resource):
    def get(self, id):
        term = Terminology.get(id)

        prov = term.get_provenance(code="self")
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (response, 200, default_headers)


class TerminologyCodeProvenance(Resource):
    def get(self, id, code):
        term = Terminology.get(id)
        prov = term.get_provenance(code=code)
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (response, 200, default_headers)
