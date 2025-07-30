import pytest
import json
from locutus.model.terminology import Terminology, Coding, CodingMapping
from locutus.model.exceptions import InvalidValueError

# import pdb
from rich import print

@pytest.fixture
def sample_terminology():
    initial_codes = [
        Coding(code="C1", display="Code One", system="http://example.com/ont1", description="Description for C1"),
        Coding(code="C2", display="Code Two", system="http://example.com/ont1", description="Description for C2")
    ]

    t = Terminology(
        id="ontology-one",
        name="Ontology One",
        url="http://example.com/ont1",
        description="A sample oncology terminology",
        codes=initial_codes
    )
    t.save()
    yield t
    Terminology.delete("ontology-one")

@pytest.fixture
def sample_terminology_with_editor():
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
    yield t
    Terminology.delete("ontology-one")


def test_terminology_get(sample_terminology):
    all_terms = Terminology.get(return_instance=False)
    assert len(all_terms) > 1

    one_term = Terminology.get(all_terms[0]['id'])
    assert one_term.id == all_terms[0]['id']

    one_term = Terminology.get(all_terms[0]['id'], return_instance=False)
    assert type(one_term) is dict 
    assert one_term['id'] == all_terms[0]['id']


def test_terminology_id(sample_terminology):
    # Normally we want these to have unique IDs, but for this we should just reuse the same one
    assert sample_terminology.id == "ontology-one"
    
    term = Terminology(
        name="Ontology One",
        url="http://example.com/ont1",
        description="A sample oncology terminology"
    )

    assert term.id[0:3] == "tm-"
    Terminology.delete(term.id)

def test_terminology_init(sample_terminology):
    assert sample_terminology.name == "Ontology One"
    assert sample_terminology.url == "http://example.com/ont1"
    assert sample_terminology.description == "A sample oncology terminology"
    assert len(sample_terminology.codes) == 2
    assert sample_terminology.codes[0].code == "C1"

def test_terminology_prov_on_init(sample_terminology_with_editor):
    assert len(sample_terminology_with_editor.get_provenance()) == 1
    prov = sample_terminology_with_editor.get_provenance("self")["self"]
    assert prov['target'] == "self"

    p1 = prov['changes'][0]
    assert p1['action'] == "Create Terminology"
    assert p1['editor'] == "unit tests"
    assert p1['target'] == "self"
    assert "timestamp" in p1 
    
    # We started with 2 codes in it, so the provenance should include those two
    p2 = prov['changes'][1]
    assert p2['action'] == "Add Term"
    assert p2['new_value'] == "C1"

    p3 = prov['changes'][2]
    assert p3['action'] == "Add Term"
    assert p3['new_value'] == "C2"


def test_build_code_dict(sample_terminology):
    code_dict = sample_terminology.build_code_dict()

    assert isinstance(code_dict, dict)
    assert len(code_dict) == 2
    assert "C1" in code_dict
    assert code_dict["C1"].code == "C1"
    assert code_dict["C1"].display == "Code One"
    assert code_dict["C1"].system == "http://example.com/ont1"
    assert code_dict["C2"].code == "C2"

def test_add_code(sample_terminology):
    sample_terminology.add_code(code="C3", display="Code Three", description="Description for C3", editor="unit-test")
    assert len(sample_terminology.codes) == 3
    assert sample_terminology.has_code("C3")
    new_code = next(c for c in sample_terminology.codes if c.code == "C3")
    assert new_code.display == "Code Three"
    assert new_code.system == "http://example.com/ont1"
    assert new_code.description == "Description for C3"

    # Verify that the addition was reflected in prov
    prov = sample_terminology.get_provenance("self")["self"]['changes'][-1]
    assert prov['action'] == "Add Term"
    assert prov['new_value'] == "C3"

def test_remove_code(sample_terminology):
    sample_terminology.remove_code("C1", editor="unit-test")
    assert len(sample_terminology.codes) == 1
    assert not sample_terminology.has_code("C1")
    assert sample_terminology.has_code("C2")

    # Verify that the removal was reflected in prov
    prov = sample_terminology.get_provenance("self")["self"]['changes'][-1]
    assert prov['action'] == "Remove Term"
    assert prov['new_value'] == "C1"
 
    # Test removing a non-existent code
    with pytest.raises(KeyError) as e_info:
        sample_terminology.remove_code("C99", editor="unit-test")
    assert len(sample_terminology.codes) == 1

