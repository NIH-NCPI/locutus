import pytest

from locutus.model.datadictionary import DataDictionary
from locutus.model.reference import Reference
from locutus.model.study import Study

from . import client
from .test_datadictionary import basic_datadictionary
from .test_study import basic_study
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_dd_post_creates_dd(client):
    response = client.post(
        "/api/DataDictionary",
        json={"name": "API Created DD", "description": "Created via POST"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201

    created = response.json
    assert created["name"] == "API Created DD"

    dd = DataDictionary.get(created["id"])
    assert dd is not None
    dd.delete(hard_delete=True)


def test_dd_put_updates_dd(client, basic_study, basic_datadictionary):
    updated = dict(client.get(f"/api/DataDictionary/{basic_datadictionary.id}").json)
    updated["description"] = "Updated Description"

    response = client.put(
        f"/api/DataDictionary/{basic_datadictionary.id}",
        json=updated,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    assert response.json["description"] == "Updated Description"


def test_dd_delete_also_clears_study_references(client, basic_study):
    dd = DataDictionary(name="DD For Study Ref Test")
    dd.save()

    study = Study.get(basic_study.id)
    study.datadictionary.append(Reference(f"DataDictionary/{dd.id}"))
    study.save()

    response = client.delete(f"/api/DataDictionary/{dd.id}")
    assert response.status_code == 200
    assert response.json["id"] == dd.id

    assert DataDictionary.get(dd.id) is None

    refreshed_study = Study.get(basic_study.id)
    assert refreshed_study.datadictionary == []


def test_dd_delete_missing_dd_raises(client):
    # Documents current behavior: DataDictionary.delete does not check for a
    # None DataDictionary before calling .dump() on it.
    with pytest.raises(AttributeError):
        client.delete("/api/DataDictionary/not-there")


def test_dd_table_delete(client, basic_study, basic_datadictionary, basic_table):
    response = client.delete(
        f"/api/DataDictionary/{basic_datadictionary.id}/Table/{basic_table.id}"
    )
    assert response.status_code == 200
    assert response.json["tables"] == []


def test_dd_table_delete_missing_dd_raises(client):
    # Documents current behavior: DataDictionaryTable.delete does not check
    # for a None DataDictionary before calling .remove_table() on it.
    with pytest.raises(AttributeError):
        client.delete("/api/DataDictionary/not-there/Table/some-table")


def test_dd_harmony_default(client, basic_study, basic_datadictionary):
    response = client.get(f"/api/DataDictionary/{basic_datadictionary.id}/harmony")
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_dd_harmony_invalid_format(client, basic_study, basic_datadictionary):
    response = client.get(
        f"/api/DataDictionary/{basic_datadictionary.id}/harmony",
        query_string={"format": "not-a-format"},
    )
    assert response.status_code == 400


def test_dd_harmony_missing_dd_raises(client):
    # Documents current behavior: DataDictionaryHarmony.get does not check
    # for a None DataDictionary before calling .as_harmony() on it.
    with pytest.raises(AttributeError):
        client.get("/api/DataDictionary/not-there/harmony")
