from locutus import persistence
from locutus.model.validation import validate_enums
from locutus import logger
import requests
from datetime import datetime, timedelta
from pathlib import Path
from search_dragon.support import ftd_ontology_lookup
import os
import csv


class ResourceSingletonBase:
    """
    A base class implementing the Singleton pattern for managing Collection and Terminology data.
    It fetches the data from the database upon the first instantiation and caches it for future use.

    Attributes:
        _instances (dict): A class-level dictionary that maps resource identifiers (name and type)
            to their respective singleton instances.
        db: A database client instance, initialized when the singleton is created.
        resource_ref: A reference to the specific document or collection in the database.
        _cached_resource: Cached data retrieved from the database, either as a dictionary (for documents)
            or a list of dictionaries (for collections).
    """

    _instances = {}

    def __new__(cls, resource_name, is_collection=False):
        """Ensure only one instance of each terminology or collection is created."""
        if (resource_name, is_collection) not in cls._instances:
            instance = super(ResourceSingletonBase, cls).__new__(cls)
            cls._instances[(resource_name, is_collection)] = instance
            instance.db = persistence()  # Initialize database client
            if is_collection:
                # Cache the entire collection
                instance.termref = instance.db.collection(resource_name).stream()
                instance._cached_resource = [doc.to_dict() for doc in instance.termref]
            else:
                # Cache a single document
                instance.termref = (
                    instance.db.collection("Terminology").document(resource_name).get()
                )
                instance._cached_resource = instance.termref.to_dict()
        return cls._instances[(resource_name, is_collection)]

    def get_cached_resource(self):
        """Access the cached terminology document."""
        return self._cached_resource


class FTDConceptMapTerminology(ResourceSingletonBase):
    """Specifically handles the ftd-concept-map-relationship Terminology"""

    resource_name = "ftd-concept-map-relationship"

    def __new__(cls):
        # Automatically pass the resource_name to the base class
        return super(FTDConceptMapTerminology, cls).__new__(cls, cls.resource_name)

    def get_cached_resource(self):
        """Access the FTD Concept Map terminology document."""
        terminology_data = super().get_cached_resource()
        return terminology_data

    def validate_codes_against(self, codes, additional_enums=None):
        """Validates the provided codes against the terminology."""
        terminology_data = self.get_cached_resource()
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

        logger.debug(f"ontology data {ontology_data}")
        return ontology_data

    def get_ontology_keys(self):
        """ """
        cached_data = self.get_cached_resource()

        for ontology_object in cached_data:
            ontologies = ontology_object.get("ontologies", {})

            ontology_keys = ontologies.keys()

            ontology_keys_list = list(ontology_keys)

            return ontology_keys_list


class FTDOntologyLookup:
    """
    This class handles fetching the CSV data from GitHub, saving it locally,
    and storing it in memory for later use in API calls.
    The CSV is fetched every time the app is redeployed and saved to a directory.
    """

    _csv_url = "https://raw.githubusercontent.com/NIH-NCPI/locutus_utilities/main/data/input/ontology_data/locutus_system_map.csv"
    _local_csv_path = "locutus/storage/data/references/ftd_ontology_lookup.csv"
    abs_path = Path(__file__).parent / "../storage/data/references/ftd_ontology_lookup.csv"
    _expiration_days = 90
    stored_ontology_lookup = {}
    reverse_lookup = {}

    @staticmethod
    def is_expired(filepath, expiration_days):
        """
        Check if the file is expired based on the modification date.
        """
        if not os.path.exists(filepath):
            return True
        file_mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        return datetime.now() - file_mtime > timedelta(days=expiration_days)

    @classmethod
    def load_data_to_memory(cls):
        """
        Load the data from the CSV file into memory.
        This is called after the CSV is fetched or if it exists locally.
    
        """
        if cls.stored_ontology_lookup: 
            return
        
        for curie, system in ftd_ontology_lookup().items():
            if curie and system:
                cls.stored_ontology_lookup[curie] = system
                # Reverse lookup: also allow system-to-curie if needed
                if system not in cls.reverse_lookup:
                    cls.reverse_lookup[system] = curie

            logger.debug("Ontology data loaded into memory.")
        else:
            logger.error("No CSV file found, unable to load data into memory.")

    @classmethod
    def fetch_and_store_csv(cls):
        """
        Fetch the CSV from GitHub if expired or missing, then store it locally and load into memory.

        EST 2025-07-30 - I've moved the this into the search dragon library. 
        """
        
        # Now load the data into memory after the file is fetched or if it exists
        cls.load_data_to_memory()

    @classmethod
    def get_mapped_system(cls, ori_system):
        """
        Get the system URL given a CURIE (e.g., 'LNC' → 'http://loinc.org').
        """
        ftd_ontology_lookup_path = cls.abs_path
        with open(ftd_ontology_lookup_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get("curie") == ori_system:
                    return row.get("system")
        return ori_system

    @classmethod
    def get_mapped_curie(cls, system_url):
        """
        Get the CURIE given a system URL (e.g., 'http://loinc.org' → 'LNC').
        """
        ftd_ontology_lookup_path = cls.abs_path
        
        with open(ftd_ontology_lookup_path, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get("system") == system_url:
                    return row.get("curie")
        
        return system_url
