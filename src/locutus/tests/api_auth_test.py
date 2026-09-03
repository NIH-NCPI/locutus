"""
Coverage for POST /api/auth/google (Auth Requirements spec, M1 Path A / S3).
google.oauth2.id_token.verify_oauth2_token is mocked -- there's no way to
get a real Google-signed token in a test, so every scenario is driven by
controlling what claims verification would have returned, matching this
project's existing convention of mocking the one genuinely external call
(see api_ontology_search_test.py's run_search mock) rather than the
handler logic around it.
"""

from unittest.mock import patch

import locutus
from locutus.model.institution import Institution
from locutus.model.user import User

from . import client


def _claims(
    sub="google-sub-1",
    email="new-user@example.com",
    email_verified=True,
    name="Test User",
):
    return {
        "sub": sub,
        "email": email,
        "email_verified": email_verified,
        "name": name,
        "iss": "https://accounts.google.com",
    }


def _clear_users():
    for doc in locutus.persistence().collection("User").stream():
        locutus.persistence().collection("User").document(doc.id).delete()


def _clear_institutions():
    for doc in locutus.persistence().collection("Institution").stream():
        locutus.persistence().collection("Institution").document(doc.id).delete()


def _clear_bootstrap_config():
    locutus.persistence().collection("Config").document("bootstrap").delete()


def test_missing_credential_returns_400(client):
    response = client.post("/api/auth/google", json={})
    assert response.status_code == 400


def test_missing_google_client_id_returns_500(client, monkeypatch):
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    response = client.post("/api/auth/google", json={"credential": "irrelevant"})
    assert response.status_code == 500


def test_invalid_credential_returns_401(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    with patch(
        "locutus.api.auth.id_token.verify_oauth2_token",
        side_effect=ValueError("bad token"),
    ):
        response = client.post("/api/auth/google", json={"credential": "bad"})
    assert response.status_code == 401


def test_unverified_email_returns_401(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    with patch(
        "locutus.api.auth.id_token.verify_oauth2_token",
        return_value=_claims(email_verified=False),
    ):
        response = client.post("/api/auth/google", json={"credential": "tok"})
    assert response.status_code == 401


def test_unprovisioned_email_returns_403_and_creates_no_user(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    _clear_users()
    try:
        with patch(
            "locutus.api.auth.id_token.verify_oauth2_token",
            return_value=_claims(email="nobody-provisioned@example.com"),
        ):
            response = client.post("/api/auth/google", json={"credential": "tok"})
        assert response.status_code == 403
        assert User.find_by_email("nobody-provisioned@example.com") is None
    finally:
        _clear_users()


def test_institution_allowlist_match_creates_user_with_institution(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    _clear_users()
    _clear_institutions()
    try:
        inst = Institution(name="VUMC", allowed_emails=["allowed@vumc.org"]).save()

        with patch(
            "locutus.api.auth.id_token.verify_oauth2_token",
            return_value=_claims(
                sub="sub-vumc-user", email="allowed@vumc.org", name="Allowed User"
            ),
        ):
            response = client.post("/api/auth/google", json={"credential": "tok"})

        assert response.status_code == 200
        assert response.json["email"] == "allowed@vumc.org"
        assert response.json["role"] == "user"
        assert response.json["institutionIds"] == [inst.id]

        created = User.find_by_email("allowed@vumc.org")
        assert created is not None
        assert created.google_sub == "sub-vumc-user"
        assert created.display_name == "Allowed User"
        assert created.institution_ids == [inst.id]
        assert created.role == "user"

        with client.session_transaction() as sess:
            assert sess["user_id"] == created.id
    finally:
        _clear_users()
        _clear_institutions()


def test_bootstrap_admin_email_creates_admin_user(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    _clear_users()
    try:
        locutus.persistence().collection("Config").document("bootstrap").set(
            {"adminEmails": ["admin@example.com"]}
        )

        with patch(
            "locutus.api.auth.id_token.verify_oauth2_token",
            return_value=_claims(sub="sub-admin", email="admin@example.com"),
        ):
            response = client.post("/api/auth/google", json={"credential": "tok"})

        assert response.status_code == 200
        assert response.json["role"] == "admin"

        created = User.find_by_email("admin@example.com")
        assert created is not None
        assert created.role == "admin"
        # An admin match doesn't imply institution membership -- those are
        # independent dimensions.
        assert created.institution_ids == []
    finally:
        _clear_users()
        _clear_bootstrap_config()


def test_returning_user_found_by_google_sub(client, monkeypatch):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    _clear_users()
    try:
        existing = User(
            email="returning@example.com",
            google_sub="sub-returning",
            institution_ids=["vumc"],
        ).save()

        with patch(
            "locutus.api.auth.id_token.verify_oauth2_token",
            return_value=_claims(sub="sub-returning", email="returning@example.com"),
        ):
            response = client.post("/api/auth/google", json={"credential": "tok"})

        assert response.status_code == 200
        assert response.json["user_id"] == existing.id
        assert response.json["institutionIds"] == ["vumc"]

        # No duplicate user created for the same google_sub.
        assert len(list(locutus.persistence().collection("User").stream())) == 1
    finally:
        _clear_users()


def test_existing_email_only_account_gets_linked_to_google_sub(client, monkeypatch):
    """An account created some other way (e.g. seeded directly) that has no
    google_sub yet must be linked on first Google login, not treated as
    unprovisioned or duplicated."""
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    _clear_users()
    try:
        existing = User(email="pre-seeded@example.com", institution_ids=["chop"]).save()
        assert existing.google_sub is None

        with patch(
            "locutus.api.auth.id_token.verify_oauth2_token",
            return_value=_claims(
                sub="sub-newly-linked", email="pre-seeded@example.com"
            ),
        ):
            response = client.post("/api/auth/google", json={"credential": "tok"})

        assert response.status_code == 200
        assert response.json["user_id"] == existing.id

        relinked = User.find_by_google_sub("sub-newly-linked")
        assert relinked is not None
        assert relinked.id == existing.id
    finally:
        _clear_users()
