from flask_restful import Resource
from locutus.model.ontologies_search import OntologyAPI

class OntologyAPIs(Resource):
    def get(self, api_id=None):
        """
        Retrieve details of all OntologyAPIs or a specific OntologyAPI by ID.
        Args:
            api_id (str): Unique identifier for a specific API. If None, 
            returns all APIs.
        Returns:
            list: A dictionary representing a specific API if `api_id` is provided, 
            or a list of dictionaries representing all APIs if `api_id` is None.
        """
        if api_id is None:
            result = OntologyAPI.get_api_ontologies()
            return result
        else:
            result = OntologyAPI.get_api_ontologies(api_id)
            if not result:
                return {"error": "Ontology API not found"}, 404
            return result, 200