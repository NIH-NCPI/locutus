from marshmallow import Schema, fields, post_load
from locutus import persistence
from enum import StrEnum  # Adds 3.11 requirement or 3.6+ with StrEnum library
from locutus.model.terminology import Terminology, Coding
from locutus.api.terminology_mapping import TerminologyMappings
from locutus.api import generate_paired_string
from sessions import SessionManager


class RelationshipCodes(StrEnum):
    @classmethod
    def get_mapping_relationship_terminology(cls):
        termref = (
            persistence()
            .collection("Terminology")
            .document("ftd-concept-map-relationship")
            .get()
        )
        return termref.to_dict()


class MappingRelationshipModel:
    @classmethod
    def add_mapping_relationship(
        cls, user_id, id, code, mapped_code, mapping_relationship
    ):
        try:
            # Validate mapping_relationship to be set. Should be Enums or ""
            relationship_dict = RelationshipCodes.get_mapping_relationship_terminology()
            relationship_codeings = relationship_dict.get("codes", [])
            relationship_codes = [entry.get("code") for entry in relationship_codeings]
            if mapping_relationship != "" and mapping_relationship not in relationship_codes:
                raise ValueError(
                    f"Invalid mapping relationship: {mapping_relationship}. Must be one of {relationship_codes}"
                )

            mappingref = (
                persistence()
                .collection("Terminology")
                .document(id)
                .collection("mappings")
                .document(code)
                .get()
            )

            if not mappingref.exists:
                raise ValueError(f"Mapping '{code}' does not exist in document '{id}'.")

            mapping_data = mappingref.to_dict()
            mappings = mapping_data.get("codes", [])

            # Find the entry for the mapped_code and update the mapping relationship
            updated = False
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
            target = generate_paired_string(code, mapped_code)
            term = Terminology(id)
            term.add_provenance(
                change_type=Terminology.ChangeType.EditMapping,
                editor=user_id,
                target=target,
                new_value=mapping_relationship,
            )

        except Exception as e:
            print(f"An error occurred while setting the mapping relationship: {str(e)}")
            raise

        response = TerminologyMappings.get_mappings(id)

        return response