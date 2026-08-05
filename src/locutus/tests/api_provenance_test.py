import pytest

from locutus.model.provenance import Provenance

from . import client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_table_provenance_get(client, sample_terminology, basic_table):
    response = client.get(f"/api/Provenance/Table/{basic_table.id}")
    assert response.status_code == 200

    body = response.json
    assert body["table"]["Reference"] == f"Table/{basic_table.id}"
    assert body["provenance"]["self"]["target"] == "self"


def test_table_var_provenance_get_all(client, sample_terminology, basic_table):
    response = client.get(f"/api/Provenance/Table/{basic_table.id}/code/ALL")
    assert response.status_code == 200
    assert "provenance" in response.json


def test_table_var_provenance_get_specific_code(
    client, sample_terminology, basic_table
):
    response = client.get(f"/api/Provenance/Table/{basic_table.id}/code/string_var")
    assert response.status_code == 200
    assert "provenance" in response.json


def test_table_provenance_get_missing_table_raises(client):
    # Documents current behavior: TableProvenance.get does not check for a
    # None Table before calling .terminology.dereference() on it.
    with pytest.raises(AttributeError):
        client.get("/api/Provenance/Table/not-there")


def test_terminology_provenance_get(client, sample_terminology):
    # Renaming a code (via the model, mirroring what the rename endpoint
    # does) generates a provenance entry to make the response non-trivial.
    sample_terminology.add_provenance(
        change_type=Provenance.ChangeType.EditTerm,
        target="self",
        old_value="before",
        new_value="after",
        editor="unit-test",
    )

    response = client.get(f"/api/Provenance/Terminology/{sample_terminology.id}")
    assert response.status_code == 200

    body = response.json
    assert body["terminology"]["Reference"] == f"Terminology/{sample_terminology.id}"
    assert len(body["provenance"]["self"]["changes"]) >= 1


def test_terminology_code_provenance_get(client, sample_terminology):
    response = client.get(
        f"/api/Provenance/Terminology/{sample_terminology.id}/code/C1"
    )
    assert response.status_code == 200
    assert "provenance" in response.json


def test_terminology_provenance_get_missing_terminology_raises(client):
    # Documents current behavior: TerminologyProvenance.get does not check
    # for a None Terminology before calling .get_provenance() on it.
    with pytest.raises(AttributeError):
        client.get("/api/Provenance/Terminology/not-there")
