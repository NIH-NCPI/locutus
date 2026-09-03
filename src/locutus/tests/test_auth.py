"""
Coverage for locutus/auth.py (Auth Requirements spec, M6) -- the decorators
and permission logic that will gate every route from Phase 5 onward. This
is the security-critical piece of the whole auth effort, so get_permission
is tested directly against the full access matrix, and each decorator is
tested end-to-end against real Flask routes and real saved documents (not
mocks), matching this project's existing convention of testing against the
live mongo test harness.
"""

import secrets
from datetime import UTC, datetime, timedelta

import pytest
from flask import Flask, g

import locutus
from locutus.auth import (
    CurrentUser,
    get_permission,
    hash_token,
    require_admin,
    require_auth,
    require_read_access,
    require_write_access,
)
from locutus.model.study import Study
from locutus.model.user import User
from locutus.model.visibility import Visibility
from locutus.sessions import SessionManager

# ── get_permission() -- the full access matrix, tested in isolation ─────


def _resource(owner_id=None, visibility=None, institutions=None, users=None):
    return {
        "owner_id": owner_id,
        "visibility": visibility,
        "access": {
            "institutions": institutions or {},
            "users": users or {},
        },
    }


def _user(user_id="u1", institution_ids=None, role="user") -> CurrentUser:
    return {"user_id": user_id, "institutionIds": institution_ids or [], "role": role}


def test_owner_gets_editor_regardless_of_visibility():
    resource = _resource(owner_id="u1", visibility=Visibility.Restricted)
    assert get_permission(resource, _user()) == "editor"


def test_institution_visibility_with_overlap():
    resource = _resource(
        owner_id="someone-else",
        visibility=Visibility.Institution,
        institutions={"vumc": "editor"},
    )
    assert get_permission(resource, _user(institution_ids=["vumc"])) == "editor"


def test_institution_visibility_without_overlap():
    resource = _resource(
        owner_id="someone-else",
        visibility=Visibility.Institution,
        institutions={"vumc": "editor"},
    )
    assert get_permission(resource, _user(institution_ids=["chop"])) is None


def test_institution_visibility_honors_stored_role_value():
    """Data model already supports viewer-role institutions (C1) even
    though nothing sets that value yet -- get_permission must honor
    whatever role is actually stored, not assume "editor"."""
    resource = _resource(
        owner_id="someone-else",
        visibility=Visibility.Institution,
        institutions={"vumc": "viewer"},
    )
    assert get_permission(resource, _user(institution_ids=["vumc"])) == "viewer"


def test_restricted_visibility_with_explicit_grant():
    resource = _resource(
        owner_id="someone-else",
        visibility=Visibility.Restricted,
        users={"u1": "editor"},
    )
    assert get_permission(resource, _user(user_id="u1")) == "editor"


def test_restricted_visibility_without_explicit_grant():
    resource = _resource(owner_id="someone-else", visibility=Visibility.Restricted)
    assert get_permission(resource, _user(institution_ids=["vumc"])) is None


def test_restricted_visibility_ignores_institution_membership():
    """Restricted means access.users only -- institution overlap must not
    grant access here, unlike Institution visibility."""
    resource = _resource(
        owner_id="someone-else",
        visibility=Visibility.Restricted,
        institutions={"vumc": "editor"},
    )
    assert get_permission(resource, _user(institution_ids=["vumc"])) is None


def test_registered_visibility_gives_any_authenticated_user_viewer():
    resource = _resource(owner_id="someone-else", visibility=Visibility.Registered)
    assert get_permission(resource, _user()) == "viewer"


def test_public_visibility_currently_behaves_like_registered():
    """Public isn't enforced yet (W3) -- every caller already authenticated
    to reach get_permission at all, so it's viewer, same as Registered."""
    resource = _resource(owner_id="someone-else", visibility=Visibility.Public)
    assert get_permission(resource, _user()) == "viewer"


def test_missing_visibility_key_treated_as_registered():
    """A document saved before M4 has no visibility key at all."""
    resource = {"owner_id": "someone-else", "access": {"institutions": {}, "users": {}}}
    assert get_permission(resource, _user()) == "viewer"


# ── Decorators, end-to-end against real routes and real documents ───────