def test_rename_code(sample_terminology):
    sample_terminology.rename_code("C1", new_code="C1_NEW", new_display="New Code One Display", editor="unit-test")
    assert sample_terminology.has_code("C1_NEW")
    assert not sample_terminology.has_code("C1")
    renamed_code = next(c for c in sample_terminology.codes if c.code == "C1_NEW")
    assert renamed_code.display == "New Code One Display"
    assert renamed_code.description == "Description for C1" # Description should remain unchanged



    sample_terminology.rename_code("C2", new_code="C2", new_display="C2 New Display", new_description="Updated description for C2", editor="unit-test")
    updated_code = next(c for c in sample_terminology.codes if c.code == "C2")
    assert updated_code.display == "C2 New Display"
    assert updated_code.description == "Updated description for C2"
    # Verify that the chnge was reflected in prov
    prov = sample_terminology.get_provenance("self")["self"]['changes'][-1]
    assert prov['action'] == "Edit Term"
    assert prov['old_value'] == "display: Code Two,description: Description for C2"
    assert prov['new_value'] == "display: C2 New Display,description: Updated description for C2"

def test_rename_code_provenance_code_and_display(sample_terminology):
    sample_terminology.rename_code("C1", new_code="C1_NEW", new_display="New Code One Display", editor="unit-test")

    # Verify that the chnge was reflected in prov for the terminology
    prov = sample_terminology.get_provenance("self")["self"]['changes'][-1]
    assert prov['action'] == "Edit Term"
    assert prov['old_value'] == "code: C1,display: Code One"
    assert prov['new_value'] == "code: C1_NEW,display: New Code One Display"

    # Verify that the the old code's prov is gone (should be under the new code now)
    assert sample_terminology.get_provenance("C1")['C1'] == []

    # Verify that the chnge was reflected in prov for the code's new name
    print(sample_terminology.get_provenance("C1_NEW"))
    prov = sample_terminology.get_provenance("C1_NEW")['C1_NEW']['changes'][-1]
    assert prov['action'] == "Edit Term"
    assert prov['old_value'] == "code: C1,display: Code One"
    assert prov['new_value'] == "code: C1_NEW,display: New Code One Display"

def test_rename_code_provenance_description_only(sample_terminology):
    sample_terminology.rename_code("C1", new_code="C1", new_display=None, new_description="Updated description for C1", editor='unit-test')
    prov = sample_terminology.get_provenance("C1")['C1']['changes']
    assert len(prov) == 1
    assert prov[0]['action'] == 'Edit Term'
    assert prov[0]['old_value'] == "description: Description for C1"
    assert prov[0]['new_value'] == "description: Updated description for C1"

def test_rename_code_provenance_display_only(sample_terminology):
    sample_terminology.rename_code("C1", new_code="C1", new_display="Updated Display", editor='unit-test')
    prov = sample_terminology.get_provenance("C1")['C1']['changes']
    assert len(prov) == 1
    assert prov[0]['action'] == 'Edit Term'
    assert prov[0]['old_value'] == "display: Code One"
    assert prov[0]['new_value'] == "display: Updated Display"

def test_rename_code_provenance_code_only(sample_terminology):
    # First, we'll update the display so that the provenance is longer than 1 entry
    sample_terminology.rename_code("C1", new_code="C1", new_display="Updated Display", editor='unit-test')
    assert len(sample_terminology.get_provenance("C1")['C1']['changes']) == 1

    # Test only changing the code
    sample_terminology.rename_code("C1", new_code="C1_NEW", new_display=None, editor="unit-test")
    # Verify that the chnge was reflected in prov for the terminology
    prov = sample_terminology.get_provenance("self")["self"]['changes'][-1]
    assert prov['action'] == "Edit Term"
    assert prov['old_value'] == "code: C1"
    assert prov['new_value'] == "code: C1_NEW"

    # Verify that the the old code's prov is gone (should be under the new code now)
    assert sample_terminology.get_provenance("C1")['C1'] == [] 
    
    # Verify that the chnge was reflected in prov for the code's new name
    prov = sample_terminology.get_provenance("C1_NEW")['C1_NEW']['changes']
    assert len(prov) == 2
    assert prov[0]['action'] == "Edit Term"
    assert prov[0]['old_value'] == "display: Code One"
    assert prov[0]['new_value'] == "display: Updated Display"
    assert prov[1]['action'] == "Edit Term"
    assert prov[1]['old_value'] == "code: C1"
    assert prov[1]['new_value'] == "code: C1_NEW"

