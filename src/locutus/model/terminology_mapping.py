from locutus import get_code_index
from locutus.api.terminology_mapping import TerminologyMappings
from locutus.model.lookups import FTDConceptMapTerminology
from locutus.model.terminology import Coding


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

        get_code_index(code)

        # Mappings have been moved into the Coding:
        coding = Coding.get(terminology_id=id, code=code)
        assert isinstance(coding, Coding)

        try:
            coding.set_mapping_relationship(
                mapped_code=mapped_code,
                mapping_relationship=mapping_relationship,
                editor=editor,
            )

        except Exception as e:
            print(f"An error occurred while setting the mapping relationship: {e!s}")
            raise

        response = TerminologyMappings.get_mappings(id)

        return response
