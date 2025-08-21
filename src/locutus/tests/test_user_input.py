import pytest

from locutus.model.terminology import Coding, CodingMapping, Terminology
from locutus.model.user_input import UserInput, MappingConversations, MappingVotes 
# from .test_terminology import sample_terminology, sample_terminology_with_editor

import pdb


@pytest.fixture
def sample_terminology(scope='class'):
    initial_codes = [
        Coding(code="C1", display="Code One", system="http://example.com/ont1", description="Description for C1"),
        Coding(code="C2", display="Code Two", system="http://example.com/ont1", description="Description for C2")
    ]

    t = Terminology(
        id="ontology-one",
        name="Ontology One",
        url="http://example.com/ont1",
        description="A sample oncology terminology",
        editor="unit tests",
        codes=initial_codes
    )
    t.save()
    coding_map = CodingMapping("MAPPED_CODE", "Mapped Display", "http://mapping.system", mapping_relationship="")
    coding_map2 = CodingMapping("MCODE", "Other Display", "http://mapping.system", mapping_relationship="")
    t.set_mapping("C1", [coding_map, coding_map2], "test_editor")


    yield t
    Terminology.delete("ontology-one")

def create_user_input(self, terminology_id, input_type, body_fragment, editor="unit-test1", code="C1", mapped_code="MAPPED_CODE"):
    body={
        "editor": editor
    }
    body.update(body_fragment)

    return UserInput.create_or_replace_user_input(
            self, 
            resource_type="Terminology",
            collection_type="user_input",
            id=terminology_id,
            code=code,
            mapped_code=mapped_code,
            type=input_type,       #"mapping_votes"
            body=body
        )

class TestMappingConversations:
    def get_input_class(self, type):
        """
        Returns the appropriate UserInput subclass for the given type.
        """
        if type == "mapping_conversations":
            return MappingConversations()
        elif type == "mapping_votes":
            return MappingVotes()
        else:
            raise ValueError("Invalid input type specified.")


    def test_convesation_basics(self, sample_terminology):

        # Now, let's discuss this mapping
        ui1 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            body_fragment={"note": "This is a test comment" }
        )

        assert ui1['mapped_code'] == "MAPPED_CODE"
        assert ui1['code'] == "C1"
        assert len(ui1['mapping_conversations']) == 1
        ui2 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            body_fragment={"note": "This is a test response" }
        )

        assert ui2['mapped_code'] == "MAPPED_CODE"
        assert ui2['code'] == "C1"
        assert len(ui2['mapping_conversations']) == 2

        ui3 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            body_fragment={"note": "This is another comment" }
        )

        assert ui3['mapped_code'] == "MAPPED_CODE"
        assert ui3['code'] == "C1"
        assert len(ui3['mapping_conversations']) == 3


        uitotal = UserInput.get_user_input(self, 
            resource_type="Terminology",
            collection_type="user_input",
            id=sample_terminology.id,
            code="C1",
            mapped_code="MAPPED_CODE",
            type="mapping_conversations",       #"mapping_votes"
        )
        assert len(uitotal['mapping_conversations']) == 3
        assert uitotal['mapped_code'] == "MAPPED_CODE"
        assert uitotal['code'] == "C1"

        UserInput.delete_user_conversations(self,
                resource_type="Terminology",
                collection_type="user_input",
                id=sample_terminology.id,
                code="C1",
                mapped_code="MAPPED_CODE")

        uitotal = UserInput.get_user_input(self, 
            resource_type="Terminology",
            collection_type="user_input",
            id=sample_terminology.id,
            code="C1",
            mapped_code="MAPPED_CODE",
            type="mapping_conversations",       #"mapping_votes"
        )
        assert "message" in uitotal 
        assert uitotal['message'] == 'No user input for this mapping.'


    def test_voting_basics(self, sample_terminology):
        # Now, let's discuss this mapping
        ui1 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_votes", 
            editor="unit-test1",
            body_fragment={"vote": "up"}
        )

        assert ui1['mapped_code'] == "MAPPED_CODE"
        assert ui1['code'] == "C1"
        assert len(ui1['mapping_votes']) == 1
        ui2 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_votes", 
            editor="unit-test2",
            body_fragment={"vote": "down" }
        )

        assert ui2['mapped_code'] == "MAPPED_CODE"
        assert ui2['code'] == "C1"
        assert len(ui2['mapping_votes']) == 2

        ui3 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_votes", 
            editor="unit-test1",
            body_fragment={"vote": "down" }
        )

        assert ui3['mapped_code'] == "MAPPED_CODE"
        assert ui3['code'] == "C1"
        assert len(ui3['mapping_votes']) == 2


        uitotal = UserInput.get_user_input(self, 
            resource_type="Terminology",
            collection_type="user_input",
            id=sample_terminology.id,
            code="C1",
            mapped_code="MAPPED_CODE",
            type="mapping_votes",       #"mapping_votes"
        )
        assert len(uitotal['mapping_votes']) == 2
        assert uitotal['mapped_code'] == "MAPPED_CODE"
        assert uitotal['code'] == "C1"

        UserInput.delete_user_votes(self,
                resource_type="Terminology",
                collection_type="user_input",
                id=sample_terminology.id,
                code="C1",
                mapped_code="MAPPED_CODE")

        uitotal = UserInput.get_user_input(self, 
            resource_type="Terminology",
            collection_type="user_input",
            id=sample_terminology.id,
            code="C1",
            mapped_code="MAPPED_CODE",
            type="mapping_votes",       #"mapping_votes"
        )
        assert "message" in uitotal 
        assert uitotal['message'] == 'No user input for this mapping.'

