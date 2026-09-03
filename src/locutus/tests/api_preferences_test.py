from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_user_pref_onto_filters_get(client):
    # No auth model change here -- UserPrefOntoFilters is a global,
    # user-preference-shaped endpoint with no resource id to gate on, and is
    # deliberately reachable without a session (see the fallback below).
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


def test_table_prefs_requires_auth(client, sample_terminology, basic_table):
    response = client.get(f"/api/Table/{basic_table.id}/filter")
    assert response.status_code == 401


def test_table_prefs_post_put_get_table_level(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
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
    finally:
        test_owner.cleanup()


def test_table_prefs_post_missing_api_preference(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = client.post(
            f"/api/Table/{basic_table.id}/filter",
            json={},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_prefs_delete(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        client.post(
            f"/api/Table/{basic_table.id}/filter",
            json={"api_preference": {"ols": ["mondo"]}},
            headers={"Content-Type": "application/json"},
        )

        response = client.delete(f"/api/Table/{basic_table.id}/filter")
        assert response.status_code == 200

        response = client.get(f"/api/Table/{basic_table.id}/filter")
        assert response.json["self"]["api_preference"] == {}
    finally:
        test_owner.cleanup()


def test_table_prefs_code_level(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = client.post(
            f"/api/Table/{basic_table.id}/filter/string_var",
            json={"api_preference": {"ols": ["hp"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        response = client.get(f"/api/Table/{basic_table.id}/filter/string_var")
        assert response.status_code == 200
        assert response.json["string_var"]["api_preference"]["ols"] == ["hp"]
    finally:
        test_owner.cleanup()


def test_table_prefs_get_missing_table_returns_404(client):
    # require_read_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table/not-there/filter")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_prefs_requires_write_access(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.post(
            f"/api/Table/{basic_table.id}/filter",
            json={"api_preference": {"ols": ["mondo"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_put_get_delete(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
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
        assert response.json["references"] == [
            {"reference": "Terminology/ontology-one"}
        ]

        response = client.delete(f"/api/Table/{basic_table.id}/preferred_terminology")
        assert response.status_code == 200

        response = client.get(f"/api/Table/{basic_table.id}/preferred_terminology")
        assert response.json["references"] == []
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_put_missing_editor(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            f"/api/Table/{basic_table.id}/preferred_terminology",
            json={
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}]
            },
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_put_invalid_shape(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = client.put(
            f"/api/Table/{basic_table.id}/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"wrong_key": "x"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_get_missing_table(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table/not-there/preferred_terminology")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_put_missing_table_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.put(
            "/api/Table/not-there/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_preferred_terminology_requires_write_access(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.put(
            f"/api/Table/{basic_table.id}/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_terminology_prefs_post_put_get(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
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
    finally:
        test_owner.cleanup()


def test_terminology_prefs_post_code_level(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.post(
            "/api/Terminology/ontology-one/filter/C1",
            json={"api_preference": {"ols": ["hp"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        response = client.get("/api/Terminology/ontology-one/filter/C1")
        assert response.json["C1"]["api_preference"]["ols"] == ["hp"]
    finally:
        test_owner.cleanup()


def test_terminology_prefs_post_code_not_present(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.post(
            "/api/Terminology/ontology-one/filter/does-not-exist",
            json={"api_preference": {"ols": ["hp"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_prefs_get_missing_terminology(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Terminology/not-there/filter")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_prefs_post_missing_terminology_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.post(
            "/api/Terminology/not-there/filter",
            json={"api_preference": {"ols": ["mondo"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_prefs_requires_write_access(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        response = client.post(
            "/api/Terminology/ontology-one/filter",
            json={"api_preference": {"ols": ["mondo"]}},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


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
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        test_owner.own(basic_table)
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
    finally:
        test_owner.cleanup()


def test_terminology_preferred_terminology_put_get_delete(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
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
        assert response.json["references"] == [
            {"reference": "Terminology/ontology-one"}
        ]

        response = client.delete("/api/Terminology/ontology-one/preferred_terminology")
        assert response.status_code == 200

        response = client.get("/api/Terminology/ontology-one/preferred_terminology")
        assert response.json["references"] == []
    finally:
        test_owner.cleanup()


def test_terminology_preferred_terminology_get_missing_terminology(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Terminology/not-there/preferred_terminology")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_preferred_terminology_put_missing_terminology_returns_404(
    client,
):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.put(
            "/api/Terminology/not-there/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_preferred_terminology_requires_write_access(
    client, sample_terminology
):
    test_owner = _Owner(client)
    try:
        response = client.put(
            "/api/Terminology/ontology-one/preferred_terminology",
            json={
                "editor": "unit-test",
                "preferred_terminologies": [{"preferred_terminology": "ontology-one"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_terminology_preferred_terminology_get_falls_back_to_table(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        test_owner.own(basic_table)
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
        assert response.json["references"] == [
            {"reference": "Terminology/ontology-one"}
        ]
    finally:
        test_owner.cleanup()
