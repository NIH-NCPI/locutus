from flask_restful import Resource
from flask import request
from locutus import logger
from locutus.api import default_headers
from locutus.model.ontologies_search import OntologyAPI, OntologyAPISearchModel

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
        
class OntologyAPISearch(Resource):
    """
    Runs the generic search
    """
    def get(self):

        keyword_param = request.args.get("keyword", default=None)

        ontology_param = request.args.get("preferred_ontologies", default=None)
        if ontology_param:
            ontology_param = ["preferred_ontologies".strip() for onto in ontology_param.split(",")]

        pref_api = request.args.get("api", default=None)
        if pref_api:
            pref_api = [api.strip() for api in pref_api.split(",")]

        logger.debug(f"keyword_param: {keyword_param}")
        logger.debug(f"ontology_param: {ontology_param}")
        logger.debug(f"pref_api: {pref_api}")

        try:
            search_results = OntologyAPISearchModel.run_search_dragon(
                keyword_param, ontology_param, pref_api
            )
            return (search_results, 200, default_headers)
        except ValueError as e:
            return {f"error {keyword_param, ontology_param,pref_api}": str(e)}, 400, default_headers