from flask_restful import Resource
from flask import request
from locutus import logger
from locutus.api import default_headers
from locutus.model.ontologies_search import OntologyAPI, OntologyAPISearchModel
from locutus.model.exceptions import *
import pdb

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

        try:
            keyword_param = request.args.get("keyword", default=None)
            if keyword_param is None:
                raise LackingRequiredParameter("keyword")

            ontology_param = request.args.get("selected_ontologies", default=None)
            if ontology_param:
                ontology_param = [onto.strip() for onto in ontology_param.split(",")]
            if ontology_param is None:
                raise LackingRequiredParameter("selected_ontologies")
            
            pref_api = request.args.get("selected_api", default=None)
            if pref_api:
                pref_api = [api.strip() for api in pref_api.split(",")]
            if pref_api is None:
                raise LackingRequiredParameter("selected_api")
            
            results_n_param = request.args.get("results_per_page", default=None)
            if results_n_param is None:
                raise LackingRequiredParameter("results_per_page")
            
            start_param = request.args.get("start_index", default=None)
            if start_param is None:
                raise LackingRequiredParameter("start")

            search_results = OntologyAPISearchModel.run_search_dragon(
                keyword_param, ontology_param, pref_api, results_n_param, start_param
            )
            return (search_results, 200, default_headers)
        
        except ValueError as e:
            return {f"error {keyword_param, ontology_param, pref_api, results_n_param, start_param}": str(e)}, 400, default_headers
        
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
