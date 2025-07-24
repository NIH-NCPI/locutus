import pytest
import json
from locutus.model.terminology import Terminology, Coding


@pytest.fixture
def sample_terminology():
    initial_codes = [
        Coding(code="C1", display="Code One", system="http://example.com/ont1", description="Description for C1"),
        Coding(code="C2", display="Code Two", system="http://example.com/ont1", description="Description for C2")
    ]
    return Terminology(
        name="Ontology One",
        url="http://example.com/ont1",
        description="A sample oncology terminology",
        codes=initial_codes
    )

def test_terminology_init(sample_terminology):
    assert sample_terminology.name == "Ontology One"
    assert sample_terminology.url == "http://example.com/ont1"
    assert sample_terminology.description == "A sample oncology terminology"
    assert len(sample_terminology.codes) == 2
    assert sample_terminology.codes[0].code == "C1"

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

def test_remove_code(sample_terminology):
    sample_terminology.remove_code("C1", editor="unit-test")
    assert len(sample_terminology.codes) == 1
    assert not sample_terminology.has_code("C1")
    assert sample_terminology.has_code("C2")

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

def test_has_code(sample_terminology):
    assert sample_terminology.has_code("C1")
    assert sample_terminology.has_code("C2")
    assert not sample_terminology.has_code("C99")