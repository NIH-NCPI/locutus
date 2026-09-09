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
