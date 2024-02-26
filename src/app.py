from flask import Flask, request

from flask_cors import CORS
from flask_restful import Resource, Api

# from locutus import init_base_storage

# Once we are inside docker, the path will probably be a bit more complex
# init_base_storage("test")

from locutus.api.terminology import Terminology, Terminologies
from locutus.api.terminology_mapping import TerminologyMapping
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.api.table import Table, Tables
from locutus.api.table_load import TableLoader
from locutus.api.study import Study, Studies
from locutus.api.datadictionary import DataDictionary, DataDictionaries

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

api.add_resource(Tables, "/api/Table")
api.add_resource(Table, "/api/Table/<string:id>")
api.add_resource(TableLoader, "/api/LoadTable")

api.add_resource(Studies, "/api/Study")
api.add_resource(Study, "/api/Study/<string:id>")

api.add_resource(DataDictionaries, "/api/DataDictionary")
api.add_resource(DataDictionary, "/api/DataDictionary/<string:id>")


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
