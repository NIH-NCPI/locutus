from . import Serializable
from marshmallow import Schema, fields, post_load, ValidationError
from locutus import persistence
from locutus.api import default_headers

class Ontology:
    """
    Represents an individual ontology with various attributes.
    Attributes:
        ontology_code (str): A unique code for the ontology.
        ontology_title (str): The title of the ontology.
        system (str): The system URL associated with the ontology.
        curie (str): The CURIE (Compact URI) for the ontology.
        version (str): The version of the ontology.
    """

    def __init__(self, ontology_code, ontology_title, system, curie="",  version=""):
        self.ontology_code = ontology_code
        self.ontology_title = ontology_title
        self.system = system
        self.curie = curie
        self.version = version

    class OntologySchema(Schema):
        """
        Marshmallow schema for serializing and deserializing Ontologies instances.
        """        
        ontology_code = fields.Str()
        ontology_title = fields.Str()
        system = fields.Str()
        curie = fields.Str()
        version = fields.Str()

        @post_load
        def build_ontology(self, data, **kwargs):
            """
            Builds an Ontologies instance from deserialized data.
            Args:
                data (dict): The deserialized data.
            Returns:
                Ontologies: An instance of the Ontologies class.
            """

            return Ontology(**data)

class OntologyAPI(Serializable):
    """
    Represents an API providing access to various ontologies.
    Attributes:
        api_id (str): Unique identifier for the API.
        api_url (str): The URL endpoint for the API.
        ontologies (list): A list of Ontologies objects.
        resource_type (str): The resource type.
    """

    def __init__(
        self,
        api_id=None,
        api_url=None,
        ontologies=None,
        resource_type="OntologyAPI",
    ):
        super().__init__(id=api_id, collection_type="OntologyAPI", resource_type=resource_type)
        self.api_id = api_id
        self.api_url = api_url
        self.ontologies = []

        if ontologies is not None:
            for ontology in ontologies:
                if isinstance(ontology, dict):
                    ontology = Ontology(**ontology)
                ontology.system = self.api_url
                self.ontologies.append(ontology)

    def to_dict(self):
        """
        Convert the OntologyAPI instance to a dictionary.
        """
        return {
            "api_id": self.api_id,
            "api_url": self.api_url,
            "ontologies": [Ontology.OntologySchema().dump(ontology) for ontology in self.ontologies]
        }

    class OntologyApiSchema(Schema):
        """
        Marshmallow schema for serializing and deserializing OntologyAPI instances.
        """
        api_id = fields.Str()
        api_url = fields.Str()
        ontologies = fields.List(fields.Nested(Ontology.OntologySchema))

        @post_load
        def build_ontology_api(self, data, **kwargs):
            """
            Builds an OntologyAPI instance from deserialized data.
            Args:
                data (dict): The deserialized data.
            Returns:
                OntologyAPI: An instance of the OntologyAPI class.
            """
            return OntologyAPI(**data)

    @classmethod
    def _process_data(cls, data):
        """
        Process and validate the API data.
        """
        # Ensure the data['ontologies'] field is a list
        if 'ontologies' in data:
            if isinstance(data['ontologies'], dict):
                data['ontologies'] = list(data['ontologies'].values())
            elif not isinstance(data['ontologies'], list):
                data['ontologies'] = []

        # Use Marshmallow to load and validate data
        try:
            api_instance = cls.OntologyApiSchema().load(data)
            return api_instance.to_dict(), None
        except ValidationError as e:
            print("Validation error:", e.messages)
            return None, {"error": "Invalid data format"}

    @classmethod
    def get_all_api_ontologies(cls):
        """
        Retrieve details of all OntologyAPIs.
        """
        ontology_apis = persistence().collection("OntologyAPI").stream()
        all_apis = []

        for doc in ontology_apis:
            data = doc.to_dict()
            processed_data, error = cls._process_data(data)
            if processed_data:
                all_apis.append(processed_data)
            elif error:
                print(error)

        return all_apis

    @classmethod
    def get_ontologies_by_api_id(cls, api_id):
        """
        Retrieve details of a specific OntologyAPI by ID.
        """
        doc = persistence().collection("OntologyAPI").document(api_id).get()
        if not doc.exists:
            return {"error": "Ontology API not found"}, 404, default_headers

        data = doc.to_dict()
        processed_data, error = cls._process_data(data)
        if processed_data:
            return processed_data, 200, default_headers
        elif error:
            return error, 400, default_headers