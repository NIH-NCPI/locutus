import pytest

from locutus.model.table import Table

from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def _row(table_id, **overrides):
    row = {
        "table_id": table_id,
        "source_variable": "string_var",
        "source_enumeration": "string_var",
        "code": "HP:0001250",
        "display": "Mapped Display",
        "system": "http://purl.obolibrary.org/obo/hp.owl",
        "provenance": "csv-import",
        "mapping_relationship": "",
    }
    row.update(overrides)
    return row


def test_sideload_post_requires_auth(client, sample_terminology, basic_table):
    response = client.post(
        "/api/SideLoad",
        json={"csvContents": [_row(basic_table.id)]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_sideload_post_happy_path(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": [_row(basic_table.id)]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json["mappings_applied"] == 1

        table = Table.get(basic_table.id)
        assert table is not None
        term = table.terminology.dereference()
        mappings = term.mappings("string_var")["string_var"]
        assert len(mappings) == 1
        assert mappings[0].code == "HP:0001250"
    finally:
        test_owner.cleanup()


def test_sideload_post_requires_write_access(client, sample_terminology, basic_table):
    # basic_table's default owner_id is None (Registered visibility) -- a
    # real, different, logged-in user only gets viewer access, so the whole
    # batch is rejected before any write, per M12.
    test_owner = _Owner(client)
    try:
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": [_row(basic_table.id)]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
        assert response.json["table_ids"] == [basic_table.id]

        table = Table.get(basic_table.id)
        assert table is not None
        term = table.terminology.dereference()
        mappings = term.mappings("string_var")["string_var"]
        assert mappings == []
    finally:
        test_owner.cleanup()


def test_sideload_post_missing_csv_contents_raises(client):
    # Documents current behavior: SideLoad.post indexes mapping_data["csvContents"]
    # directly; a body without that key raises an unhandled KeyError instead
    # of the LackingRequiredParameter/APIError the surrounding except clauses
    # are set up to catch.
    test_owner = _Owner(client)
    try:
        with pytest.raises(KeyError):
            client.post(
                "/api/SideLoad", json={}, headers={"Content-Type": "application/json"}
            )
    finally:
        test_owner.cleanup()


def test_sideload_post_missing_mapping_relationship_key_raises(
    client, sample_terminology, basic_table
):
    # Documents current behavior: Coding.set_mappings always validates
    # mapping.mapping_relationship, even though CodingMapping itself only
    # validates when it's not None. A row shaped without the
    # 'mapping_relationship' key entirely (as opposed to present-but-blank,
    # which is what a real CSV upload would produce) ends up with
    # mapping_relationship=None and crashes.
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        row = _row(basic_table.id)
        del row["mapping_relationship"]

        with pytest.raises(TypeError):
            client.post(
                "/api/SideLoad",
                json={"csvContents": [row]},
                headers={"Content-Type": "application/json"},
            )
    finally:
        test_owner.cleanup()


def test_sideload_post_missing_provenance_returns_400(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        row = _row(basic_table.id, provenance="")
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": [row]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_sideload_post_table_not_found_returns_400(client):
    test_owner = _Owner(client)
    try:
        row = _row("not-a-real-table")
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": [row]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_sideload_harmonizes_mapped_codes(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        rows = [
            _row(basic_table.id, code="hpo:0001250"),
            _row(
                basic_table.id,
                code="0002197",
                system="https://purl.obolibrary.org/obo/hp.owl/",
            ),
        ]
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": rows},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        table = Table.get(basic_table.id)
        assert table is not None
        mappings = table.terminology.dereference().mappings("string_var")["string_var"]
        assert [(m.code, m.system) for m in mappings] == [
            ("HP:0001250", "http://purl.obolibrary.org/obo/hp.owl"),
            ("HP:0002197", "http://purl.obolibrary.org/obo/hp.owl"),
        ]
    finally:
        test_owner.cleanup()


def test_sideload_rejects_unrecognized_codes_before_writing(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        rows = [
            _row(basic_table.id),
            _row(basic_table.id, code="MAPPED_CODE", system="http://mapping.system"),
            _row(basic_table.id, code="", system=""),  # blank line, tolerated
            _row(basic_table.id, code="HP:0001250", system="http://snomed.info/sct"),
        ]
        response = client.post(
            "/api/SideLoad",
            json={"csvContents": rows},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert response.json["error"] == "UnrecognizedMappingCode"
        problems = response.json["problems"]
        assert len(problems) == 2
        assert problems[0].startswith("row 2 (string_var/string_var):")
        assert "unknown system" in problems[0]
        assert problems[1].startswith("row 4 ")
        assert "the system is 'snomedct'" in problems[1]

        table = Table.get(basic_table.id)
        assert table is not None
        mappings = table.terminology.dereference().mappings("string_var")
        assert mappings.get("string_var", []) == []
    finally:
        test_owner.cleanup()
