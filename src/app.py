from flask import Flask, request, render_template, url_for

from flask_cors import CORS, cross_origin
from flask_restful import Resource, Api


# from locutus import init_base_storage

# Once we are inside docker, the path will probably be a bit more complex
# init_base_storage("test")

from locutus.api.terminology import (
    Terminology,
    Terminologies,
    TerminologyRenameCode,
    TerminologyEdit,
)
from locutus.api.preferences_term import (
    OntologyAPISearchPreferences,
    PreferredTerminology,
)
from locutus.api.terminology_mapping import TerminologyMapping, MappingRelationship
from locutus.api.terminology_mappings import TerminologyMappings
from locutus.api.table import (
    Table,
    Tables,
    HarmonyCSV,
    TableEdit,
    TableRenameCode,
)
from locutus.api.preferences_table import (
    TableOntologyAPISearchPreferences,
    TablePreferredTerminology,
)
from locutus.api.table_mappings import TableMappings, TableMapping
from locutus.api.table_load import TableLoader, TableLoader2
from locutus.api.provenance import (
    TableProvenance,
    TableVarProvenance,
    TerminologyProvenance,
    TerminologyCodeProvenance,
)
from locutus.api.study import Study, Studies, StudyEdit
from locutus.api.datadictionary import (
    DataDictionary,
    DataDictionaries,
    DataDictionaryTable,
)
from locutus.api.ontologies_search import OntologyAPIs, OntologyAPISearch
from locutus.api.sessions import SessionStart, SessionTerminate, SessionStatus

from locutus.sessions import SessionManager

from locutus.api.user_input import TerminologyUserInput, TableUserInput

from locutus.api.metadata import Version

from locutus.api.user_prefs import UserPrefOntoFilters


app = Flask(__name__)
app.url_map.strict_slashes = False  # allow trailing slashes(code/'../')
CORS(app)
api = Api(app)

# Sessions
session_manager = SessionManager(app)

api.add_resource(OntologyAPISearch,"/api/ontology_search")

# GET app version
api.add_resource(Version, "/api/version")

api.add_resource(
    SessionStart,
    "/api/session/start",
    resource_class_kwargs={"session_manager": session_manager},
)
api.add_resource(
    SessionTerminate,
    "/api/session/terminate",
    resource_class_kwargs={"session_manager": session_manager},
)
api.add_resource(
    SessionStatus,
    "/api/session/status",
    resource_class_kwargs={"session_manager": session_manager},
)

api.add_resource(UserPrefOntoFilters, "/api/user/preferences/ontologies")

# Terminology GET (all terminologies)/POST (new without an ID)
api.add_resource(Terminologies, "/api/Terminology")
# Terminology GET (by ID), PUT (with id, can be create if you have an ID
# already), DELETE (by ID)
api.add_resource(Terminology, "/api/Terminology/<string:id>")
api.add_resource(TerminologyMappings, "/api/Terminology/<string:id>/mapping")
api.add_resource(
    TerminologyMapping, "/api/Terminology/<string:id>/mapping/<path:code>"
)
api.add_resource(
    MappingRelationship,
    "/api/Terminology/<string:id>/mapping_relationship/<path:code>/mapping/<path:mapped_code>",
)
api.add_resource(
    TerminologyRenameCode,
    "/api/Terminology/<string:id>/rename",
)
# GET/POST/PUT/DELETE Ontology API preferences at Terminology level
api.add_resource(
    OntologyAPISearchPreferences,
    "/api/Terminology/<string:id>/filter",
    endpoint="onto_terminology_preferences",
)
# GET/POST/PUT/DELETE Ontology API preferences at Code level
api.add_resource(
    OntologyAPISearchPreferences,
    "/api/Terminology/<string:id>/filter/<path:code>",
    endpoint="onto_code_preferences",
)
# GET/PUT/DELETE preferred_terminology sub-collection associated with a Terminology
api.add_resource(
    PreferredTerminology, "/api/Terminology/<string:id>/preferred_terminology"
)

# GET/PUT user_input sub-collection associated with a Terminology/code/input type
api.add_resource(
    TerminologyUserInput,
    "/api/Terminology/<string:id>/user_input/<path:code>/mapping/<path:mapped_code>/<string:type>",
)

# Terminology/<id>/<code> PUT or DELETE depending on add or remove individual
# code. Body for put will include display in addition to the code (and possibly
# other stuff in the future. )
api.add_resource(TerminologyEdit, "/api/Terminology/<string:id>/code/<path:code>")
api.add_resource(
    TableRenameCode,
    "/api/Table/<string:id>/rename",
)
api.add_resource(Tables, "/api/Table")
api.add_resource(Table, "/api/Table/<string:id>")

# PUT, DELETE
api.add_resource(TableEdit, "/api/Table/<string:id>/variable/<path:code>")

# GET/DELETE/PUT
api.add_resource(TableMapping, "/api/Table/<string:id>/mapping/<path:code>")
# GET/DELETE
api.add_resource(TableMappings, "/api/Table/<string:id>/mapping")
api.add_resource(HarmonyCSV, "/api/Table/<string:id>/harmony")
# GET/POST/PUT/DELETE Ontology API preferences at Table level
api.add_resource(
    TableOntologyAPISearchPreferences,
    "/api/Table/<string:id>/filter",
    endpoint="onto_table_preferences",
)
# GET/POST/PUT/DELETE Ontology API preferences at Variable level
api.add_resource(
    TableOntologyAPISearchPreferences,
    "/api/Table/<string:id>/filter/<path:code>",
    endpoint="onto_var_preferences",
)

# GET/PUT/DELETE preferred_terminology sub-collection associated with a Table (shadow Terminology)
api.add_resource(
    TablePreferredTerminology, "/api/Table/<string:id>/preferred_terminology"
)
api.add_resource(
    TableUserInput, "/api/Table/<string:id>/user_input/<path:code>/mapping/<path:mapped_code>/<string:type>"
)

# POST
api.add_resource(TableLoader, "/api/LoadTable")
# PUT (by ID)
api.add_resource(TableLoader2, "/api/LoadTable/<string:id>")

api.add_resource(Studies, "/api/Study")
api.add_resource(Study, "/api/Study/<string:id>")
api.add_resource(StudyEdit, "/api/Study/<string:id>/dd/<string:dd_id>")

api.add_resource(DataDictionaries, "/api/DataDictionary")
api.add_resource(DataDictionary, "/api/DataDictionary/<string:id>")

# Currently, only DELETE
api.add_resource(
    DataDictionaryTable, "/api/DataDictionary/<string:id>/Table/<string:table_id>"
)

api.add_resource(TerminologyProvenance, "/api/Provenance/Terminology/<string:id>")
api.add_resource(
    TerminologyCodeProvenance,
    "/api/Provenance/Terminology/<string:id>/code/<path:code>",
)
api.add_resource(TableProvenance, "/api/Provenance/Table/<string:id>")
api.add_resource(
    TableVarProvenance, "/api/Provenance/Table/<string:id>/code/<path:code>"
)

# GET Ontology All OntologyAPIs and ontology details
api.add_resource(OntologyAPIs, "/api/OntologyAPI", endpoint="all_ontologies")
# GET (by ID) Single OntologyAPI and ontology details
api.add_resource(
    OntologyAPIs, "/api/OntologyAPI/<string:api_id>", endpoint="ontology_by_id"
)


@app.errorhandler(404)
@cross_origin(allow_headers=["Content-Type"])
def not_found(e):
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