def test_has_code(sample_terminology):
    assert sample_terminology.has_code("C1")
    assert sample_terminology.has_code("C2")
    assert not sample_terminology.has_code("C99")


def test_set_mapping(sample_terminology):
    # Initially, no mappings
    mappings = [mp for mp in sample_terminology.mappings("C1")["C1"] if mp.valid]
    assert len(mappings) == 0

    # Set a mapping
    coding_map = CodingMapping("MAPPED_CODE", "Mapped Display", "http://mapping.system", mapping_relationship="")
    sample_terminology.set_mapping("C1", [coding_map], "test_editor")

    retrieved_mappings = sample_terminology.mappings("C1")["C1"]
    assert len(retrieved_mappings) == 1
    assert retrieved_mappings[0].code == "MAPPED_CODE"
    assert retrieved_mappings[0].display == "Mapped Display"
    assert retrieved_mappings[0].system == "http://mapping.system"

    # Set another mapping for the same code by a different editor
    coding_map_2 = CodingMapping("MAPPED_CODE_2", "Mapped Display 2", "http://mapping.system", mapping_relationship="")
    sample_terminology.set_mapping("C1", [coding_map, coding_map_2], "another_editor")
    
    retrieved_mappings = [mp for mp in sample_terminology.mappings("C1")["C1"] if mp.valid]
    assert len(retrieved_mappings) == 2 # Should now have mappings from both editors

def test_set_mapping_provenance(sample_terminology):
    # Set a mapping
    coding_map = CodingMapping("MAPPED_CODE", "Mapped Display", "http://mapping.system", mapping_relationship="")
    sample_terminology.set_mapping("C1", [coding_map], "unit-test")

    # Verify that the chnge was reflected in prov for the terminology
    prov = sample_terminology.get_provenance("C1")["C1"]['changes']
    assert len(prov) == 1
    assert prov[0]['action'] == "Add Mapping"
    assert prov[0]['old_value'] == ""
    assert prov[0]['new_value'] == "MAPPED_CODE"

    sample_terminology.set_mapping("C1", [CodingMapping("NEW_CODE", "New Mapped Display", "http://mapping.system", mapping_relationship="equivalent")], "unit-test")
    prov = sample_terminology.get_provenance("C1")["C1"]['changes']
    assert len(prov) == 2
    assert prov[-1]['action'] == "Edit Mapping"
    assert prov[-1]['old_value'] == "MAPPED_CODE"
    assert prov[-1]['new_value'] == "NEW_CODE"

    sample_terminology.set_mapping("C1", [coding_map, CodingMapping("NEW_CODE", "New Mapped Display", "http://mapping.system", mapping_relationship="equivalent")], "unit-test")
    prov = sample_terminology.get_provenance("C1")["C1"]['changes']
    assert len(prov) == 3
    assert prov[-1]['action'] == "Edit Mapping"
    assert prov[-1]['old_value'] == "NEW_CODE"
    assert prov[-1]['new_value'] == "MAPPED_CODE,NEW_CODE"

