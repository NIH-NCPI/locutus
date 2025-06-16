from flask_restful import Resource
from flask import request
from locutus import logger
from locutus.api import default_headers
from locutus.model.ontologies_search import OntologyAPI, OntologyAPISearchModel
from locutus.model.exceptions import *
from locutus.model.exceptions import InvalidValueError


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

            # Convert string parameters to appropriate types
            try:
                results_n_param = int(results_n_param)
                start_param = int(start_param)
            except ValueError:
                raise InvalidValueError(value="results_per_page or start_index", 
                                       valid_values="These parameters must be valid integers")
                
            search_results = OntologyAPISearchModel.run_search_dragon(
                keyword_param, ontology_param, pref_api, results_n_param, start_param
            )
            return (search_results, 200, default_headers)
        
        except ValueError as e:
            error_msg = f"Invalid parameters: keyword={keyword_param}, ontologies={ontology_param}, api={pref_api}, results_per_page={results_n_param}, start_index={start_param}. Error: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}, 400, default_headers
        
        except InvalidValueError as e:
            logger.error(f"Invalid value error: {e}")
            return e.to_dict(), e.status_code, default_headers
        
        except APIError as e:
            logger.error(f"API Error: {e}")
            return e.to_dict(), e.status_code, default_headers
            
        except Exception as e:
            error_msg = f"Unexpected error during ontology search: {str(e)}"
            logger.error(error_msg)
            return {"error": error_msg}, 500, default_headers
