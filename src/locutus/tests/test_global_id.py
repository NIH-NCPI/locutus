import pytest
from locutus.model import GlobalID 

import pdb

from rich import print
import pytest


def test_global_id_persistence():
    current_ids = list(GlobalID.find("Terminology"))

    gid1 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyOne")
    gid1.save()

    gid2 = GlobalID(resource_type="Terminology", 
                   key="http://someplace.org:TerminologyTwo")
    gid2.save()

    assert gid1._id is not None 
    assert gid2._id is not None 

    term_ids = GlobalID.find("Terminology")
    assert type(term_ids) is list
    assert len(term_ids) == 2 + len(current_ids)

    gid1.delete()
    gid2.delete()

def test_common_domain_functionality():
    current_ids = list(GlobalID.find("Terminology"))

    gid1 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyOne",
                    domain="Domain 1")
    gid1.save()


    gid2 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyOne",
                    domain="Domain 1", reuse_id=True)
    gid2.save()

    assert gid1._id is not None 
    assert gid2._id is not None 
    assert gid1._id == gid2._id

    # Test that the search only returns one for the correct domain
    term_ids = GlobalID.find("Terminology")
    assert len(list(term_ids)) == len(current_ids)

    term_ids = GlobalID.find("Terminology",
                    domain="Domain 1")
    assert type(term_ids) is GlobalID

    gid1.delete()


def test_distinct_domain_functionality():
    current_ids = list(GlobalID.find("Terminology"))

    gid1 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyOne",
                    domain="Domain 1")
    gid1.save()

    gid2 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyOne",
                    domain="Domain 2")
    gid2.save()
    gid3 = GlobalID(resource_type="Terminology", 
                    key="http//someplace.org:TerminologyTwo",
                    domain="Domain 2")

    assert gid1._id is not None 
    assert gid2._id is not None 
    assert gid3._id is not None

    # Test that the search only returns one for the correct domain
    term_ids = GlobalID.find("Terminology")
    assert len(list(term_ids)) == len(current_ids)

    term_ids = GlobalID.find("Terminology",
                    domain="Domain 1")
    assert type(term_ids) is GlobalID


    term_ids = GlobalID.find("Terminology",
                    domain="Domain 2")
    assert type(term_ids) is list 
    assert len(term_ids) == 2

    gid1.delete()
    gid2.delete()
    gid3.delete()

def test_global_id_creation_full():
    """
    Tests that a GlobalID object is created correctly with all parameters.
    """
    gid = GlobalID(resource_type="Terminology", key="ICD10", id="ICD10-12345", object_id="db-9876")
    
    assert gid.resource_type == "Terminology"
    assert gid.key == "ICD10"
    assert gid.id == "ICD10-12345"
    assert gid.object_id == "db-9876"
    gid.delete()

def test_global_id_creation_minimal():
    """
    Tests that a GlobalID object can be created with only the required parameters.
    """
    gid = GlobalID(resource_type="DataDictionary", key="LOINC")

    assert gid.resource_type == "DataDictionary"
    assert gid.key == "LOINC"
    assert gid.id[0:3] == "dd-"
    assert gid.object_id is None
    gid.delete()

def test_global_id_dump_full():
    """
    Tests that the dump() method returns the correct dictionary for a full object.
    """
    gid = GlobalID(resource_type="Terminology", key="ICD10", id="ICD10-12345", object_id="db-9876")

    expected_dict = {
        "domain": "",
        "resource_type": "Terminology",
        "key": "ICD10",
        "id": "ICD10-12345",
        "object_id": "db-9876"
    }

    assert gid.dump() == expected_dict
    gid.delete()

def test_global_id_dump_minimal():
    """
    Tests that the dump() method returns the correct dictionary for a minimal object.
    """
    gid = GlobalID(resource_type="Study", key="ABCD")
    gidd = gid.dump()
    assert gidd.get("resource_type") == "Study"
    assert gidd.get("key") == "ABCD"
    assert "id" in gidd
    assert gidd.get("object_id") is None
    gid.delete()


def test_invalid_resource_type():
    with pytest.raises(ValueError, match="is not a valid resource type"):
        gid = GlobalID(resource_type="noresource", key="code1")

@pytest.mark.parametrize("resource_type, key", [
    ("", "key1"),
    ("resource", ""),
    (123, "key2"),
    ("resource3", 456),
    (None, "key4")
])
def test_global_id_invalid_required_params(resource_type, key):
    """
    Tests for invalid or missing required parameters, expecting a TypeError.
    Note: The current implementation doesn't raise an error for empty strings
    or None, but it is good practice to test for these cases in a real-world
    scenario, where you might add validation.
    """
    with pytest.raises(ValueError, match="is required for all"):
        gid = GlobalID(resource_type=resource_type, key=key)
    