from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence


class Ontologies:
    """
    Represents an individual ontology with various attributes.

    Attributes:
        ontology_code (str): A unique code for the ontology.
        ontology_title (str): The title of the ontology.
        system (str): The system URL associated with the ontology.
        curie (str: optional): The CURIE (Compact URI) for the ontology.
        version (str: optional): The version of the ontology.
    """

    def __init__(self, ontology_code, ontology_title, system, curie="",  version=""):
        self.ontology_code = ontology_code
        self.ontology_title = ontology_title
        self.system = system
        self.curie = curie
        self.version = version

    class OntologiesSchema(Schema):
        """
        Marshmallow schema for serializing and deserializing Ontologies instances.
        """        
        ontology_code = fields.Str(
            required=True, error_messages={"required": "Ontologies *must* have a code "}
        )
        ontology_title = fields.Str(
            required=True, error_messages={"required": "Ontologies *must* have a title "}
        )
        system = fields.URL(
            required=True, error_messages={"required": "Ontologies *must* have a system "}
        )
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

            return Ontologies(**data)

class OntologyAPI(Serializable):
    """
    Represents an API providing access to various ontologies.

    Attributes:
        id (str): Unique identifier for the API.
        api_source (str): Source of the API.
        api_url (str): The URL endpoint for the API.
        ontologies (list): A list of Ontologies objects.
        resource_type (str): The resource type.
    """
    
    def __init__(
        self,
        id=None,
        api_source=None,
        api_url=None,
        ontologies=None,
        resource_type="OntologyAPI",

    ):
        super().__init__(id=id, collection_type="OntologyAPI", resource_type=resource_type)
        self.id = id
        self.api_source = api_source
        self.api_url = api_url
        self.ontologies = []

        if ontologies is not None:
            for ontology in ontologies:
                if type(ontology) is dict:
                    ontology = Ontologies(**ontology)
                ontology.system = self.api_url
                self.ontologies.append(ontology)

        # Generate an ID if not provided
        super().identify()

    @classmethod
    def get(cls, id, return_instance=True):
        """
        Retrieve an OntologyAPI instance from the database by ID.

        Args:
            id (str): The ID of the OntologyAPI to retrieve.
            TODO return_instance (bool, optional): Whether to return an
              instance of the class. Defaults to True.

        Returns:
            OntologyAPI or dict: An instance of OntologyAPI if return_instance
              is True, otherwise a dictionary.
        """
        resource = persistence().collection(cls.__name__).document(id).get().to_dict()

        # Just in case we just need the dict representation as it is found in
        # the database.
        if not return_instance:
            return resource

        return cls(**resource)
    
    def dump(self):
        """
        Serialize the OntologyAPI instance to a dictionary.

        Returns:
            dict: A dictionary representation of the OntologyAPI instance.
        """      
        return self.__class__._get_schema().dump(self)

    class OntologyApiSchema(Schema):
        """
        Marshmallow schema for serializing and deserializing OntologyAPI instances.
        """
        id = fields.Str()
        api_source = fields.Str(required=True)
        api_url = fields.Url(required=True)
        ontologies = fields.List(fields.Nested(Ontologies.OntologiesSchema))


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
    def _get_schema(cls):
        """
        Get the schema for the OntologyAPI class

        Returns:
            OntologyApiSchema: The schema for the OntologyAPI class.
        """
        if cls._schema is None:
            cls._schema = cls.OntologyApiSchema()
        return cls._schema
