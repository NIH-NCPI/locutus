from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence
from search_dragon.search import run_search
from locutus.model.lookups import OntologyAPICollection
from locutus.model.exceptions import InvalidValueError

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

    def __init__(self, ontology_code, ontology_title, system, curie="", version=""):
        self.ontology_code = ontology_code
        self.ontology_title = ontology_title
        self.system = system
        self.curie = curie
        self.version = version

    class _Schema(Schema):
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
            Builds an Ontology instance from deserialized data.
            Args:
                data (dict): The deserialized data.
            Returns:
                Ontology: An instance of the Ontology class.
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
        api_name=None,
        resource_type="OntologyAPI",
    ):
        super().__init__(id=api_id, collection_type="OntologyAPI", resource_type=resource_type)
        self.api_id = api_id
        self.api_url = api_url
        self.api_name = api_name
        self.ontologies = []

    class _Schema(Schema):
        """
        Marshmallow schema for serializing and deserializing OntologyAPI instances.
        """
        api_id = fields.Str()
        api_url = fields.Str()
        api_name = fields.Str()
        ontologies = fields.List(fields.Nested(Ontology._Schema))

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
    def get_api_ontologies(cls, api_id=None):
        """
        Retrieve details of all OntologyAPIs or a specific OntologyAPI by ID.
        Args:
            api_id (str): Unique identifier for a specific API. If None, 
            returns all APIs.
        Returns:
            processed_data: A list with a specific API if `api_id` is provided, 
            or a list of dictionaries representing each API if `api_id` is None.
        """
        if api_id:
            processed_data = cls.get(api_id, return_instance=False)
            if processed_data is None:
                return None
            return [processed_data]
        else:
            processed_data = [x.to_dict() for x in persistence().collection("OntologyAPI").stream()]
            return processed_data
        
class OntologyAPISearchModel():

    def run_search_dragon(keywords, ontologies, apis, results_per_page, start_index):
        onto_seed_data = OntologyAPICollection()
        onto_data = onto_seed_data.get_ontology_data("system")

        # Validate ontologies(FE provided) against expected ontologies(firestore)
        onto_curies = onto_seed_data.get_ontology_data("curie")
        valid_curies = onto_curies.values()
        for onto in ontologies:
            if onto not in valid_curies:
                raise InvalidValueError(value=f"{onto}",valid_values=valid_curies)

        search_result = run_search(onto_data, keywords, ontologies, apis, results_per_page, start_index)
        return search_result