from locutus import persistence
from locutus.model.validation import validate_enums


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
