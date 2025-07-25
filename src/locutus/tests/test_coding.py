
# test_coding.py
import pytest
from locutus.model.terminology import Coding 


import pdb


class TestCoding:
    """
    Unit tests for the Coding class using PyTest.
    """

    def test_coding_initialization_required_fields(self):
        """Tests successful initialization with only required fields."""
        coding = Coding(code="SNOMED", system="SNOMED CT")
        assert coding.code == "SNOMED"
        assert coding.system == "SNOMED CT"
        assert coding.display == ""
        assert coding.description == ""

    def test_coding_initialization_all_fields(self):
        """Tests successful initialization with all fields."""
        coding = Coding(
            code="12345",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "12345"
        assert coding.display == "Fever"
        assert coding.system == "LOINC"
        assert coding.description == "Clinical finding of elevated body temperature"

    def test_coding_with_dots(self):
        """Tests successful initialization with all fields."""

        coding = Coding(
            code="<FTD-DOT>",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "."

        coding = Coding(
            code="<FTD-DOT-DOT>",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == ".."

        

    def test_coding_initialization_with_whitespace(self):
        """Tests initialization with whitespace in string fields."""
        coding = Coding(
            code="  CODE123  ",
            display="  Display Text  ",
            system="  SYSTEM_A  ",
            description="  Some description.  "
        )
        assert coding.code == "CODE123"
        assert coding.display == "Display Text"
        assert coding.system == "SYSTEM_A"
        assert coding.description == "Some description."

    def test_coding_to_dict_required_fields(self):
        """Tests to_dict method with only required fields."""
        coding = Coding(code="ICD10", system="ICD-10-CM")
        expected_dict = {
            "code": "ICD10",
            "display": "",
            "system": "ICD-10-CM"
        }
        assert coding.to_dict() == expected_dict

    def test_coding_to_dict_all_fields(self):
        """Tests to_dict method with all fields."""
        coding = Coding(
            code="456",
            display="Headache",
            system="RxNorm",
            description="Pain in the head"
        )
        expected_dict = {
            "code": "456",
            "display": "Headache",
            "system": "RxNorm",
            "description": "Pain in the head"
        }
        assert coding.to_dict() == expected_dict

    def test_coding_missing_code_raises_error(self):
        """Tests that missing 'code' raises ValueError."""
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(code="", system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(code="   ", system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(code=None, system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(code=123, system="SystemX")

    def test_coding_missing_system_raises_error(self):
        """Tests that missing 'system' raises ValueError."""
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(code="CodeY", system="")
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(code="CodeY", system="   ")
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(code="CodeY", system=None)
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(code="CodeY", system=456)

    def test_coding_optional_fields_none(self):
        """Tests that optional fields correctly handle None values."""
        coding = Coding(code="TestCode", system="TestSystem", display=None, description=None)
        assert coding.display is None
        assert coding.description is None
        assert coding.to_dict()["display"] is None
        assert coding.to_dict()["description"] is None

    def test_coding_optional_fields_empty_string(self):
        """Tests that optional fields handle empty string values (and strip them)."""
        coding = Coding(code="TestCode", system="TestSystem", display="", description="  ")
        assert coding.display == ""
        assert coding.description == ""
        assert "description" not in coding.to_dict()
        assert coding.to_dict()["display"] == ""
