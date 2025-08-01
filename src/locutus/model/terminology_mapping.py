from marshmallow import Schema, fields, post_load
from locutus import persistence, FTD_PLACEHOLDERS, normalize_ftd_placeholders
from enum import StrEnum  # Adds 3.11 requirement or 3.6+ with StrEnum library
from locutus.model.terminology import Terminology, Coding
from locutus.model.lookups import FTDConceptMapTerminology
from locutus.model.exceptions import *
from locutus.api.terminology_mapping import TerminologyMappings
from locutus.api import generate_mapping_index
from locutus.sessions import SessionManager

class MappingRelationshipModel:
    @classmethod
    def add_mapping_relationship(
        cls, editor, id, code, mapped_code, mapping_relationship
    ):

        # Validation of mapping_relationship
        ftd_terminology = FTDConceptMapTerminology()
        ftd_terminology.validate_codes_against(
            mapping_relationship, additional_enums=[""]
        )

        code_index = get_code_index(code)

        try:
            mappingref = (
                persistence()
                .collection("Terminology")
                .document(id)
                .collection("mappings")
                .document(code_index)
                .get()
            )

            if not mappingref.exists:
                raise ValueError(f"Mapping '{code_index}' does not exist in document '{id}'.")

            mapping_data = mappingref.to_dict()
            mappings = mapping_data.get("codes", [])

            # Find the entry for the mapped_code and update the mapping relationship
            updated = False

            # Ensure codes/mappings are not placeholders at this point.
            code = normalize_ftd_placeholders(code)
            mapped_code = normalize_ftd_placeholders(mapped_code)

            for entry in mappings:
                if entry.get("code") == mapped_code:
                    entry["mapping_relationship"] = mapping_relationship
                    updated = True
                    break

            if not updated:
                raise ValueError(
                    f"Mapping '{code}' | '{mapped_code}' not found in document '{id}'."
                )

            mappingref.reference.update({"codes": mappings})

            # Add provenance
            target = generate_mapping_index(code, mapped_code)
            term = Terminology(id)
            term.add_provenance(
                change_type=Terminology.ChangeType.EditMapping,
                editor=editor,
                target=target,
                new_value=mapping_relationship
            )

        except Exception as e:
            print(f"An error occurred while setting the mapping relationship: {str(e)}")
            raise

        response = TerminologyMappings.get_mappings(id)

        return response
