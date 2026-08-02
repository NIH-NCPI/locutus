import pytest

from locutus.model.study import Study

from . import client
from .test_study import basic_study
from .test_terminology import sample_terminology


def test_study_none(client):
    response = client.get("/api/Study/not-there")
    assert response.status_code == 404


def test_study_get(client, sample_terminology, basic_study):
    response = client.get("/api/Study")
    assert response.status_code == 200

    studies = response.json
    assert len(studies) >= 1

    response = client.get(f"/api/Study/{basic_study.id}")
    assert response.status_code == 200

    study = response.json
    assert study["id"] == basic_study.id
    assert study["title"] == basic_study.title
    assert study["name"] == basic_study.name

    assert study["description"] == basic_study.description


def test_studies_post_creates_study(client):
    body = {
        "name": "API Created Study",
        "title": "API Created Study Title",
        "url": "http://ftd.unit.tests/api_study/created",
        "description": "Created via POST",
    }

    response = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 201

    created = response.json
    assert created["name"] == "API Created Study"
    assert created["id"] is not None

    study = Study.get(created["id"])
    assert study is not None
    study.delete(hard_delete=True)


def test_studies_post_missing_title(client):
    body = {
        "name": "Missing Title Study",
        "url": "http://ftd.unit.tests/api_study/no_title",
    }

    response = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


def test_studies_post_missing_name(client):
    body = {
        "title": "Missing Name Study",
        "url": "http://ftd.unit.tests/api_study/no_name",
    }

    response = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


def test_study_put_updates_study(client, sample_terminology, basic_study):
    updated = dict(client.get(f"/api/Study/{basic_study.id}").json)
    updated["description"] = "Updated Description"

    response = client.put(
        f"/api/Study/{basic_study.id}",
        json=updated,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 201
    assert response.json["description"] == "Updated Description"

    study = Study.get(basic_study.id)
    assert study.description == "Updated Description"


def test_study_delete(client):
    body = {
        "name": "Study To Delete",
        "title": "Study To Delete Title",
        "url": "http://ftd.unit.tests/api_study/to_delete",
    }
    created = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    ).json
    study_id = created["id"]

    response = client.delete(f"/api/Study/{study_id}")
    assert response.status_code == 200
    assert response.json["id"] == study_id

    assert Study.get(study_id) is None


def test_study_delete_missing_study_raises(client):
    # Documents current behavior: Study.delete does not check for a None
    # result before calling .dump() on it, so a missing id blows up with an
    # unhandled AttributeError instead of returning 404.
    with pytest.raises(AttributeError):
        client.delete("/api/Study/not-there")


def test_study_edit_removes_dd_reference(client):
    body = {
        "name": "Study With DD",
        "title": "Study With DD Title",
        "url": "http://ftd.unit.tests/api_study/with_dd",
        "datadictionary": [{"reference": "DataDictionary/dd-fake"}],
    }
    created = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    ).json
    study_id = created["id"]

    response = client.delete(f"/api/Study/{study_id}/dd/dd-fake")
    assert response.status_code == 200
    assert response.json["datadictionary"] == []

    study = Study.get(study_id)
    study.delete(hard_delete=True)


def test_study_edit_dd_reference_not_found(client, sample_terminology, basic_study):
    response = client.delete(f"/api/Study/{basic_study.id}/dd/does-not-exist")
    assert response.status_code == 404


def test_study_harmony_default(client, sample_terminology, basic_study):
    response = client.get(f"/api/Study/{basic_study.id}/harmony")
    assert response.status_code == 200
    assert response.json == []


def test_study_harmony_invalid_format(client, sample_terminology, basic_study):
    response = client.get(
        f"/api/Study/{basic_study.id}/harmony", query_string={"format": "not-a-format"}
    )
    assert response.status_code == 400


def test_study_harmony_missing_study_raises(client):
    # Documents current behavior: StudyHarmony.get does not check for a None
    # result before calling .as_harmony() on it.
    with pytest.raises(AttributeError):
        client.get("/api/Study/not-there/harmony")
