import pytest

from locutus.model.table import Table

from . import client
from .test_table import basic_table
from .test_terminology import sample_terminology


def _row(table_id, **overrides):
    row = {
        "table_id": table_id,
        "source_variable": "string_var",
        "source_enumeration": "string_var",
        "code": "MAPPED_CODE",
        "display": "Mapped Display",
        "system": "http://mapping.system",
        "provenance": "csv-import",
        "mapping_relationship": "",
    }
    row.update(overrides)
    return row


def test_sideload_post_happy_path(client, sample_terminology, basic_table):
    response = client.post(
        "/api/SideLoad",
        json={"csvContents": [_row(basic_table.id)]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    # Documents current behavior: SetMappings has no return statement, so a
    # successful sideload responds with a JSON null body.
    assert response.json is None

    table = Table.get(basic_table.id)
    term = table.terminology.dereference()
    mappings = term.mappings("string_var")["string_var"]
    assert len(mappings) == 1
    assert mappings[0].code == "MAPPED_CODE"


def test_sideload_post_missing_csv_contents_raises(client):
    # Documents current behavior: SideLoad.post indexes mapping_data["csvContents"]
    # directly; a body without that key raises an unhandled KeyError instead
    # of the LackingRequiredParameter/APIError the surrounding except clauses
    # are set up to catch.
    with pytest.raises(KeyError):
        client.post(
            "/api/SideLoad", json={}, headers={"Content-Type": "application/json"}
        )


def test_sideload_post_missing_mapping_relationship_key_raises(
    client, sample_terminology, basic_table
):
    # Documents current behavior: Coding.set_mappings always validates
    # mapping.mapping_relationship, even though CodingMapping itself only
    # validates when it's not None. A row shaped without the
    # 'mapping_relationship' key entirely (as opposed to present-but-blank,
    # which is what a real CSV upload would produce) ends up with
    # mapping_relationship=None and crashes.
    row = _row(basic_table.id)
    del row["mapping_relationship"]

    with pytest.raises(TypeError):
        client.post(
            "/api/SideLoad",
            json={"csvContents": [row]},
            headers={"Content-Type": "application/json"},
        )


def test_sideload_post_missing_provenance_returns_400(
    client, sample_terminology, basic_table
):
    row = _row(basic_table.id, provenance="")
    response = client.post(
        "/api/SideLoad",
        json={"csvContents": [row]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_sideload_post_table_not_found_returns_400(client):
    row = _row("not-a-real-table")
    response = client.post(
        "/api/SideLoad",
        json={"csvContents": [row]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
