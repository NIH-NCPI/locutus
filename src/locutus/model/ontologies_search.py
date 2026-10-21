from marshmallow import Schema, fields, post_load
from term_wyrm import SearchService
from term_wyrm.apis import available_apis

from locutus.model.exceptions import APIError, InvalidValueError
from locutus.model.lookups import OntologyAPICollection

from . import Serializable


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
        super().__init__(
            id=api_id, collection_type="OntologyAPI", resource_type=resource_type
        )
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
            processed_data = cls.find(params={"api_id": api_id}, return_instance=False)
            if processed_data is None:
                return None
            return processed_data
        else:
            processed_data = cls.get(return_instance=False)
            return processed_data


class OntologyAPISearchModel:
    @staticmethod
    def run_search(keywords, ontologies, apis, results_per_page, start_index):
        """Search ``apis`` for ``keywords`` within ``ontologies``.

        ``start_index`` is a 0-based page number. Raises ValueError for bad
        paging values, InvalidValueError for unknown ontologies or APIs, and
        APIError (502) when every API failed.
        """
        onto_seed_data = OntologyAPICollection()

        # Validate ontologies(FE provided) against expected ontologies(firestore)
        onto_curies = onto_seed_data.get_ontology_data("curie")
        valid_curies = {curie.upper() for curie in onto_curies.values()}
        for onto in ontologies:
            if onto.upper() not in valid_curies:
                raise InvalidValueError(
                    value=f"{onto}", valid_values=onto_curies.values()
                )

        page_size = int(results_per_page)
        page = int(start_index)
        if page < 0:
            raise ValueError(f"start_index must be >= 0, not {page}")

        try:
            service = SearchService(apis)
        except (KeyError, TypeError) as e:
            raise InvalidValueError(
                value=f"{apis}", valid_values=sorted(available_apis())
            ) from e
        try:
            result = service.search(
                keywords, ontologies, page_size=page_size, offset=page * page_size
            )
        except KeyError as e:
            # Listed in the OntologyAPI collection but unknown to term-wyrm.
            raise InvalidValueError(
                value=f"{ontologies}", valid_values=onto_curies.values()
            ) from e

        if result.failures and not result.pages:
            raise APIError(
                "No ontology API could answer: "
                + "; ".join(f"{f.source}: {f.error}" for f in result.failures),
                status_code=502,
            )

        response = result.to_dict()
        # search-dragon reported a single URL; keep it for the front end.
        response["search_query"] = next(
            reversed(response["search_queries"].values()), ""
        )
        return response
