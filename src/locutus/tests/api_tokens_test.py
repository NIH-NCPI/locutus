"""
Coverage for /api/tokens and /api/admin/tokens/<id> (Auth Requirements
spec, M9), exercised end-to-end against the real Flask app via session
cookies -- no mocking needed here, unlike api_auth_test.py, since nothing
external is involved.
"""

import locutus
from locutus.model.api_token import ApiToken
from locutus.model.user import User

from . import client


def _clear_users():
    for doc in locutus.persistence().collection("User").stream():
        locutus.persistence().collection("User").document(doc.id).delete()


def _clear_tokens():
    for doc in locutus.persistence().collection("ApiToken").stream():
        locutus.persistence().collection("ApiToken").document(doc.id).delete()


def _login_as(client, user_id):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id


def test_post_requires_auth(client):
    response = client.post("/api/tokens", json={"name": "laptop"})
    assert response.status_code == 401


def test_post_rejects_api_token_credential(client):
    """interactive_only=True -- a token must not be able to mint another
    token to extend its own access."""
    _clear_users()
    _clear_tokens()
    try:
        user = User(email="token-creator@example.com").save()
        assert user.id is not None
        _, raw = ApiToken.create(user_id=user.id, name="existing-token")

        response = client.post(
            "/api/tokens",
            json={"name": "new-token"},
            headers={"Authorization": f"Bearer {raw}"},
        )
        assert response.status_code == 403
    finally:
        _clear_users()
        _clear_tokens()


def test_post_missing_name_returns_400(client):
    _clear_users()
    try:
        user = User(email="post-missing-name@example.com").save()
        _login_as(client, user.id)

        response = client.post("/api/tokens", json={})
        assert response.status_code == 400
    finally:
        _clear_users()


def test_post_invalid_expires_at_returns_400(client):
    _clear_users()
    try:
        user = User(email="post-bad-expiry@example.com").save()
        _login_as(client, user.id)

        response = client.post(
            "/api/tokens", json={"name": "laptop", "expiresAt": "not-a-date"}
        )
        assert response.status_code == 400
    finally:
        _clear_users()


def test_post_creates_token_and_returns_plaintext_once(client):
    _clear_users()
    _clear_tokens()
    try:
        user = User(email="post-creates@example.com").save()
        assert user.id is not None
        _login_as(client, user.id)

        response = client.post("/api/tokens", json={"name": "laptop"})
        assert response.status_code == 200
        assert response.json["token"].startswith("lct_")
        assert response.json["tokenId"] is not None

        tokens = ApiToken.list_for_user(user.id)
        assert len(tokens) == 1
        assert tokens[0].name == "laptop"
    finally:
        _clear_users()
        _clear_tokens()


def test_get_requires_auth(client):
    response = client.get("/api/tokens")
    assert response.status_code == 401


def test_get_only_lists_callers_own_tokens_without_secrets(client):
    _clear_users()
    _clear_tokens()
    try:
        user_a = User(email="list-a@example.com").save()
        user_b = User(email="list-b@example.com").save()
        assert user_a.id is not None and user_b.id is not None
        ApiToken.create(user_id=user_a.id, name="a-token")
        ApiToken.create(user_id=user_b.id, name="b-token")

        _login_as(client, user_a.id)
        response = client.get("/api/tokens")

        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]["name"] == "a-token"
        assert "tokenHash" not in response.json[0]
        assert "token" not in response.json[0]
    finally:
        _clear_users()
        _clear_tokens()


def test_get_works_with_api_token_credential(client):
    """Unlike POST, listing isn't interactive-only."""
    _clear_users()
    _clear_tokens()
    try:
        user = User(email="list-via-token@example.com").save()
        assert user.id is not None
        _, raw = ApiToken.create(user_id=user.id, name="laptop")

        response = client.get("/api/tokens", headers={"Authorization": f"Bearer {raw}"})
        assert response.status_code == 200
        assert len(response.json) == 1
    finally:
        _clear_users()
        _clear_tokens()


def test_delete_requires_auth(client):
    response = client.delete("/api/tokens/some-id")
    assert response.status_code == 401


def test_delete_owner_revokes_own_token(client):
    _clear_users()
    _clear_tokens()
    try:
        user = User(email="delete-owner@example.com").save()
        assert user.id is not None
        token, _ = ApiToken.create(user_id=user.id, name="laptop")
        assert token.id is not None
        _login_as(client, user.id)

        response = client.delete(f"/api/tokens/{token.id}")
        assert response.status_code == 200
        assert ApiToken.get(token.id) is None
    finally:
        _clear_users()
        _clear_tokens()


def test_delete_non_owner_gets_404_and_token_survives(client):
    _clear_users()
    _clear_tokens()
    try:
        owner = User(email="delete-real-owner@example.com").save()
        other = User(email="delete-not-owner@example.com").save()
        assert owner.id is not None and other.id is not None
        token, _ = ApiToken.create(user_id=owner.id, name="laptop")
        assert token.id is not None
        _login_as(client, other.id)

        response = client.delete(f"/api/tokens/{token.id}")
        assert response.status_code == 404
        assert ApiToken.get(token.id) is not None
    finally:
        _clear_users()
        _clear_tokens()


def test_admin_delete_requires_admin(client):
    _clear_users()
    _clear_tokens()
    try:
        owner = User(email="admin-del-owner@example.com").save()
        non_admin = User(email="admin-del-non-admin@example.com").save()
        assert owner.id is not None and non_admin.id is not None
        token, _ = ApiToken.create(user_id=owner.id, name="laptop")
        assert token.id is not None
        _login_as(client, non_admin.id)

        response = client.delete(f"/api/admin/tokens/{token.id}")
        assert response.status_code == 403
        assert ApiToken.get(token.id) is not None
    finally:
        _clear_users()
        _clear_tokens()


def test_admin_delete_revokes_any_users_token(client):
    _clear_users()
    _clear_tokens()
    try:
        owner = User(email="admin-del-target@example.com").save()
        admin = User(email="admin-del-admin@example.com", role=User.Role.Admin).save()
        assert owner.id is not None and admin.id is not None
        token, _ = ApiToken.create(user_id=owner.id, name="laptop")
        assert token.id is not None
        _login_as(client, admin.id)

        response = client.delete(f"/api/admin/tokens/{token.id}")
        assert response.status_code == 200
        assert ApiToken.get(token.id) is None
    finally:
        _clear_users()
        _clear_tokens()
