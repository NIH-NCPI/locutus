import pytest 
from locutus.model.terminology import Terminology, Coding, CodingMapping
from .test_terminology import sample_terminology, sample_terminology_with_editor

# import pdb 

_all_terms = None
@pytest.fixture
def all_terminologies():
    global _all_terms 

    if _all_terms is None:
        _all_terms = Terminology.get()
    return _all_terms

def test_get_preference_terminology(sample_terminology):
    # Test with no preference set
    assert "C1" not in sample_terminology.get_preference()

    # Set a preference
    sample_terminology.add_or_update_pref({"ols": ["HP", "MONDO"]})
    assert sample_terminology.get_preference()["self"]["api_preference"] == {"ols": ["HP", "MONDO"]}

    # Test for a code without preference
    assert "C99" not in sample_terminology.get_preference("C99")


def test_add_or_update_pref_terminology(sample_terminology):
    # Add a new preference
    sample_terminology.add_or_update_pref({"ols": ["HP", "MONDO"]})
    assert sample_terminology.get_preference()["self"]["api_preference"]  == {"ols": ["HP", "MONDO"]}

    # Update an existing preference
    sample_terminology.add_or_update_pref({"umls": ["MAXO"]})
    assert sample_terminology.get_preference()["self"]["api_preference"] == {"umls": ["MAXO"]}

def test_get_preference(sample_terminology):
    # Test with no preference set
    assert "C1" not in sample_terminology.get_preference("C1")

    # Set a preference
    sample_terminology.add_or_update_pref({"ols": ["HP", "MONDO"]}, "C1")
    assert sample_terminology.get_preference("C1")["C1"]["api_preference"] == {"ols": ["HP", "MONDO"]}

    # Test for a code without preference
    assert "C99" not in sample_terminology.get_preference("C99")

def test_add_or_update_pref(sample_terminology):
    # Add a new preference
    sample_terminology.add_or_update_pref({"ols": ["HP", "MONDO"]}, "C1")
    assert sample_terminology.get_preference("C1")["C1"]["api_preference"]  == {"ols": ["HP", "MONDO"]}

    # Update an existing preference
    sample_terminology.add_or_update_pref({"umls": ["MAXO"]}, "C1")
    assert sample_terminology.get_preference("C1")["C1"]["api_preference"] == {"umls": ["MAXO"]}

    
def test_remove_pref(sample_terminology):
    sample_terminology.add_or_update_pref({"ols": ["HP", "MONDO"]}, "C1")
    assert sample_terminology.get_preference("C1")["C1"]["api_preference"] is not None

    sample_terminology.remove_pref("C1")
    assert "C1" not in sample_terminology.get_preference("C1")

    # Test removing a non-existent preference
    sample_terminology.remove_pref("C99")
    assert "C99" not in sample_terminology.get_preference("C99")


def test_get_preferred_terminology(sample_terminology, all_terminologies):
    term = all_terminologies[0].id
    assert sample_terminology.get_preferred_terminology()["references"] == []
    sample_terminology.replace_preferred_terminology("unit-test", [{"preferred_terminology": term}])
    assert sample_terminology.get_preferred_terminology()["references"] == [{"reference": f"Terminology/{term}"}]

def test_replace_preferred_terminology(sample_terminology, all_terminologies):
    term1 = all_terminologies[1].id
    term2 = all_terminologies[0].id
    assert sample_terminology.get_preferred_terminology()["references"] == []
    sample_terminology.replace_preferred_terminology("unit-test", [{"preferred_terminology": term1}])
    assert sample_terminology.get_preferred_terminology()["references"] == [{"reference": f"Terminology/{term1}"}]
    sample_terminology.replace_preferred_terminology("unit-test", [{"preferred_terminology": term2}])
    assert sample_terminology.get_preferred_terminology()["references"] == [{"reference": f"Terminology/{term2}"}]

def test_remove_preferred_terminology(sample_terminology, all_terminologies):
    term = all_terminologies[0].id
    sample_terminology.replace_preferred_terminology("unit-test", [{"preferred_terminology": term}])
    assert sample_terminology.get_preferred_terminology()["references"] == [{"reference": f"Terminology/{term}"}]

    # Remove the set preferred terminology
    sample_terminology.remove_preferred_terminology()
    assert sample_terminology.get_preferred_terminology()["references"] == []
