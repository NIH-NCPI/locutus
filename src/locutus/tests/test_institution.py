import locutus
from locutus.model.institution import Institution


def _clear():
    for doc in locutus.persistence().collection("Institution").stream():
        locutus.persistence().collection("Institution").document(doc.id).delete()


def test_institution_save_and_get_round_trip():
    _clear()

    try:
        inst = Institution(
            name="VUMC",
            member_ids=["u1", "u2"],
            allowed_emails=["a@vumc.org"],
        ).save()

        fetched = Institution.get(inst.id)
        assert fetched is not None
        assert fetched.name == "VUMC"
        assert fetched.member_ids == ["u1", "u2"]
        assert fetched.allowed_emails == ["a@vumc.org"]
    finally:
        _clear()


def test_institution_get_missing_returns_none():
    assert Institution.get("does-not-exist") is None


def test_institution_defaults_are_empty_lists():
    _clear()

    try:
        inst = Institution(name="CHOP").save()
        fetched = Institution.get(inst.id)
        assert fetched is not None
        assert fetched.member_ids == []
        assert fetched.allowed_emails == []
    finally:
        _clear()


def test_institution_all():
    _clear()

    try:
        Institution(name="VUMC").save()
        Institution(name="CHOP").save()

        names = sorted(inst.name for inst in Institution.all() if inst.name is not None)
        assert names == ["CHOP", "VUMC"]
    finally:
        _clear()


def test_institution_allows_email():
    inst = Institution(name="VUMC", allowed_emails=["a@vumc.org"])
    assert inst.allows_email("a@vumc.org") is True
    assert inst.allows_email("nobody@vumc.org") is False


def test_institution_add_and_remove_member():
    inst = Institution(name="VUMC", member_ids=["u1"])

    inst.add_member("u2")
    assert inst.member_ids == ["u1", "u2"]

    # Adding an existing member is a no-op, not a duplicate.
    inst.add_member("u1")
    assert inst.member_ids == ["u1", "u2"]

    inst.remove_member("u1")
    assert inst.member_ids == ["u2"]

    # Removing a member that isn't there doesn't raise.
    inst.remove_member("not-a-member")
    assert inst.member_ids == ["u2"]


def test_institution_delete():
    _clear()

    try:
        inst = Institution(name="VUMC").save()
        assert Institution.get(inst.id) is not None

        inst.delete()
        assert Institution.get(inst.id) is None
    finally:
        _clear()
