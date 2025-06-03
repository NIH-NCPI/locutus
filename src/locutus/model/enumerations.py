from locutus import persistence
from locutus.model.validation import validate_enums

from locutus import logger


class TerminologySingletonBase:
    """
    A base class implementing the Singleton pattern for managing terminology data.
    It fetches the data from the database upon the first instantiation and caches it for future use.

    Attributes:
        _instances (dict): A class-level dictionary that maps `terminology_name`
            to their respective singleton instances.
        db: A database client instance, initialized when the singleton is created.
        termref: A reference to the specific document in the `Terminology` collection.
        _terminology_data: Cached terminology data retrieved from the database.
    """

    _instances = {}

    def __new__(cls, terminology_name):
        """Ensure only one instance of each terminology is created."""
        cls._instances[terminology_name] = super(TerminologySingletonBase, cls).__new__(
            cls
        )
        instance = cls._instances[terminology_name]
        instance.db = persistence()
        instance.termref = (
            instance.db.collection("Terminology").document(terminology_name).get()
        )
        instance._terminology_data = instance.termref.to_dict()

        return cls._instances[terminology_name]

    def get_terminology(self):
        """Access the cached terminology document."""
        return self._terminology_data


class FTDConceptMapTerminology(TerminologySingletonBase):
    """Specifically handles the ftd-concept-map-relationship Terminology"""

    terminology_name = "ftd-concept-map-relationship"

    def __new__(cls):
        # Automatically pass the terminology_name to the base class
        return super(FTDConceptMapTerminology, cls).__new__(cls, cls.terminology_name)

    def get_terminology(self):
        """Access the FTD Concept Map terminology document."""
        terminology_data = super().get_terminology()
        return terminology_data

    def validate_codes_against(self, codes, additional_enums=None):
        """Validates the provided codes against the terminology."""
        terminology_data = self.get_terminology()
        terminology_codes = [
            entry["code"] for entry in terminology_data["codes"] if "code" in entry
        ]
        validate_enums(codes, terminology_codes, additional_enums=additional_enums)


class OntologyAPICollection(ResourceSingletonBase):
    """
    Manages the OntologyAPI collection as a singleton.

    This class handles the entire "OntologyAPI" collection, providing methods to
    access and filter its cached data for various operations.
    """

    resource_name = "OntologyAPI"

    def __new__(cls):
        """
        Creates or retrieves the singleton instance for the OntologyAPI collection.
        """
        return super(OntologyAPICollection, cls).__new__(
            cls, cls.resource_name, is_collection=True
        )

    def get_ontology_data(self, field):
        """Retrieve specific field data for each ontology object.
        cached data format [ontologies:{ado:{ado ontology data}}]
        """

        cached_data = self.get_cached_resource()
        ontology_data = {}

        for ontology_object in cached_data:
            ontologies = ontology_object.get("ontologies", {})

            for ontology_code, ontology_details in ontologies.items():

                # Check if the requested field exists in the details
                if field in ontology_details:
                    ontology_data[ontology_code.upper()] = ontology_details[field]

        logger.info(f"ontology data {ontology_data}")
        return ontology_data

    def get_ontology_keys(self):
        """ """
        cached_data = self.get_cached_resource()

        for ontology_object in cached_data:
            ontologies = ontology_object.get("ontologies", {})

            ontology_keys = ontologies.keys()

            ontology_keys_list = list(ontology_keys)

            return ontology_keys_list