@pytest.fixture
def auth_app():
    app = Flask(__name__)
    SessionManager(app)

    @app.route("/probe/auth")
    @require_auth
    def probe_auth():
        return {"user_id": g.current_user["user_id"]}, 200

    @app.route("/probe/auth-interactive")
    @require_auth(interactive_only=True)
    def probe_auth_interactive():
        return {"user_id": g.current_user["user_id"]}, 200

    @app.route("/probe/admin")
    @require_admin
    def probe_admin():
        return {"user_id": g.current_user["user_id"]}, 200

    @app.route("/probe/read/<id>")
    @require_read_access("Study", "id")
    def probe_read(id):
        return {"ok": True}, 200

    @app.route("/probe/write/<id>")
    @require_write_access("Study", "id")
    def probe_write(id):
        return {"ok": True}, 200

    with app.test_client() as client:
        yield client

    # Each session_transaction() in these tests writes a real MongoDB-backed
    # session document (M10) -- clean up so they don't leak into other
    # tests (e.g. test_sessions.py's exact-count assertions).
    db = locutus.persistence()
    db.client[db.db_name]["sessions"].delete_many({})


@pytest.fixture
def basic_user():
    user = User(email="auth-basic@example.com", institution_ids=["vumc"]).save()
    yield user
    assert user.id is not None
    user.delete()


@pytest.fixture
def admin_user():
    user = User(email="auth-admin@example.com", role=User.Role.Admin).save()
    yield user
    assert user.id is not None
    user.delete()


def _make_token(user_id: str, expires_at: datetime | None = None):
    raw = "lct_" + secrets.token_hex(16)
    locutus.persistence().create_api_token(
        {
            "userId": user_id,
            "tokenHash": hash_token(raw),
            "name": "test-token",
            "createdAt": datetime.now(UTC),
            "lastUsedAt": None,
            "expiresAt": expires_at,
        }
    )
    return raw


def _clear_api_tokens():
    for doc in locutus.persistence().collection("ApiToken").stream():
        locutus.persistence().collection("ApiToken").document(doc.id).delete()


def test_require_auth_rejects_no_credential(auth_app):
    response = auth_app.get("/probe/auth")
    assert response.status_code == 401


def test_require_auth_accepts_valid_session(auth_app, basic_user):
    assert basic_user.id is not None
    with auth_app.session_transaction() as sess:
        sess["user_id"] = basic_user.id

    response = auth_app.get("/probe/auth")
    assert response.status_code == 200
    assert response.json["user_id"] == basic_user.id


def test_require_auth_rejects_session_for_deleted_user(auth_app):
    with auth_app.session_transaction() as sess:
        sess["user_id"] = "does-not-exist"

    response = auth_app.get("/probe/auth")
    assert response.status_code == 401


