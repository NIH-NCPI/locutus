from flask import Flask, request
from flask_restful import Resource, Api

from locutus.api import init_base_storage
from locutus.api.terminology import Terminology, Terminologies
from locutus.api.table import Table, Tables
from locutus.api.study import Study, Studies
from locutus.api.datadictionary import DataDictionary, DataDictionaries

app = Flask(__name__)
api = Api(app)


# Once we are inside docker, the path will probably be a bit more complex
init_base_storage("test")

api.add_resource(Terminologies, "/api/Terminology")
api.add_resource(Terminology, "/api/Terminology/<string:id>")

api.add_resource(Tables, "/api/Table")
api.add_resource(Table, "/api/Table/<string:id>")

api.add_resource(Studies, "/api/Study")
api.add_resource(Study, "/api/Study/<string:id>")

api.add_resource(DataDictionaries, "/api/DataDictionary")
api.add_resource(DataDictionary, "/api/DataDictionary/<string:id>")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
