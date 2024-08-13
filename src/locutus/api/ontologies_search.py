from flask_restful import Resource
from locutus import persistence
from locutus.model.ontologies_search import OntologyAPI

from locutus.api import default_headers

class OntologyAPIs(Resource):
    def get(self):
        """
        Retrieve all available OntologyAPIs.
        """
        api_details = OntologyAPI.get_all_api_ontologies()
        return api_details, 200

class OntologyAPIById(Resource):
    def get(self, api_id):
        """
        Retrieve details of a specific OntologyAPI by ID.
        """
        result = OntologyAPI.get_ontologies_by_api_id(api_id)
        if result is None:
            return {"error": "Not found"}, 404
        return result, 200