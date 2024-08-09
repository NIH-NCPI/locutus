from flask_restful import Resource
from locutus import persistence

from locutus.api import default_headers

class OntologyAPIs(Resource):
    def get(self):
        """
        Retrieve titles of the available OntologyAPIs.
        """
        ontology_apis = persistence().collection("OntologyAPI").stream()

        # Fetch all OntologyAPI details from the database
        api_details = [doc.to_dict() for doc in ontology_apis]
        
        return api_details, 200, default_headers

class OntologyAPI(Resource):
    def get(self, id):
        """
        Retrieve details for a single Ontology API based on ID.
        """
        # Fetch the specific OntologyAPI document from the database using the provided ID
        doc_ref = persistence().collection("OntologyAPI").document(id)
        doc = doc_ref.get()
        
        if doc.exists:
            return doc.to_dict(), 200, default_headers
        else:
            return {"error": "Ontology API not found"}, 404, default_headers