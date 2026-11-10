from datetime import UTC, datetime, timedelta

import locutus
from locutus.auth import TOKEN_PREFIX, hash_token
from locutus.model.api_token import ApiToken
from locutus.model.audit_event import AuditEvent


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


def _clear_audit():
    for doc in locutus.persistence().collection("AuditEvent").stream():
        locutus.persistence().collection("AuditEvent").document(doc.id).delete()


def test_revoke_by_owner_marks_token_revoked_and_keeps_it():
    _clear()
    _clear_audit()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.revoke(token.id, "u1") is True
        revoked = ApiToken.get(token.id)
        assert revoked is not None
        assert revoked.revoked_at is not None
        assert revoked.revoked_by == "u1"

        # Hidden from the owner's own list; still visible to an admin.
        assert ApiToken.list_for_user("u1") == []
        assert len(ApiToken.list_for_user("u1", include_revoked=True)) == 1

        [event] = AuditEvent.find(user_id="u1")
        assert event.action == AuditEvent.Action.TokenRevoke
        assert event.actor_id == event.target_user_id == "u1"
        assert event.target_token_ids == [token.id]
    finally:
        _clear()
        _clear_audit()


def test_revoke_twice_returns_false():
    _clear()
    _clear_audit()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.revoke(token.id, "u1") is True
        assert ApiToken.revoke(token.id, "u1") is False
    finally:
        _clear()
        _clear_audit()


def test_revoke_by_non_owner_fails_and_leaves_token_intact():
    _clear()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.revoke(token.id, "u2") is False
        fetched = ApiToken.get(token.id)
        assert fetched is not None
        assert fetched.revoked_at is None
    finally:
        _clear()


def test_revoke_missing_token_returns_false():
    assert ApiToken.revoke("does-not-exist", "u1") is False


def test_admin_revoke_ignores_ownership_and_records_reason():
    _clear()
    _clear_audit()

    try:
        token, _ = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.admin_revoke(token.id, "admin1", "found in a log") is True
        fetched = ApiToken.get(token.id)
        assert fetched is not None
        assert fetched.revoked_by == "admin1"
        assert fetched.revoke_reason == "found in a log"

        [event] = AuditEvent.find(user_id="u1")
        assert event.actor_id == "admin1"
        assert event.reason == "found in a log"
    finally:
        _clear()
        _clear_audit()


def test_admin_revoke_missing_token_returns_false():
    assert ApiToken.admin_revoke("does-not-exist", "admin1") is False


def test_admin_revoke_all_only_touches_that_users_active_tokens():
    _clear()
    _clear_audit()

    try:
        a, _ = ApiToken.create(user_id="u1", name="a")
        b, _ = ApiToken.create(user_id="u1", name="b")
        already, _ = ApiToken.create(user_id="u1", name="already-revoked")
        other, _ = ApiToken.create(user_id="u2", name="other")
        assert a.id is not None and b.id is not None
        assert already.id is not None and other.id is not None
        ApiToken.revoke(already.id, "u1")

        revoked = ApiToken.admin_revoke_all("u1", "admin1")
        assert sorted(revoked) == sorted([a.id, b.id])
        assert ApiToken.list_for_user("u1") == []
        assert len(ApiToken.list_for_user("u2")) == 1

        [event] = AuditEvent.find(action=AuditEvent.Action.TokenRevokeAll)
        assert sorted(event.target_token_ids) == sorted(revoked)
    finally:
        _clear()
        _clear_audit()


def test_revoke_by_value():
    _clear()
    _clear_audit()

    try:
        token, raw = ApiToken.create(user_id="u1", name="laptop")
        assert token.id is not None

        assert ApiToken.revoke_by_value(raw, "finder") is True
        fetched = ApiToken.get(token.id)
        assert fetched is not None
        assert fetched.revoked_by == "finder"

        # Already revoked, and a value that was never a token.
        assert ApiToken.revoke_by_value(raw, "finder") is False
        assert ApiToken.revoke_by_value("lct_not-a-real-token", "finder") is False

        [event] = AuditEvent.find(user_id="u1")
        assert event.action == AuditEvent.Action.TokenRevokeByValue
        assert event.actor_id == "finder"
    finally:
        _clear()
        _clear_audit()
