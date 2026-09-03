import json

from bson import json_util
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import require_read_access
from locutus.model.table import Table
from locutus.model.terminology import Terminology


class TableProvenance(Resource):
    @require_read_access("Table", "id")
    def get(self, id: str):
        # require_read_access already confirmed this id exists.
        table = Table.get(id)
        assert table is not None
        term = table.terminology.dereference()

        prov = term.get_provenance(code="self")

        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}
        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TableVarProvenance(Resource):
    @require_read_access("Table", "id")
    def get(self, id: str, code: str):
        # require_read_access already confirmed this id exists.
        table = Table.get(id)
        assert table is not None
        term = table.terminology.dereference()

        prov_code = None if code == "ALL" else code
        prov = term.get_provenance(code=prov_code)
        response = {"table": {"Reference": f"Table/{table.id}"}, "provenance": prov}

        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TerminologyProvenance(Resource):
    @require_read_access("Terminology", "id")
    def get(self, id: str):
        # require_read_access already confirmed this id exists.
        term = Terminology.get(id)
        assert term is not None

        prov = term.get_provenance(code="self")
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (json.loads(json_util.dumps(response)), 200, default_headers)


class TerminologyCodeProvenance(Resource):
    @require_read_access("Terminology", "id")
    def get(self, id: str, code: str):
        # require_read_access already confirmed this id exists.
        term = Terminology.get(id)
        assert term is not None
        prov = term.get_provenance(code=code)
        response = {
            "terminology": {"Reference": f"Terminology/{term.id}"},
            "provenance": prov,
        }

        return (json.loads(json_util.dumps(response)), 200, default_headers)