def test_delete_singular_mapping_provenance(sample_terminology):
    # Setup some dummy mappings for testing the stub
    sample_terminology.save()
    sample_terminology.set_mapping("C1", [
                CodingMapping("MAP1", display="Map One", system="http://map.com", mapping_relationship='equivalent'), 
                CodingMapping("MAP2", "Map Two", "http://map.com", mapping_relationship='equivalent')], "editorA")
    sample_terminology.set_mapping("C2", [CodingMapping("MAP2", "Map Two", "http://map.com", mapping_relationship='equivalent')], "editorA")   
    
    prov = sample_terminology.get_provenance("C1")["C1"]['changes']
    assert len(prov) == 1

    # Test deleting a specific code's mapping for an editor
    sample_terminology.delete_mappings(editor="editorA", code="C1")
    prov = sample_terminology.get_provenance("C1")["C1"]['changes']

    assert len(prov) == 2
    assert prov[-1]['action'] == "Soft Delete Mapping"
    old_value = prov[-1]['old_value']
    assert len(old_value['codes']) == 2
    assert old_value['codes'][0]['code'] == "MAP1"
    assert old_value['codes'][0]['display'] == "Map One"
    assert old_value['codes'][0]['system'] == "http://map.com"
    assert old_value['codes'][1]['code'] == "MAP2"
    assert old_value['codes'][1]['display'] == "Map Two"
    assert old_value['code'] == "C1"
    
    assert 'timestamp' in prov[-1]
    assert prov[-1]['target'] == "C1"

def test_delete_all_mapping_provenance(sample_terminology):
    # Setup some dummy mappings for testing the stub
    sample_terminology.save()
    sample_terminology.set_mapping("C1", [
                CodingMapping("MAP1", display="Map One", system="http://map.com", mapping_relationship='equivalent'), 
                CodingMapping("MAP2", "Map Two", "http://map.com", mapping_relationship='equivalent')], "editorA")
    sample_terminology.set_mapping("C2", [CodingMapping("MAP2", "Map Two", "http://map.com", mapping_relationship='equivalent')], "editorA")   
    
    assert len(sample_terminology.get_provenance("C1")["C1"]['changes']) == 1
    assert len(sample_terminology.get_provenance("C2")["C2"]['changes']) == 1

    # Test deleting a specific code's mapping for an editor
    sample_terminology.delete_mappings(editor="editorA")

    prov = sample_terminology.get_provenance("self")['self']['changes']
    print(prov[-1])
    assert prov[-1]['action'] == "Soft Delete All Mappings"
    assert prov[-1]['editor'] == "editorA"

    prov = sample_terminology.get_provenance("C1")["C1"]['changes']
    assert len(prov) == 2
    assert prov[-1]['action'] == "Soft Delete Mapping"
    old_value = prov[-1]['old_value']
    assert len(old_value['codes']) == 2
    assert old_value['codes'][0]['code'] == "MAP1"
    assert old_value['codes'][0]['display'] == "Map One"
    assert old_value['codes'][0]['system'] == "http://map.com"
    assert old_value['codes'][1]['code'] == "MAP2"
    assert old_value['codes'][1]['display'] == "Map Two"
    assert old_value['code'] == "C1"
    
    assert 'timestamp' in prov[-1]
    assert prov[-1]['target'] == "C1"

    prov = sample_terminology.get_provenance("C2")["C2"]['changes']
    assert len(prov) == 2
    assert prov[-1]['action'] == "Soft Delete Mapping"
    old_value = prov[-1]['old_value']
    assert len(old_value['codes']) == 1

def test_delete_mappings(sample_terminology):
    # Setup some dummy mappings for testing the stub
    sample_terminology.save()
    sample_terminology.set_mapping("C1", [CodingMapping("MAP1", display="Map One", system="http://map.com", mapping_relationship='equivalent')], "editorA")
    sample_terminology.set_mapping("C2", [CodingMapping("MAP2", "Map Two", "http://map.com", mapping_relationship='equivalent')], "editorA")
    sample_terminology.set_mapping("C1", [CodingMapping("MAP3", "Map Three", "http://map.com", mapping_relationship='equivalent')], "editorB")

    # Test deleting a specific code's mapping for an editor
    sample_terminology.delete_mappings(editor="editorA", code="C1")

    mappings = [mp for mp in sample_terminology.mappings("C1")["C1"] if mp.valid]

    assert len(mappings) == 0 # Only editorB's mapping for C1 should remain
    assert sample_terminology.mappings("C2") # C2 mapping for editorA should still exist

    # Test deleting all mappings for an editor
    sample_terminology.delete_mappings(editor="editorA")
    mappings = [mp for mp in sample_terminology.mappings("C2")["C2"] if mp.valid]
    assert len(mappings) == 0 # C2 mapping for editorA should be gone
    mappings = [mp for mp in sample_terminology.mappings("C1")["C1"] if mp.valid]
    assert len(mappings) == 0 # editorB's mapping for C1 should remain