def test_require_auth_accepts_valid_api_token(auth_app, basic_user):
    assert basic_user.id is not None
    token = _make_token(basic_user.id)
    try:
        response = auth_app.get(
            "/probe/auth", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json["user_id"] == basic_user.id
    finally:
        _clear_api_tokens()


def test_require_auth_rejects_unknown_token(auth_app):
    response = auth_app.get(
        "/probe/auth", headers={"Authorization": "Bearer lct_not-a-real-token"}
    )
    assert response.status_code == 401


def test_require_auth_rejects_expired_token(auth_app, basic_user):
    assert basic_user.id is not None
    token = _make_token(basic_user.id, expires_at=datetime.now(UTC) - timedelta(days=1))
    try:
        response = auth_app.get(
            "/probe/auth", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 401
    finally:
        _clear_api_tokens()


def test_require_auth_interactive_only_rejects_api_token(auth_app, basic_user):
    assert basic_user.id is not None
    token = _make_token(basic_user.id)
    try:
        response = auth_app.get(
            "/probe/auth-interactive", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 403
    finally:
        _clear_api_tokens()


def test_require_auth_interactive_only_accepts_session(auth_app, basic_user):
    assert basic_user.id is not None
    with auth_app.session_transaction() as sess:
        sess["user_id"] = basic_user.id

    response = auth_app.get("/probe/auth-interactive")
    assert response.status_code == 200


def test_require_admin_rejects_no_credential(auth_app):
    response = auth_app.get("/probe/admin")
    assert response.status_code == 401


def test_require_admin_rejects_non_admin(auth_app, basic_user):
    assert basic_user.id is not None
    with auth_app.session_transaction() as sess:
        sess["user_id"] = basic_user.id

    response = auth_app.get("/probe/admin")
    assert response.status_code == 403


def test_require_admin_accepts_admin(auth_app, admin_user):
    assert admin_user.id is not None
    with auth_app.session_transaction() as sess:
        sess["user_id"] = admin_user.id

    response = auth_app.get("/probe/admin")
    assert response.status_code == 200


def test_require_read_access_404s_before_403ing(auth_app, basic_user):
    """A nonexistent resource must 404, never fall through to a 403 (or
    crash) -- this is what retires the old "crashes on missing id" bug
    family for free once every route carries this decorator (Phase 5)."""
    assert basic_user.id is not None
    with auth_app.session_transaction() as sess:
        sess["user_id"] = basic_user.id

    response = auth_app.get("/probe/read/does-not-exist")
    assert response.status_code == 404


def test_require_read_access_403s_without_access(auth_app, basic_user):
    assert basic_user.id is not None
    study = Study(
        name="No Access Study",
        url="http://ftd.unit.tests/no-access-study/",
        title="No Access Study",
        description="",
        owner_id="someone-else",
        visibility=Visibility.Institution,
        access={"institutions": {"chop": "editor"}, "users": {}},
    )
    study.save()
    try:
        with auth_app.session_transaction() as sess:
            sess["user_id"] = basic_user.id

        response = auth_app.get(f"/probe/read/{study.id}")
        assert response.status_code == 403
    finally:
        study.delete(hard_delete=True)


def test_require_read_access_allows_registered_visibility(auth_app, basic_user):
    assert basic_user.id is not None
    study = Study(
        name="Registered Study",
        url="http://ftd.unit.tests/registered-study/",
        title="Registered Study",
        description="",
        owner_id="someone-else",
        visibility=Visibility.Registered,
    )
    study.save()
    try:
        with auth_app.session_transaction() as sess:
            sess["user_id"] = basic_user.id

        response = auth_app.get(f"/probe/read/{study.id}")
        assert response.status_code == 200
    finally:
        study.delete(hard_delete=True)


def test_require_write_access_403s_viewer_only_access(auth_app, basic_user):
    assert basic_user.id is not None
    study = Study(
        name="Viewer Only Study",
        url="http://ftd.unit.tests/viewer-only-study/",
        title="Viewer Only Study",
        description="",
        owner_id="someone-else",
        visibility=Visibility.Registered,
    )
    study.save()
    try:
        with auth_app.session_transaction() as sess:
            sess["user_id"] = basic_user.id

        read_response = auth_app.get(f"/probe/read/{study.id}")
        write_response = auth_app.get(f"/probe/write/{study.id}")
        assert read_response.status_code == 200
        assert write_response.status_code == 403
    finally:
        study.delete(hard_delete=True)


def test_require_write_access_allows_owner(auth_app, basic_user):
    assert basic_user.id is not None
    study = Study(
        name="Owned Study",
        url="http://ftd.unit.tests/owned-write-study/",
        title="Owned Study",
        description="",
        owner_id=basic_user.id,
        visibility=Visibility.Restricted,
    )
    study.save()
    try:
        with auth_app.session_transaction() as sess:
            sess["user_id"] = basic_user.id

        response = auth_app.get(f"/probe/write/{study.id}")
        assert response.status_code == 200
    finally:
        study.delete(hard_delete=True)


def test_require_write_access_allows_institution_editor(auth_app, basic_user):
    assert basic_user.id is not None
    study = Study(
        name="Institution Editor Study",
        url="http://ftd.unit.tests/institution-editor-study/",
        title="Institution Editor Study",
        description="",
        owner_id="someone-else",
        visibility=Visibility.Institution,
        access={"institutions": {"vumc": "editor"}, "users": {}},
    )
    study.save()
    try:
        with auth_app.session_transaction() as sess:
            sess["user_id"] = basic_user.id

        response = auth_app.get(f"/probe/write/{study.id}")
        assert response.status_code == 200
    finally:
        study.delete(hard_delete=True)
