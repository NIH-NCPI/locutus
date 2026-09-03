from datetime import UTC, datetime, timedelta

import locutus
from locutus.auth import TOKEN_PREFIX, hash_token
from locutus.model.api_token import ApiToken


def _clear():
    for doc in locutus.persistence().collection("ApiToken").stream():
        locutus.persistence().collection("ApiToken").document(doc.id).delete()


def test_create_returns_model_and_plaintext_matching_the_stored_hash():
    _clear()

    try:
        token, raw = ApiToken.create(user_id="u1", name="laptop")
        assert raw.startswith(TOKEN_PREFIX)
        assert token.id is not None
        assert token.user_id == "u1"
        assert token.name == "laptop"
        assert token.expires_at is None

        # The plaintext returned here is the only copy that will ever
        # exist -- confirm what's actually stored is only its hash, and
        # that hash matches what a real lookup would compute.
        stored = locutus.persistence().get_api_token(hash_token(raw))
        assert stored is not None
        assert stored["id"] == token.id
        assert "token" not in stored
    finally:
        _clear()


def test_create_with_expiry():
    _clear()

    try:
        expires_at = datetime.now(UTC) + timedelta(days=30)
        token, _ = ApiToken.create(user_id="u1", name="ci-bot", expires_at=expires_at)
        assert token.expires_at == expires_at
    finally:
        _clear()


def test_get_found_and_not_found():
    _clear()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        fetched = ApiToken.get(token.id)
        assert fetched is not None
        assert fetched.name == "laptop"

        assert ApiToken.get("does-not-exist") is None
    finally:
        _clear()


def test_list_for_user_only_returns_that_users_tokens():
    _clear()

    try:
        ApiToken.create(user_id="u1", name="u1-laptop")
        ApiToken.create(user_id="u1", name="u1-ci")
        ApiToken.create(user_id="u2", name="u2-laptop")

        u1_tokens = ApiToken.list_for_user("u1")
        assert sorted(t.name for t in u1_tokens if t.name is not None) == [
            "u1-ci",
            "u1-laptop",
        ]

        u2_tokens = ApiToken.list_for_user("u2")
        assert [t.name for t in u2_tokens] == ["u2-laptop"]

        assert ApiToken.list_for_user("u3-has-none") == []
    finally:
        _clear()


def test_delete_by_owner_succeeds():
    _clear()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.delete(token.id, "u1") is True
        assert ApiToken.get(token.id) is None
    finally:
        _clear()


def test_delete_by_non_owner_fails_and_leaves_token_intact():
    _clear()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.delete(token.id, "u2") is False
        assert ApiToken.get(token.id) is not None
    finally:
        _clear()


def test_delete_missing_token_returns_false():
    assert ApiToken.delete("does-not-exist", "u1") is False


def test_admin_delete_ignores_ownership():
    _clear()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.admin_delete(token.id) is True
        assert ApiToken.get(token.id) is None
    finally:
        _clear()


def test_admin_delete_missing_token_returns_false():
    assert ApiToken.admin_delete("does-not-exist") is False
