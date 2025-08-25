import pytest

from locutus.model.coding import Coding, CodingMapping 
from locutus.model.terminology import Terminology
from locutus.model.user_input import UserInput, MappingConversation, MappingVote
# from .test_terminology import sample_terminology, sample_terminology_with_editor

import pdb


@pytest.fixture
def sample_terminology(scope='class'):
    initial_codes = [
        Coding(terminology_id="ontology-one", code="C1", display="Code One", system="http://example.com/ont1", description="Description for C1"),
        Coding(terminology_id="ontology-one", code="C2", display="Code Two", system="http://example.com/ont1", description="Description for C2")
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
    t.delete(hard_delete=True)

    

def create_user_input(self, terminology_id, input_type, input_value, editor="unit-test1", code="C1", mapped_code="MAPPED_CODE"):
    return UserInput.create_or_replace_user_input(
            resource_type="Terminology",
            collection_type="user_input",
            id=terminology_id,
            code=code,
            mapped_code=mapped_code,
            type=input_type,       #"mapping_votes"
            input_value=input_value,
            editor=editor
        )

class TestMappingConversations:
    def get_input_class(self, type):
        """
        Returns the appropriate UserInput subclass for the given type.
        """
        if type == "mapping_conversations":
            return MappingConversation()
        elif type == "mapping_votes":
            return MappingVote()
        else:
            raise ValueError("Invalid input type specified.")

    def test_duplicate_votes(self, sample_terminology):
        mv1 = MappingVote(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        mv1.save()

        mv2 = MappingVote(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        mv2.save()
        assert mv1.id == mv2.id
        mv1.delete(hard_delete=True)

    def test_duplicate_conversations(self, sample_terminology):
        mc1 = MappingConversation(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        mc1.save()

        mc2 = MappingConversation(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        mc2.save()
        assert mc1.id == mc2.id
        mc2.delete(hard_delete=True)

    def test_simple_votes(self, sample_terminology):
        mv = MappingVote(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        assert mv.mapping_votes == {}
        mv.add_input("down", "user1")
        mv.add_input("up", "user2")
        assert len(mv.mapping_votes) == 2
        mv.add_input("up", "user1")
        assert len(mv.mapping_votes) == 2

        mv.save()
        mvv = MappingVote.get(terminology_id=sample_terminology.id,
                                    source_code="C1", 
                                    mapped_code="MAPPED_CODE",
                                    return_instance=False)
        assert mvv['mapping_votes'] == mv.dump()['mapping_votes']
        mvv = MappingVote.get(terminology_id=sample_terminology.id,
                                    source_code="C1", 
                                    mapped_code="MAPPED_CODE",
                                    return_instance=True)
        assert mvv.terminology_id==mv.terminology_id 
        assert len(mvv.mapping_votes) == 2
        assert mvv.to_dict() == mv.to_dict()
        mv.delete(hard_delete=True)

    def test_simple_conversations(self, sample_terminology):
        mc = MappingConversation(
            terminology_id=sample_terminology.id,
            source_code="C1",
            mapped_code="MAPPED_CODE"
        )
        assert mc.mapping_conversations == []
        mc.add_input("This is an initial comment", editor="user1")
        mc.add_input("this is a reply", editor="user2")
        mc.add_input("And another comment in response to the reply", editor="user1")
        assert len(mc.mapping_conversations) == 3

        mc.save()

        mcc = MappingConversation.get(terminology_id=sample_terminology.id,
                                    source_code="C1", 
                                    mapped_code="MAPPED_CODE",
                                    return_instance=True)
        assert mcc.id == mc.id

        # Make sure it's an instance and not already a dict
        assert mcc.terminology_id == mc.terminology_id
        assert len(mcc.mapping_conversations) == 3
        assert mcc.to_dict() == mc.to_dict()

        mcc.delete(hard_delete=True)

    def test_conversation_basics(self, sample_terminology):
        # Now, let's discuss this mapping

        ui1 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            input_value="This is a test comment"
        )
        assert ui1['mapped_code'] == "MAPPED_CODE"
        assert ui1['code'] == "C1"
        assert len(ui1['mapping_conversations']) == 1
        ui2 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            input_value="This is a test response"
        )

        assert ui2['mapped_code'] == "MAPPED_CODE"
        assert ui2['code'] == "C1"
        assert len(ui2['mapping_conversations']) == 2

        ui3 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_conversations", 
            input_value="This is another comment"
        )

        assert ui3['mapped_code'] == "MAPPED_CODE"
        assert ui3['code'] == "C1"
        assert len(ui3['mapping_conversations']) == 3


        uitotal = UserInput.get_user_input( 
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

        UserInput.delete_user_conversations(
                resource_type="Terminology",
                collection_type="user_input",
                id=sample_terminology.id,
                code="C1",
                mapped_code="MAPPED_CODE",
                hard_delete=True)

        uitotal = UserInput.get_user_input( 
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
            input_value="up"
        )
        assert ui1['mapped_code'] == "MAPPED_CODE"
        assert ui1['code'] == "C1"
        assert len(ui1['mapping_votes']) == 1
        ui2 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_votes", 
            editor="unit-test2",
            input_value="down"
        )

        assert ui2['mapped_code'] == "MAPPED_CODE"
        assert ui2['code'] == "C1"
        assert ui2['source_code'] == "C1"
        assert len(ui2['mapping_votes']) == 2

        ui3 = create_user_input(self, 
            sample_terminology.id, 
            input_type="mapping_votes", 
            editor="unit-test1",
            input_value="down"
        )

        assert ui3['mapped_code'] == "MAPPED_CODE"
        assert ui3['code'] == "C1"
        assert len(ui3['mapping_votes']) == 2

        uitotal = UserInput.get_user_input( 
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

        UserInput.delete_user_votes(
                resource_type="Terminology",
                collection_type="user_input",
                id=sample_terminology.id,
                code="C1",
                mapped_code="MAPPED_CODE",
                hard_delete=True)

        uitotal = UserInput.get_user_input( 
            resource_type="Terminology",
            collection_type="user_input",
            id=sample_terminology.id,
            code="C1",
            mapped_code="MAPPED_CODE",
            type="mapping_votes",       #"mapping_votes"
        )
        assert "message" in uitotal 
        assert uitotal['message'] == 'No user input for this mapping.'

