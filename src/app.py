from flask import Flask, request, render_template, url_for

from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api

import pdb

# from locutus import init_base_storage

# Once we are inside docker, the path will probably be a bit more complex
# init_base_storage("test")

from locutus.api.terminology import (
    Terminology,
    Terminologies,
    TerminologyRenameCode,
    TerminologyEdit,
)
from locutus.api.terminology_mapping import TerminologyMapping
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.api.table import Table, Tables, HarmonyCSV, TableEdit, TableRenameCode
from locutus.api.table_mappings import TableMappings, TableMapping
from locutus.api.table_load import TableLoader
from locutus.api.study import Study, Studies
from locutus.api.datadictionary import (
    DataDictionary,
    DataDictionaries,
    DataDictionaryTable,
)

app = Flask(__name__)
CORS(app)
api = Api(app)

# Terminology GET (all terminologies)/POST (new without an ID)
api.add_resource(Terminologies, "/api/Terminology")
# Terminology GET (by ID), PUT (with id, can be create if you have an ID
# already), DELETE (by ID)
api.add_resource(Terminology, "/api/Terminology/<string:id>")
api.add_resource(TerminologyMappings, "/api/Terminology/<string:id>/mapping")
api.add_resource(
    TerminologyMapping, "/api/Terminology/<string:id>/mapping/<string:code>"
)
api.add_resource(
    TerminologyRenameCode,
    "/api/Terminology/<string:id>/rename",
)
# Terminology/<id>/<code> PUT or DELETE depending on add or remove individual
# code. Body for put will include display in addition to the code (and possibly
# other stuff in the future. )
api.add_resource(TerminologyEdit, "/api/Terminology/<string:id>/code/<string:code>")
api.add_resource(
    TableRenameCode,
    "/api/Table/<string:id>/rename",
)
api.add_resource(Tables, "/api/Table")
api.add_resource(Table, "/api/Table/<string:id>")

# PUT, DELETE
api.add_resource(TableEdit, "/api/Table/<string:id>/variable/<string:code>")

# GET/DELETE/PUT
api.add_resource(TableMapping, "/api/Table/<string:id>/mapping/<string:code>")
# GET/DELETE
api.add_resource(TableMappings, "/api/Table/<string:id>/mapping")
api.add_resource(HarmonyCSV, "/api/Table/<string:id>/harmony")
api.add_resource(TableLoader, "/api/LoadTable")

api.add_resource(Studies, "/api/Study")
api.add_resource(Study, "/api/Study/<string:id>")

api.add_resource(DataDictionaries, "/api/DataDictionary")
api.add_resource(DataDictionary, "/api/DataDictionary/<string:id>")

# Currently, only DELETE
api.add_resource(
    DataDictionaryTable, "/api/DataDictionary/<string:id>/Table/<string:table_id>"
)


@app.errorhandler(404)
@cross_origin(allow_headers=["Content-Type"])
def not_found(e):
    # pdb.set_trace()
    return (
        render_template(
            "error_404.html",
            image=url_for("static", filename="does_not_compute.jpg"),
            error=e,
        ),
        404,
    )


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
