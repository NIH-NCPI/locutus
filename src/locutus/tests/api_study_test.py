import pytest

from locutus.model.study import Study

from . import _Owner, client
from .test_study import basic_study
from .test_terminology import sample_terminology


def test_study_get_requires_auth(client):
    response = client.get("/api/Study/not-there")
    assert response.status_code == 401


def test_study_none(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Study/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_study_get(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
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
    finally:
        test_owner.cleanup()


def test_studies_post_requires_auth(client):
    body = {
        "name": "No Auth Study",
        "title": "No Auth Study Title",
        "url": "http://ftd.unit.tests/api_study/no_auth",
    }
    response = client.post(
        "/api/Study", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 401


def test_studies_post_creates_study(client):
    test_owner = _Owner(client)
    try:
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
        # The creator is stamped as owner automatically (M4) -- never
        # trusted from the request body.
        assert created["owner_id"] == test_owner.user.id

        study = Study.get(created["id"])
        assert study is not None
        study.delete(hard_delete=True)
    finally:
        test_owner.cleanup()


def test_studies_post_missing_title(client):
    test_owner = _Owner(client)
    try:
        body = {
            "name": "Missing Title Study",
            "url": "http://ftd.unit.tests/api_study/no_title",
        }

        response = client.post(
            "/api/Study", json=body, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_studies_post_missing_name(client):
    test_owner = _Owner(client)
    try:
        body = {
            "title": "Missing Name Study",
            "url": "http://ftd.unit.tests/api_study/no_name",
        }

        response = client.post(
            "/api/Study", json=body, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_study_put_updates_study(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_study)

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
        assert study is not None
        assert study.description == "Updated Description"
        # PUT must not let the client reassign ownership via the body.
        assert study.owner_id == test_owner.user.id
    finally:
        test_owner.cleanup()


def test_study_put_requires_write_access(client, sample_terminology, basic_study):
    """basic_study's default owner_id is None -- a real, different,
    logged-in user only gets Registered-visibility viewer access, not
    editor, so a write must 403."""
    test_owner = _Owner(client)
    try:
        updated = dict(client.get(f"/api/Study/{basic_study.id}").json)

        response = client.put(
            f"/api/Study/{basic_study.id}",
            json=updated,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_study_delete(client):
    test_owner = _Owner(client)
    try:
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
    finally:
        test_owner.cleanup()


def test_study_delete_requires_write_access(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
        response = client.delete(f"/api/Study/{basic_study.id}")
        assert response.status_code == 403
        assert Study.get(basic_study.id) is not None
    finally:
        test_owner.cleanup()


def test_study_delete_missing_study_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.delete("/api/Study/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_study_edit_removes_dd_reference(client):
    test_owner = _Owner(client)
    try:
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
        assert study is not None
        study.delete(hard_delete=True)
    finally:
        test_owner.cleanup()


def test_study_edit_dd_reference_not_found(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_study)
        response = client.delete(f"/api/Study/{basic_study.id}/dd/does-not-exist")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_study_edit_requires_write_access(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
        response = client.delete(f"/api/Study/{basic_study.id}/dd/does-not-exist")
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


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
    # Documents current behavior: StudyHarmony is out of scope for Phase 5
    # (M11 aggregate endpoint, same as HarmonyTableCSV) and still does not
    # check for a None result before calling .as_harmony() on it.
    with pytest.raises(AttributeError):
        client.get("/api/Study/not-there/harmony")
