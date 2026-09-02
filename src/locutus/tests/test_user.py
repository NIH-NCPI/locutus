import locutus
from locutus.model.user import User


def _clear():
    for doc in locutus.persistence().collection("User").stream():
        locutus.persistence().collection("User").document(doc.id).delete()


def test_user_save_and_get_round_trip():
    _clear()

    try:
        user = User(
            email="a@example.com",
            display_name="A User",
            institution_ids=["vumc"],
            role=User.Role.User,
        ).save()
        assert user.id is not None

        fetched = User.get(user.id)
        assert fetched is not None
        assert fetched.email == "a@example.com"
        assert fetched.display_name == "A User"
        assert fetched.institution_ids == ["vumc"]
        assert fetched.role == User.Role.User
        assert fetched.is_admin() is False
    finally:
        _clear()


def test_user_get_missing_returns_none():
    assert User.get("does-not-exist") is None


def test_user_defaults_role_to_user():
    _clear()

    try:
        user = User(email="b@example.com").save()
        assert user.id is not None
        fetched = User.get(user.id)
        assert fetched is not None
        assert fetched.role == User.Role.User
        assert fetched.institution_ids == []
    finally:
        _clear()


def test_user_admin_role():
    _clear()

    try:
        user = User(email="admin@example.com", role=User.Role.Admin).save()
        assert user.id is not None
        fetched = User.get(user.id)
        assert fetched is not None
        assert fetched.is_admin() is True
    finally:
        _clear()


def test_user_find_by_email():
    _clear()

    try:
        User(email="findme@example.com", institution_ids=["chop"]).save()

        found = User.find_by_email("findme@example.com")
        assert found is not None
        assert found.institution_ids == ["chop"]

        assert User.find_by_email("nobody@example.com") is None
    finally:
        _clear()


def test_user_delete():
    _clear()

    try:
        user = User(email="delete-me@example.com").save()
        assert user.id is not None
        assert User.get(user.id) is not None

        user.delete()
        assert User.get(user.id) is None
    finally:
        _clear()
