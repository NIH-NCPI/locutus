from flask_restful import Resource
from locutus import persistence

from locutus.api import default_headers

class Ontologies(Resource):
    def get(self):
        """
        Retrieve all Ontology APIs.
        """
        return (
            [x.to_list() for x in persistence().collection("OntologyAPI").stream()],
            200,
            default_headers,
        )


class Ontology(Resource):
    def get(self, id):
        """
        Retrieve a single Ontology API by ID.
        """
        t = persistence().collection("OntologyAPI").document(id).get()
        return t.to_dict(), 200, default_headers