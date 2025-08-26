
# test_coding.py
import pytest
from locutus.model.coding import Coding, CodingMapping 
from locutus.model.user_input import MappingConversation, MappingVote
from locutus import get_code_index

import pdb

from rich import print

@pytest.fixture
def coding_one():
    c1 = Coding(terminology_id="Example-Terminology",
        code="code1",
        display="Code One",
        description="A Very Fine Description for the glorious term, 'code1'",
        system="http://example.com/example-terminology",
        rank=1 
    )
    c1.save()
    yield c1 
    c1.delete()

@pytest.fixture
def coding_two():
    c2 = Coding(terminology_id="Example-Terminology",
        code="code2",
        display="Code Two",
        description="A Very Fine Description for the glorious term, 'code2'",
        system="http://example.com/example-terminology",
        rank=2
    )
    c2.save()
    yield c2
    c2.delete()

class TestCoding:
    """
    Unit tests for the Coding class using PyTest.
    """

    def test_coding_initialization_required_fields(self):
        """Tests successful initialization with only required fields."""
        with pytest.raises(TypeError) as e:
            Coding(code="SNOMED", system="https://snomedct.org")

        with pytest.raises(ValueError, match="Term ID is required for all Codings.") as e:
            Coding(terminology_id="", code="SNOMED", system="https://snomedct.org")

        coding = Coding(terminology_id="term1", code="SNOMED", system="SNOMED CT")
        assert coding.id is None
        assert coding.code == "SNOMED"
        assert coding.system == "SNOMED CT"
        assert coding.display == ""
        assert coding.description == ""

    def test_coding_initialization_all_fields(self, coding_one):
        """Tests successful initialization with all fields."""
        
        assert coding_one.code == "code1"
        assert coding_one.display == "Code One"
        assert coding_one.system == "http://example.com/example-terminology"
        assert coding_one.description == "A Very Fine Description for the glorious term, 'code1'"
    
    def test_delete(self, coding_one):
        assert coding_one.valid == True 
        coding_one.delete(hard_delete=False)

        coding = Coding.get(terminology_id=coding_one.terminology_id, code=coding_one.code, valid_only=False)
        assert coding.valid == False 
        coding = Coding(terminology_id="term1", code="SNOMED", system="SNOMED CT")
        coding.save()

        c = Coding.get(code="SNOMED", system="SNOMED CT")
        assert c.code == coding.code 
        assert c.terminology_id == coding.terminology_id 
        coding.delete(hard_delete=True)

        c = Coding.get(code="SNOMED", system="SNOMED CT")
        assert c == [] 

    def test_get_order(self, coding_two, coding_one):
        c3 = Coding(terminology_id="Example-Terminology",
            code="code3",
            display="Code Three",
            description="number three",
            system="http://example.com/example-terminology",
            rank=0
        )
        c3.save()
        codes = Coding.get(system=coding_one.system)

        assert type(codes) is list
        # We should be able to get both of our codes back by querying the system and they
        # should be ordered by rank
        assert len(codes) == 3
        assert codes[0].code == c3.code
        assert codes[1].code == coding_one.code 
        assert codes[2].code == coding_two.code
     
        c3.delete()

    def test_basic_persistence(self, coding_one, coding_two):
        assert coding_one._id is not None
        assert coding_one._id == coding_one.id
        codes = Coding.get(system=coding_one.system)

        assert type(codes) is list
        # We should be able to get both of our codes back by querying the system
        assert len(codes) == 2 

        # We should be able to get both of our codes back by querying by the terminology ID
        codes = Coding.get(terminology_id=coding_one.terminology_id)
        print(codes)
        assert len(codes) == 2

        code = Coding.get(system=coding_one.system, code=coding_one.code)
        assert code.code == coding_one.code 
        assert code.system == coding_one.system 
        assert code.terminology_id == coding_one.terminology_id 
        assert code.description == coding_one.description

    def test_set_mappings(self, coding_one):
        mappings = [
            CodingMapping(code="MAP_C1_A", display="Map C1 A", system="http://map.com/A", mapping_relationship='equivalent'),
            CodingMapping(code="MAP_C1_B", display="Map C1 B", system="http://map.com/B", mapping_relationship='equivalent'),
        ]

        mapped_codes = coding_one.set_mappings(mappings)
        assert mapped_codes == ["MAP_C1_A", "MAP_C1_B"]
        coding_one.save()

        db_copy = Coding.get(
                terminology_id=coding_one.terminology_id,
                code=coding_one.code)
        assert len(db_copy.mappings) == 2

        assert db_copy.mappings[0].code == "MAP_C1_A" 
        assert db_copy.mappings[0].mapping_relationship == 'equivalent' 
        assert db_copy.mappings[1].code == "MAP_C1_B"
        assert db_copy.mappings[1].mapping_relationship == 'equivalent'

        # Test that setting it again overwrites the previous pair
        coding_one.set_mappings([mappings[1]])
        coding_one.save()
        db_copy = Coding.get(
                terminology_id=coding_one.terminology_id,
                code=coding_one.code)
        assert len(db_copy.mappings) == 1
        assert db_copy.mappings[0].code == "MAP_C1_B"
        assert db_copy.mappings[0].mapping_relationship == 'equivalent'

        # Test that we can delete the mapping
        mapped_codes = coding_one.delete_mappings()
        assert mapped_codes[0]['code'] == "MAP_C1_B"
        db_copy = Coding.get(
                terminology_id=coding_one.terminology_id,
                code=coding_one.code)
        assert len(db_copy.mappings) == 0


    def test_coding_with_dots(self):
        """Tests successful initialization with all fields."""

        coding = Coding(
            terminology_id="term1", 
            code="<FTD-DOT>",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "."

        coding = Coding(
            terminology_id="term1", 
            code="<FTD-DOT-DOT>",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == ".."

    def test_coding_search_with_problem_chars(self):
        c1 = Coding(
            terminology_id="term1",
            code=".",
            display="The Dot",
            system="Robot"
        )
        c1.save()

        c2 = Coding(
            terminology_id="term1",
            code="..",
            display="The Dots",
            system="Robot"
        )
        c2.save()

        c3 = Coding(
            terminology_id="term1",
            code=".term",
            display="The Dots",
            system="Robot"
        )
        c3.save()

        c4 = Coding(
            terminology_id="term1",
            code="..term",
            display="The Dots",
            system="Robot"
        )
        c4.save()

        c5 = Coding(
            terminology_id="term1",
            code="/",
            display="The Slash",
            system="Robot"
        )
        c5.save()

        c6 = Coding(
            terminology_id="term1",
            code="/slash",
            display="The Slash",
            system="Robot"
        )
        c6.save()

        c7 = Coding(
            terminology_id="term1",
            code="slash/",
            display="The Slash",
            system="Robot"
        )
        c7.save()

        c8 = Coding(
            terminology_id="term1",
            code="#",
            display="The Slash",
            system="Robot"
        )
        c8.save()

        c9 = Coding(
            terminology_id="term1",
            code="#hash",
            display="The Slash",
            system="Robot"
        )
        c9.save()

        c10 = Coding(
            terminology_id="term1",
            code="ha#sh",
            display="The Slash",
            system="Robot"
        )
        c10.save()

        c11 = Coding(
            terminology_id="term1",
            code="hash#",
            display="The Slash",
            system="Robot"
        )
        c11.save()
        c = Coding.get(terminology_id="term1", code=".")
        assert c is not None 
        assert c.code == "."

        c = Coding.get(terminology_id="term1", code="..")
        assert c is not None 
        assert c.code == ".."

        c = Coding.get(terminology_id="term1", code=".term")
        assert c is not None 
        assert c.code == ".term"

        c = Coding.get(terminology_id="term1", code="..term")
        assert c is not None 
        assert c.code == "..term"

        c = Coding.get(terminology_id="term1", code="/")
        assert c is not None 
        assert c.code == "/"

        c = Coding.get(terminology_id="term1", code="/slash")
        assert c is not None 
        assert c.code == "/slash"

        c = Coding.get(terminology_id="term1", code="slash/")
        assert c is not None 
        assert c.code == "slash/"

        c = Coding.get(terminology_id="term1", code="#")
        assert c is not None 
        assert c.code == "#"

        c = Coding.get(terminology_id="term1", code="#hash")
        assert c is not None 
        assert c.code == "#hash"

        c = Coding.get(terminology_id="term1", code="ha#sh")
        assert c is not None 
        assert c.code == "ha#sh"

        c = Coding.get(terminology_id="term1", code="hash#")
        assert c is not None 
        assert c.code == "hash#"

        codes = Coding.get(terminology_id="term1")
        assert len(codes) == 11
        for x in codes:
            x.delete()

    def test_code_index(self):
        # We no longer need to worry about these special encodings
        assert get_code_index(".") == "."    #"<FTD-DOT>"
        assert get_code_index(".something") == ".something"
        assert get_code_index("some.thing") == "some.thing"
        assert get_code_index("something.") == "something."
                
        assert get_code_index("..") == ".."  # "<FTD-DOT-DOT>"
        assert get_code_index("..something") == "..something"
        assert get_code_index("some..thing") == "some..thing"
        assert get_code_index("something..") == "something.."

        assert get_code_index("#") == "#"    # "<FTD-HASH>"
        assert get_code_index("#something") == "#something" #"<FTD-HASH>something"
        assert get_code_index("some#thing") == "some#thing" #"some<FTD-HASH>thing"
        assert get_code_index("something#") == "something#" #"something<FTD-HASH>"

    def test_coding_with_hashes(self):
        coding = Coding(
            terminology_id="term1", 
            code="<FTD-HASH>89",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "#89"
        coding = Coding(
            terminology_id="term1", 
            code="8<FTD-HASH>9",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "8#9"
        coding = Coding(
            terminology_id="term1", 
            code="89<FTD-HASH>",
            display="Fever",
            system="LOINC",
            description="Clinical finding of elevated body temperature"
        )
        assert coding.code == "89#"


    def test_coding_initialization_with_whitespace(self):
        """Tests initialization with whitespace in string fields."""
        coding = Coding(
            terminology_id="term1", 
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
        coding = Coding(terminology_id="term1", code="ICD10", system="ICD-10-CM")
        expected_dict = {
            "code": "ICD10",
            "display": "",
            "system": "ICD-10-CM"
        }
        assert coding.to_dict() == expected_dict

    def test_coding_to_dict_all_fields(self):
        """Tests to_dict method with all fields."""
        coding = Coding(
            terminology_id="term1", 
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
            Coding(terminology_id="term1", code="", system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(terminology_id="term1", code="   ", system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(terminology_id="term1", code=None, system="SystemX")
        with pytest.raises(ValueError, match="Code is a required string and cannot be empty."):
            Coding(terminology_id="term1", code=123, system="SystemX")

    def test_coding_missing_system_raises_error(self):
        """Tests that missing 'system' raises ValueError."""
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(terminology_id="term1", code="CodeY", system="")
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(terminology_id="term1", code="CodeY", system="   ")
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(terminology_id="term1", code="CodeY", system=None)
        with pytest.raises(ValueError, match="System is a required string and cannot be empty."):
            Coding(terminology_id="term1", code="CodeY", system=456)

    def test_coding_optional_fields_none(self):
        """Tests that optional fields correctly handle None values."""
        coding = Coding(terminology_id="term1", code="TestCode", system="TestSystem", display=None, description=None)
        assert coding.display is ""
        assert coding.description is ""
        assert coding.to_dict()["display"] is ""
        assert "description" not in coding.to_dict()

    def test_coding_optional_fields_empty_string(self):
        """Tests that optional fields handle empty string values (and strip them)."""
        coding = Coding(terminology_id="term1", code="TestCode", system="TestSystem", display="", description="  ")
        assert coding.display == ""
        assert coding.description == ""
        assert "description" not in coding.to_dict()
        assert coding.to_dict()["display"] == ""
