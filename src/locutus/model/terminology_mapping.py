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

        # Mappings have been moved into the Coding:
        coding = Coding.get(terminology_id=id,
            code=code)
        
        try:
            coding.set_mapping_relationship(
                mapped_code=mapped_code, 
                mapping_relationship=mapping_relationship, 
                editor=editor)

        except Exception as e:
            print(f"An error occurred while setting the mapping relationship: {str(e)}")
            raise

        response = TerminologyMappings.get_mappings(id)

        return response