def test_mapping_relationship(sample_terminology):
    try:
        mapping_c1_editorA = CodingMapping("MAP_C1_A", "Map C1 A", "http://map.com/A", mapping_relationship='equivalent')
        mapping_c1_editorB = CodingMapping("MAP_C1_B", "Map C1 B", "http://map.com/B", mapping_relationship='source-is-narrower-than-target')
        mapping_c2_editorA = CodingMapping("MAP_C2_A", "Map C2 A", "http://map.com/A", mapping_relationship='source-is-broader-than-target')
        mapping_c2_editorB = CodingMapping("MAP_C2_B", "Map C2 A", "http://map.com/A", mapping_relationship='')
    except Exception as e:
        raise pytest.fail(f"There was a problem with acceptable mapping relationships: {e}")
    
    with pytest.raises(InvalidValueError) as e_info:
        mapping_c2_editorA = CodingMapping("MAP_C2_A", "Map C2 A", "http://map.com/A", mapping_relationship='asdf')


def test_mappings(sample_terminology):
    # Setup some dummy mappings for testing the stub
    mapping_c1_editorA = CodingMapping("MAP_C1_A", "Map C1 A", "http://map.com/A", mapping_relationship='equivalent')
    mapping_c1_editorB = CodingMapping("MAP_C1_B", "Map C1 B", "http://map.com/B", mapping_relationship='equivalent')
    mapping_c2_editorA = CodingMapping("MAP_C2_A", "Map C2 A", "http://map.com/A", mapping_relationship='equivalent')

    sample_terminology.set_mapping("C1", [mapping_c1_editorA, mapping_c1_editorB], "editorA")
    
    sample_terminology.set_mapping("C2", [mapping_c2_editorA], "editorA")

    c1_mappings = sample_terminology.mappings("C1")["C1"]
    assert len(c1_mappings) == 2
    assert any(m.code == "MAP_C1_A" for m in c1_mappings)
    assert any(m.code == "MAP_C1_B" for m in c1_mappings)

    # Replace the previous mappings
    sample_terminology.set_mapping("C1", [mapping_c1_editorB], "editorA")
    c1_mappings = sample_terminology.mappings("C1")["C1"]
    assert len(c1_mappings) == 1
    assert c1_mappings[0].code == "MAP_C1_B"
    
    c2_mappings = sample_terminology.mappings("C2")["C2"]
    assert len(c2_mappings) == 1
    assert c2_mappings[0].code == "MAP_C2_A"

    mappings = [mp for mp in sample_terminology.mappings("C99")["C99"] if mp.valid]
    assert len(mappings) == 0 # No mappings for non-existent code

def test_get_provenance(sample_terminology):
    # Test with no provenance
    assert sample_terminology.get_provenance("C1")["C1"] == []

    # Add some provenance
    sample_terminology.add_provenance(change_type="created", editor="admin", target="C1", details="Initial creation")
    sample_terminology.add_provenance(change_type="modified", editor="user1", target="C1", old_value="valA", new_value="valB")

    provenance_c1 = sample_terminology.get_provenance("C1")["C1"]["changes"]
    assert len(provenance_c1) == 2
    assert provenance_c1[0]["action"] == "created"
    assert provenance_c1[1]["editor"] == "user1"

    assert sample_terminology.get_provenance("C2")["C2"] == []

def test_add_provenance(sample_terminology):
    initial_provenance_count = len(sample_terminology.get_provenance("C1")["C1"])
    sample_terminology.add_provenance(change_type="added", editor="test_editor", target="C1", new_entry="Some new data")
    assert len(sample_terminology.get_provenance("C1")["C1"]["changes"]) == initial_provenance_count + 1
    new_provenance_entry = sample_terminology.get_provenance("C1")["C1"]["changes"][-1]
    assert new_provenance_entry["action"] == "added"
    assert new_provenance_entry["editor"] == "test_editor"
    assert new_provenance_entry["target"] == "C1"
    assert new_provenance_entry["new_entry"] == "Some new data"
    assert "timestamp" in new_provenance_entry
