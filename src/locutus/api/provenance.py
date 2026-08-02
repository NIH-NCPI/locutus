import json

from bson import json_util
from flask_restful import Resource

from locutus.api import default_headers
from locutus.model.table import Table
from locutus.model.terminology import Terminology


class TableProvenance(Resource):
    def get(self, id: str):
        table = Table.get(id)
        term = table.terminology.dereference()

        prov = term.get_provenance(code="self")

        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}
        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TableVarProvenance(Resource):
    def get(self, id: str, code: str):
        table = Table.get(id)
        term = table.terminology.dereference()

        if code == "ALL":
            code = None
        prov = term.get_provenance(code=code)
        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}

        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TerminologyProvenance(Resource):
    def get(self, id: str):
        term = Terminology.get(id)

        prov = term.get_provenance(code="self")
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TerminologyCodeProvenance(Resource):
    def get(self, id: str, code: str):
        term = Terminology.get(id)
        prov = term.get_provenance(code=code)
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (json.loads(json_util.dumps(response)), 200, default_headers)
