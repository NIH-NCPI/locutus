import pytest 
from locutus.model.terminology import Terminology, Coding, CodingMapping
from .test_terminology import sample_terminology, sample_terminology_with_editor

import pdb 

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