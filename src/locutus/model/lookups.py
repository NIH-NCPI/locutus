import logging
from datetime import UTC, datetime, timedelta
from typing import Any, ClassVar

from term_wyrm import default_vocabularies

import locutus
import locutus.model.terminology
from locutus.model.validation import validate_enums

logger = logging.getLogger(__name__)


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

    _instances: ClassVar[dict] = {}

    # How long a cached read is trusted before the next access re-fetches it.
    # Keeps the common case (many reads, e.g. one per search request) cheap
    # while bounding how long an admin-side DB edit can stay invisible to a
    # running server -- see issues/021.
    _cache_ttl: ClassVar[timedelta] = timedelta(minutes=5)

    # Set in __new__ only (this class deliberately has no __init__, since
    # cached singleton instances shouldn't be re-initialized on every "call").
    db: Any
    termref: Any
    _cached_resource: Any
    _cached_at: datetime

    def __new__(cls, resource_name, is_collection=False):
        """Ensure only one instance of each terminology or collection is created,
        refreshing its cached data once _cache_ttl has elapsed since the last fetch.
        """
        key = (resource_name, is_collection)
        instance = cls._instances.get(key)
        stale = instance is None or (
            datetime.now(UTC) - instance._cached_at > cls._cache_ttl
        )

        if stale:
            if instance is None:
                instance = super().__new__(cls)
                cls._instances[key] = instance
                instance.db = locutus.persistence()  # Initialize database client

            if is_collection:
                # Cache the entire collection
                instance.termref = instance.db.collection(resource_name).stream()
                instance._cached_resource = [doc.to_dict() for doc in instance.termref]
            else:
                # Cache a single document
                instance._cached_resource = locutus.model.terminology.Terminology.get(
                    resource_name, return_instance=True
                )

                if instance._cached_resource is not None:
                    instance._cached_resource = (
                        instance._cached_resource.realize_as_dict()
                    )

            instance._cached_at = datetime.now(UTC)

        return cls._instances[key]

    def get_cached_resource(self):
        """Access the cached terminology document."""
        return self._cached_resource


class FTDConceptMapTerminology(ResourceSingletonBase):
    """Specifically handles the ftd-concept-map-relationship Terminology"""

    resource_name = "ftd-concept-map-relationship"

    def __new__(cls):
        # Automatically pass the resource_name to the base class
        return super().__new__(cls, cls.resource_name)

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
        return super().__new__(cls, cls.resource_name, is_collection=True)

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
        cached_data = self.get_cached_resource()

        for ontology_object in cached_data:
            ontologies = ontology_object.get("ontologies", {})

            ontology_keys = ontologies.keys()

            ontology_keys_list = list(ontology_keys)

            return ontology_keys_list


class FTDOntologyLookup:
    """Prefix <-> system lookups, backed by term-wyrm's vocabularies.

    System matching ignores http/https and trailing slashes; returned
    prefixes and systems are the preferred ones.
    """

    @classmethod
    def fetch_and_store_csv(cls):
        """Load the vocabularies at startup rather than on the first request."""
        default_vocabularies()

    @classmethod
    def get_mapped_system(cls, ori_system):
        """
        Get the system URL given a CURIE prefix (e.g., 'LNC' → 'http://loinc.org').
        """
        voc = default_vocabularies().resolve(ori_system)
        return voc.system if voc else ori_system

    @classmethod
    def get_mapped_curie(cls, system_url):
        """
        Get the preferred CURIE prefix given a system URL
        (e.g., 'http://loinc.org' → 'loinc').
        """
        voc = default_vocabularies().by_system(system_url) if system_url else None
        return voc.prefix if voc else ""
