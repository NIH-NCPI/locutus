from datetime import UTC, datetime

import locutus
from locutus.model.institution import Institution
from locutus.model.user import User

from . import _Owner, client


def _clear_institutions():
    for doc in locutus.persistence().collection("Institution").stream():
        locutus.persistence().collection("Institution").document(doc.id).delete()


def test_admin_institutions_post_requires_auth(client):
    response = client.post(
        "/api/admin/institutions",
        json={"name": "VUMC"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_admin_institutions_post_requires_admin(client):
    test_owner = _Owner(client)
    try:
        response = client.post(
            "/api/admin/institutions",
            json={"name": "VUMC"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_admin_institutions_post_creates(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        response = client.post(
            "/api/admin/institutions",
            json={
                "id": "vumc",
                "name": "VUMC",
                "allowedEmails": ["a@vumc.org"],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201
        body = response.json
        assert body["id"] == "vumc"
        assert body["name"] == "VUMC"
        assert body["allowedEmails"] == ["a@vumc.org"]

        fetched = Institution.get("vumc")
        assert fetched is not None
        assert fetched.name == "VUMC"
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_institutions_post_rejects_invalid_email(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        response = client.post(
            "/api/admin/institutions",
            json={"id": "vumc", "name": "VUMC", "allowedEmails": ["1"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert Institution.get("vumc") is None
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_institutions_post_missing_name(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.post(
            "/api/admin/institutions",
            json={},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        admin.cleanup()


def test_admin_institutions_post_duplicate_id_returns_409(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        Institution(id="vumc", name="VUMC").save()

        response = client.post(
            "/api/admin/institutions",
            json={"id": "vumc", "name": "VUMC Again"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 409

        # The original wasn't clobbered.
        fetched = Institution.get("vumc")
        assert fetched is not None
        assert fetched.name == "VUMC"
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_institutions_get_requires_admin(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/admin/institutions")
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_admin_institutions_get_lists_all(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        Institution(name="VUMC").save()
        Institution(name="CHOP").save()

        response = client.get("/api/admin/institutions")
        assert response.status_code == 200
        names = sorted(i["name"] for i in response.json)
        assert names == ["CHOP", "VUMC"]
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_institution_get_by_id(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.get(f"/api/admin/institutions/{institution.id}")
        assert response.status_code == 200
        assert response.json["name"] == "VUMC"
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_institution_get_by_id_resolves_members(client):
    """memberIds alone is a list of opaque ids -- the admin UI needs actual
    detail (who is this, when did they last log in) to be useful, so the
    response also carries a resolved `members` array alongside the
    unchanged `memberIds`."""
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    never_logged_in = User(email="never-logged-in@vumc.org", institution_ids=[]).save()
    logged_in = User(email="logged-in@vumc.org", institution_ids=[]).save()
    try:
        assert never_logged_in.id is not None
        assert logged_in.id is not None

        last_login = datetime(2026, 9, 20, 12, 0, 0, tzinfo=UTC)
        logged_in.last_login_at = last_login
        logged_in.save()

        institution = Institution(name="VUMC").save()
        assert institution.id is not None
        institution.add_member(never_logged_in.id)
        institution.add_member(logged_in.id)
        # A memberIds entry with no matching User (stale/deleted account)
        # must be silently skipped, not raise.
        institution.add_member("deleted-user-id")
        institution.save()

        response = client.get(f"/api/admin/institutions/{institution.id}")
        assert response.status_code == 200
        assert response.json["memberIds"] == [
            never_logged_in.id,
            logged_in.id,
            "deleted-user-id",
        ]

        members = {m["id"]: m for m in response.json["members"]}
        assert set(members.keys()) == {never_logged_in.id, logged_in.id}

        assert members[never_logged_in.id]["email"] == "never-logged-in@vumc.org"
        assert members[never_logged_in.id]["lastLoginAt"] is None

        assert members[logged_in.id]["email"] == "logged-in@vumc.org"
        assert members[logged_in.id]["lastLoginAt"] is not None
    finally:
        _clear_institutions()
        never_logged_in.delete()
        logged_in.delete()
        admin.cleanup()


def test_admin_institution_get_by_id_missing_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.get("/api/admin/institutions/not-there")
        assert response.status_code == 404
    finally:
        admin.cleanup()


def test_admin_allowlist_requires_admin(client):
    test_owner = _Owner(client)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"emails": ["a@vumc.org"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        _clear_institutions()
        test_owner.cleanup()


def test_admin_allowlist_post_add_emails(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"emails": ["a@vumc.org", "b@vumc.org"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert sorted(response.json) == ["a@vumc.org", "b@vumc.org"]

        # Adding an already-present email is a no-op, not a duplicate.
        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"emails": ["a@vumc.org"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert sorted(response.json) == ["a@vumc.org", "b@vumc.org"]
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_post_rejects_invalid_email(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"emails": ["1"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        fetched = Institution.get(institution.id)
        assert fetched is not None
        assert fetched.allowed_emails == []

        # A mix of valid and invalid rejects the whole batch -- the valid
        # one isn't partially applied.
        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"emails": ["a@vumc.org", "1"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400

        fetched = Institution.get(institution.id)
        assert fetched is not None
        assert fetched.allowed_emails == []
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_post_single_email_shorthand(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={"email": "a@vumc.org"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json == ["a@vumc.org"]
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_post_missing_emails_returns_400(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.post(
            f"/api/admin/institutions/{institution.id}/allowlist",
            json={},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_post_missing_institution_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.post(
            "/api/admin/institutions/not-there/allowlist",
            json={"emails": ["a@vumc.org"]},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        admin.cleanup()


def test_admin_allowlist_get(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC", allowed_emails=["a@vumc.org"]).save()
        assert institution.id is not None

        response = client.get(f"/api/admin/institutions/{institution.id}/allowlist")
        assert response.status_code == 200
        assert response.json == ["a@vumc.org"]
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_delete(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(
            name="VUMC", allowed_emails=["a@vumc.org", "b@vumc.org"]
        ).save()
        assert institution.id is not None

        response = client.delete(
            f"/api/admin/institutions/{institution.id}/allowlist/a@vumc.org"
        )
        assert response.status_code == 200
        assert response.json == ["b@vumc.org"]

        fetched = Institution.get(institution.id)
        assert fetched is not None
        assert fetched.allowed_emails == ["b@vumc.org"]
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_delete_revokes_provisioned_member(client):
    """Removing an email that already has an account attached doubles as
    "revoke this institution's access" -- both memberIds (bookkeeping) and
    the user's own institutionIds (what get_permission() actually
    consults) must drop the institution, or the allowlist edit wouldn't
    actually revoke anything for someone already provisioned."""
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    member = User(email="member@vumc.org", institution_ids=[]).save()
    try:
        institution = Institution(
            name="VUMC", allowed_emails=["member@vumc.org"]
        ).save()
        assert institution.id is not None
        assert member.id is not None

        member.institution_ids = [institution.id]
        member.save()
        institution.add_member(member.id)
        institution.save()

        response = client.delete(
            f"/api/admin/institutions/{institution.id}/allowlist/member@vumc.org"
        )
        assert response.status_code == 200
        assert response.json == []

        fetched_inst = Institution.get(institution.id)
        assert fetched_inst is not None
        assert fetched_inst.allowed_emails == []
        assert fetched_inst.member_ids == []

        fetched_member = User.get(member.id)
        assert fetched_member is not None
        assert fetched_member.institution_ids == []
    finally:
        _clear_institutions()
        member.delete()
        admin.cleanup()


def test_admin_allowlist_delete_not_present_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC").save()
        assert institution.id is not None

        response = client.delete(
            f"/api/admin/institutions/{institution.id}/allowlist/not-there@vumc.org"
        )
        assert response.status_code == 404
    finally:
        _clear_institutions()
        admin.cleanup()


def test_admin_allowlist_delete_requires_admin(client):
    test_owner = _Owner(client)
    _clear_institutions()
    try:
        institution = Institution(name="VUMC", allowed_emails=["a@vumc.org"]).save()
        assert institution.id is not None

        response = client.delete(
            f"/api/admin/institutions/{institution.id}/allowlist/a@vumc.org"
        )
        assert response.status_code == 403
    finally:
        _clear_institutions()
        test_owner.cleanup()


# ── S4: admin user management ────────────────────────────────────────────


def test_admin_users_get_requires_auth(client):
    response = client.get("/api/admin/users")
    assert response.status_code == 401


def test_admin_users_get_requires_admin(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/admin/users")
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_admin_users_get_lists_all(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    disabled = User(
        email="disabled@vumc.org",
        institution_ids=[],
        disabled_at=datetime.now(UTC),
        disabled_by=admin.user.id,
    ).save()
    try:
        response = client.get("/api/admin/users")
        assert response.status_code == 200

        # Listing includes disabled accounts -- an admin managing users
        # needs to see them, both to re-enable and just to know who's
        # disabled. Scoped to the ids this test created, since other
        # accounts may exist in the shared test database.
        by_id = {u["id"]: u for u in response.json}
        assert by_id[admin.user.id]["disabledAt"] is None
        assert by_id[member.id]["email"] == "member@vumc.org"
        assert by_id[member.id]["disabledAt"] is None
        assert by_id[disabled.id]["email"] == "disabled@vumc.org"
        assert by_id[disabled.id]["disabledAt"] is not None
        assert by_id[disabled.id]["disabledBy"] == admin.user.id
    finally:
        member.delete()
        disabled.delete()
        admin.cleanup()


def test_admin_user_get_by_id(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=["vumc"]).save()
    try:
        response = client.get(f"/api/admin/users/{member.id}")
        assert response.status_code == 200
        assert response.json["email"] == "member@vumc.org"
        assert response.json["institutionIds"] == ["vumc"]
    finally:
        member.delete()
        admin.cleanup()


def test_admin_user_get_by_id_missing_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.get("/api/admin/users/not-there")
        assert response.status_code == 404
    finally:
        admin.cleanup()


def test_admin_user_disable_requires_admin(client):
    test_owner = _Owner(client)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    try:
        response = client.post(f"/api/admin/users/{member.id}/disable")
        assert response.status_code == 403
    finally:
        member.delete()
        test_owner.cleanup()


def test_admin_user_disable_sets_fields(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    assert member.id is not None
    try:
        response = client.post(f"/api/admin/users/{member.id}/disable")
        assert response.status_code == 200
        assert response.json["disabledAt"] is not None
        assert response.json["disabledBy"] == admin.user.id

        fetched = User.get(member.id)
        assert fetched is not None
        assert fetched.disabled_at is not None
        assert fetched.disabled_by == admin.user.id
    finally:
        member.delete()
        admin.cleanup()


def test_admin_user_disable_missing_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.post("/api/admin/users/not-there/disable")
        assert response.status_code == 404
    finally:
        admin.cleanup()


def test_admin_user_disable_rejects_self_target(client):
    """No admin self-lockout -- there may be no other admin available to
    reverse it."""
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    assert admin.user.id is not None
    try:
        response = client.post(f"/api/admin/users/{admin.user.id}/disable")
        assert response.status_code == 403

        fetched = User.get(admin.user.id)
        assert fetched is not None
        assert fetched.disabled_at is None
    finally:
        admin.cleanup()


def test_admin_user_disable_is_idempotent(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    try:
        first = client.post(f"/api/admin/users/{member.id}/disable")
        assert first.status_code == 200

        second = client.post(f"/api/admin/users/{member.id}/disable")
        assert second.status_code == 200
        assert second.json["disabledAt"] is not None
    finally:
        member.delete()
        admin.cleanup()


def test_admin_user_enable_requires_admin(client):
    test_owner = _Owner(client)
    member = User(
        email="member@vumc.org", institution_ids=[], disabled_at=datetime.now(UTC)
    ).save()
    try:
        response = client.post(f"/api/admin/users/{member.id}/enable")
        assert response.status_code == 403
    finally:
        member.delete()
        test_owner.cleanup()


def test_admin_user_enable_clears_fields(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(
        email="member@vumc.org",
        institution_ids=[],
        disabled_at=datetime.now(UTC),
        disabled_by="some-other-admin-id",
    ).save()
    assert member.id is not None
    try:
        response = client.post(f"/api/admin/users/{member.id}/enable")
        assert response.status_code == 200
        assert response.json["disabledAt"] is None
        assert response.json["disabledBy"] is None

        fetched = User.get(member.id)
        assert fetched is not None
        assert fetched.disabled_at is None
        assert fetched.disabled_by is None
    finally:
        member.delete()
        admin.cleanup()


def test_admin_user_enable_missing_returns_404(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    try:
        response = client.post("/api/admin/users/not-there/enable")
        assert response.status_code == 404
    finally:
        admin.cleanup()


def test_admin_user_enable_is_idempotent(client):
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    try:
        first = client.post(f"/api/admin/users/{member.id}/enable")
        assert first.status_code == 200

        second = client.post(f"/api/admin/users/{member.id}/enable")
        assert second.status_code == 200
        assert second.json["disabledAt"] is None
    finally:
        member.delete()
        admin.cleanup()


def test_disabled_user_cannot_authenticate_after_admin_disables_them(client):
    """End-to-end: disabling through the admin endpoint actually revokes
    access, not just the flag -- the disabled user's own session stops
    working on their very next request."""
    admin = _Owner(client, email="admin@example.com", role=User.Role.Admin)
    member = User(email="member@vumc.org", institution_ids=[]).save()
    try:
        response = client.post(f"/api/admin/users/{member.id}/disable")
        assert response.status_code == 200

        with client.session_transaction() as sess:
            sess["user_id"] = member.id

        response = client.get("/api/admin/users")
        assert response.status_code == 401
    finally:
        member.delete()
        admin.cleanup()
