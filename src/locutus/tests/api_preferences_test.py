import pytest

from . import client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_user_pref_onto_filters_get(client):
    # Documents current behavior: with no active session and no editor, the
    # "Application Default" fallback in UserPrefOntoFilters.get is
    # unreachable, since SessionManager.create_user_id returns None quietly
    # rather than raising. The response ends up keyed by "null" (JSON's
    # rendering of a None dict key) instead.
    response = client.get("/api/user/preferences/ontologies")
    assert response.status_code == 200
    body = response.json
    assert "Application Default" not in body
    assert body["null"]["api_preference"]["ols"] == ["mondo", "hp", "maxo", "ncit"]


def test_table_prefs_post_put_get_table_level(client, sample_terminology, basic_table):
    response = client.post(
        f"/api/Table/{basic_table.id}/filter",
        json={"api_preference": {"ols": ["mondo"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/filter")
    assert response.status_code == 200
    assert response.json["self"]["api_preference"]["ols"] == ["mondo"]

    response = client.put(
        f"/api/Table/{basic_table.id}/filter",
        json={"api_preference": {"ols": ["hp"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/filter")
    assert response.json["self"]["api_preference"]["ols"] == ["hp"]


def test_table_prefs_post_missing_api_preference(
    client, sample_terminology, basic_table
):
    response = client.post(
        f"/api/Table/{basic_table.id}/filter",
        json={},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_prefs_delete(client, sample_terminology, basic_table):
    client.post(
        f"/api/Table/{basic_table.id}/filter",
        json={"api_preference": {"ols": ["mondo"]}},
        headers={"Content-Type": "application/json"},
    )

    response = client.delete(f"/api/Table/{basic_table.id}/filter")
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/filter")
    assert response.json["self"]["api_preference"] == {}


def test_table_prefs_code_level(client, sample_terminology, basic_table):
    response = client.post(
        f"/api/Table/{basic_table.id}/filter/string_var",
        json={"api_preference": {"ols": ["hp"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/filter/string_var")
    assert response.status_code == 200
    assert response.json["string_var"]["api_preference"]["ols"] == ["hp"]


def test_table_prefs_get_missing_table_raises(client):
    # Documents current behavior: TableOntologyAPISearchPreferences.get does
    # not check for a None Table before calling .get_preference() on it.
    with pytest.raises(AttributeError):
        client.get("/api/Table/not-there/filter")


def test_table_preferred_terminology_put_get_delete(
    client, sample_terminology, basic_table
):
    response = client.put(
        f"/api/Table/{basic_table.id}/preferred_terminology",
        json={
            "editor": "unit-test",
            "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
        },
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/preferred_terminology")
    assert response.status_code == 200
    assert response.json["references"] == [{"reference": "Terminology/ontology-one"}]

    response = client.delete(f"/api/Table/{basic_table.id}/preferred_terminology")
    assert response.status_code == 200

    response = client.get(f"/api/Table/{basic_table.id}/preferred_terminology")
    assert response.json["references"] == []


def test_table_preferred_terminology_put_missing_editor(
    client, sample_terminology, basic_table
):
    response = client.put(
        f"/api/Table/{basic_table.id}/preferred_terminology",
        json={"preferred_terminologies": [{"preferred_terminology": "ontology-one"}]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_preferred_terminology_put_invalid_shape(
    client, sample_terminology, basic_table
):
    response = client.put(
        f"/api/Table/{basic_table.id}/preferred_terminology",
        json={"editor": "unit-test", "preferred_terminologies": [{"wrong_key": "x"}]},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_preferred_terminology_get_missing_table(client):
    response = client.get("/api/Table/not-there/preferred_terminology")
    assert response.status_code == 404


def test_table_preferred_terminology_put_missing_table_raises(client):
    # Documents current behavior: unlike its own .get, TablePreferredTerminology.put
    # does not check for a None Table before calling .replace_preferred_terminology().
    with pytest.raises(AttributeError):
        client.put(
            "/api/Table/not-there/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )


def test_terminology_prefs_post_put_get(client, sample_terminology):
    response = client.post(
        "/api/Terminology/ontology-one/filter",
        json={"api_preference": {"ols": ["mondo"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/filter")
    assert response.json["self"]["api_preference"]["ols"] == ["mondo"]

    response = client.put(
        "/api/Terminology/ontology-one/filter",
        json={"api_preference": {"ols": ["hp"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/filter")
    assert response.json["self"]["api_preference"]["ols"] == ["hp"]

    response = client.delete("/api/Terminology/ontology-one/filter")
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/filter")
    assert response.json["self"]["api_preference"] == {}


def test_terminology_prefs_post_code_level(client, sample_terminology):
    response = client.post(
        "/api/Terminology/ontology-one/filter/C1",
        json={"api_preference": {"ols": ["hp"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/filter/C1")
    assert response.json["C1"]["api_preference"]["ols"] == ["hp"]


def test_terminology_prefs_post_code_not_present(client, sample_terminology):
    response = client.post(
        "/api/Terminology/ontology-one/filter/does-not-exist",
        json={"api_preference": {"ols": ["hp"]}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404


def test_terminology_prefs_get_missing_terminology(client):
    response = client.get("/api/Terminology/not-there/filter")
    assert response.status_code == 404


def test_terminology_prefs_post_missing_terminology_raises(client):
    # Documents current behavior: unlike its own .get, the .post/.put/.delete
    # methods on OntologyAPISearchPreferences don't check for a None Terminology.
    with pytest.raises(AttributeError):
        client.post(
            "/api/Terminology/not-there/filter",
            json={"api_preference": {"ols": ["mondo"]}},
            headers={"Content-Type": "application/json"},
        )


def test_terminology_prefs_get_table_fallback_never_triggers(
    client, sample_terminology, basic_table
):
    # Documents current behavior: the fallback condition is
    # `if table_id and not any(pref.values())`. For OntologyAPISearchPreferences,
    # pref's values are always a dict shaped like {"api_preference": {...}},
    # which is truthy even when empty -- so `any(pref.values())` is always
    # True and the table fallback can never actually trigger, unlike the
    # equivalent-looking check in PreferredTerminology.get (where the value
    # being checked is a list, correctly falsy when empty). Passing table_id
    # here has no effect; the terminology's own (empty) prefs are returned.
    client.post(
        f"/api/Table/{basic_table.id}/filter",
        json={"api_preference": {"ols": ["from-table"]}},
        headers={"Content-Type": "application/json"},
    )

    response = client.get(
        "/api/Terminology/ontology-one/filter",
        query_string={"table_id": basic_table.id},
    )
    assert response.status_code == 200
    assert response.json["self"]["api_preference"] == {}


def test_terminology_preferred_terminology_put_get_delete(client, sample_terminology):
    response = client.put(
        "/api/Terminology/ontology-one/preferred_terminology",
        json={
            "editor": "unit-test",
            "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
        },
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/preferred_terminology")
    assert response.json["references"] == [{"reference": "Terminology/ontology-one"}]

    response = client.delete("/api/Terminology/ontology-one/preferred_terminology")
    assert response.status_code == 200

    response = client.get("/api/Terminology/ontology-one/preferred_terminology")
    assert response.json["references"] == []


def test_terminology_preferred_terminology_get_missing_terminology(client):
    response = client.get("/api/Terminology/not-there/preferred_terminology")
    assert response.status_code == 404


def test_terminology_preferred_terminology_put_missing_terminology_raises(client):
    # Documents current behavior: unlike its own .get, PreferredTerminology.put
    # does not check for a None Terminology before calling
    # .replace_preferred_terminology() on it.
    with pytest.raises(AttributeError):
        client.put(
            "/api/Terminology/not-there/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )


def test_terminology_preferred_terminology_get_falls_back_to_table(
    client, sample_terminology, basic_table
):
    client.put(
        f"/api/Table/{basic_table.id}/preferred_terminology",
        json={
            "editor": "unit-test",
            "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
        },
        headers={"Content-Type": "application/json"},
    )

    response = client.get(
        "/api/Terminology/ontology-one/preferred_terminology",
        query_string={"table_id": basic_table.id},
    )
    assert response.status_code == 200
    assert response.json["references"] == [{"reference": "Terminology/ontology-one"}]
