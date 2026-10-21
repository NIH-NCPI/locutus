import logging

import pytest

from locutus.model.exceptions import UnrecognizedMappingCode
from locutus.model.lookups import FTDOntologyLookup
from locutus.model.mapped_codes import (
    harmonize_for_export,
    harmonize_mapping,
    harmonize_mappings,
)

HP_SYSTEM = "http://purl.obolibrary.org/obo/hp.owl"
SNOMED_SYSTEM = "http://snomed.info/sct"


def test_harmonize_mapping_keeps_other_fields():
    mapping = {"code": "HPO:0001250", "display": "Seizure", "mapping_relationship": ""}
    assert harmonize_mapping(mapping) == {
        "code": "HP:0001250",
        "display": "Seizure",
        "mapping_relationship": "",
        "system": HP_SYSTEM,
    }
    assert mapping["code"] == "HPO:0001250"  # input untouched


def test_harmonize_mappings_reports_every_problem():
    with pytest.raises(UnrecognizedMappingCode) as error:
        harmonize_mappings(
            [
                {"code": "HP:0001250"},
                {"code": "FOO:1"},
                {"code": "123", "system": "http://nowhere.example"},
            ]
        )
    assert [p.split(":")[0] for p in error.value.problems] == ["mapping 1", "mapping 2"]
    assert error.value.status_code == 400
    assert error.value.to_dict()["problems"] == error.value.problems


class TestExport:
    def test_harmonizes(self):
        assert harmonize_for_export(
            "0001250", "https://purl.obolibrary.org/obo/hp.owl/"
        ) == (
            "HP:0001250",
            HP_SYSTEM,
        )

    def test_unmatched_is_exported_as_stored_with_a_warning(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = harmonize_for_export("OLD:123", "http://old.example/system")
        assert result == ("OLD:123", "http://old.example/system")
        assert "can't be harmonized" in caplog.text

    def test_prefix_wins_over_a_conflicting_system(self, caplog):
        with caplog.at_level(logging.WARNING):
            result = harmonize_for_export("HP:0001250", SNOMED_SYSTEM)
        assert result == ("HP:0001250", HP_SYSTEM)
        assert "using the prefix" in caplog.text


class TestFTDOntologyLookup:
    @pytest.mark.parametrize(
        ("system", "prefix"),
        [
            (HP_SYSTEM, "HP"),
            ("https://purl.obolibrary.org/obo/hp.owl/", "HP"),
            (SNOMED_SYSTEM, "snomedct"),
            ("http://nowhere.example", ""),
            ("", ""),
            (None, ""),
        ],
    )
    def test_get_mapped_curie(self, system, prefix):
        assert FTDOntologyLookup.get_mapped_curie(system) == prefix

    def test_get_mapped_system(self):
        assert FTDOntologyLookup.get_mapped_system("hpo") == HP_SYSTEM
        assert FTDOntologyLookup.get_mapped_system("NOPE") == "NOPE"
