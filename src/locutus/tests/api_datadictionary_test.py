import pytest

from locutus.model.datadictionary import DataDictionary
from locutus.model.reference import Reference
from locutus.model.study import Study

from . import _Owner, client
from .test_datadictionary import basic_datadictionary
from .test_study import basic_study
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_dd_post_requires_auth(client):
    response = client.post(
        "/api/DataDictionary",
        json={"name": "No Auth DD", "description": "Created via POST"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_dd_post_creates_dd(client):
    test_owner = _Owner(client)
    try:
        response = client.post(
            "/api/DataDictionary",
            json={"name": "API Created DD", "description": "Created via POST"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

        created = response.json
        assert created["name"] == "API Created DD"
        # The creator is stamped as owner automatically (M4) -- never
        # trusted from the request body.
        assert created["owner_id"] == test_owner.user.id

        dd = DataDictionary.get(created["id"])
        assert dd is not None
        dd.delete(hard_delete=True)
    finally:
        test_owner.cleanup()


def test_dd_put_updates_dd(client, basic_study, basic_datadictionary):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_datadictionary)

        updated = dict(
            client.get(f"/api/DataDictionary/{basic_datadictionary.id}").json
        )
        updated["description"] = "Updated Description"

        response = client.put(
            f"/api/DataDictionary/{basic_datadictionary.id}",
            json=updated,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201
        assert response.json["description"] == "Updated Description"
        # PUT must not let the client reassign ownership via the body.
        assert response.json["owner_id"] == test_owner.user.id
    finally:
        test_owner.cleanup()


def test_dd_put_requires_write_access(client, basic_study, basic_datadictionary):
    """basic_datadictionary's default owner_id is None -- a real, different,
    logged-in user only gets Registered-visibility viewer access."""
    test_owner = _Owner(client)
    try:
        updated = dict(
            client.get(f"/api/DataDictionary/{basic_datadictionary.id}").json
        )

        response = client.put(
            f"/api/DataDictionary/{basic_datadictionary.id}",
            json=updated,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_dd_delete_also_clears_study_references(client, basic_study):
    test_owner = _Owner(client)
    try:
        dd = DataDictionary(name="DD For Study Ref Test")
        test_owner.own(dd)

        study = Study.get(basic_study.id)
        assert study is not None
        study.datadictionary.append(Reference(f"DataDictionary/{dd.id}"))
        study.save()

        response = client.delete(f"/api/DataDictionary/{dd.id}")
        assert response.status_code == 200
        assert response.json["id"] == dd.id

        assert DataDictionary.get(dd.id) is None

        refreshed_study = Study.get(basic_study.id)
        assert refreshed_study is not None
        assert refreshed_study.datadictionary == []
    finally:
        test_owner.cleanup()


def test_dd_delete_requires_write_access(client, basic_study, basic_datadictionary):
    test_owner = _Owner(client)
    try:
        response = client.delete(f"/api/DataDictionary/{basic_datadictionary.id}")
        assert response.status_code == 403
        assert DataDictionary.get(basic_datadictionary.id) is not None
    finally:
        test_owner.cleanup()


def test_dd_delete_missing_dd_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.delete("/api/DataDictionary/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_dd_table_delete(client, basic_study, basic_datadictionary, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_datadictionary)
        response = client.delete(
            f"/api/DataDictionary/{basic_datadictionary.id}/Table/{basic_table.id}"
        )
        assert response.status_code == 200
        assert response.json["tables"] == []
    finally:
        test_owner.cleanup()


def test_dd_table_delete_requires_write_access(
    client, basic_study, basic_datadictionary, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.delete(
            f"/api/DataDictionary/{basic_datadictionary.id}/Table/{basic_table.id}"
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_dd_table_delete_missing_dd_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.delete("/api/DataDictionary/not-there/Table/some-table")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


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
    # Documents current behavior: DataDictionaryHarmony is out of scope for
    # Phase 5 (M11 aggregate endpoint, same as HarmonyTableCSV/StudyHarmony)
    # and still does not check for a None result before calling
    # .as_harmony() on it.
    with pytest.raises(AttributeError):
        client.get("/api/DataDictionary/not-there/harmony")
