from locutus.model.study import Study
from locutus.model.user import User
from locutus.model.visibility import Visibility

from . import _Owner, client
from .test_study import basic_study
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_combined_harmony_requires_auth(client):
    response = client.get("/api/harmony")
    assert response.status_code == 401


def test_combined_harmony_no_ids(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/harmony")
        assert response.status_code == 200
        assert response.json == {"harmony": [], "omitted": []}
    finally:
        test_owner.cleanup()


def test_combined_harmony_with_study(client, sample_terminology, basic_study):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_study)
        response = client.get("/api/harmony", query_string={"studies": basic_study.id})
        assert response.status_code == 200
        assert isinstance(response.json["harmony"], list)
        assert response.json["omitted"] == []
    finally:
        test_owner.cleanup()


def test_combined_harmony_with_table(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = client.get("/api/harmony", query_string={"tables": basic_table.id})
        assert response.status_code == 200
        assert isinstance(response.json["harmony"], list)
        assert response.json["omitted"] == []
    finally:
        test_owner.cleanup()


def test_combined_harmony_invalid_format(client):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/harmony", query_string={"format": "not-a-format"})
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_combined_harmony_unknown_ids_omitted(client):
    # Unlike almost every other resource in this codebase, build_combined_harmony
    # checks each id for None before using it, so unknown ids are silently
    # skipped rather than causing a crash or a 404 -- but M11 now requires
    # reporting them back rather than just quietly returning a partial result.
    test_owner = _Owner(client)
    try:
        response = client.get(
            "/api/harmony",
            query_string={
                "studies": "not-there",
                "datadictionaries": "not-there",
                "tables": "not-there",
            },
        )
        assert response.status_code == 200
        assert response.json["harmony"] == []
        assert sorted(response.json["omitted"]) == ["not-there"] * 3
    finally:
        test_owner.cleanup()


def test_combined_harmony_inaccessible_ids_omitted(client):
    # A Restricted-visibility study owned by someone else, with an access
    # map that doesn't include the caller, gets omitted from the export
    # (and reported) rather than 403ing the whole request.
    test_owner = _Owner(client)
    other_owner = User(email="combined-harmony-other-owner@example.com").save()
    restricted_study = Study(
        name="Restricted Study",
        url="http://ftd.unit.tests/combined_harmony/restricted",
        owner_id=other_owner.id,
        visibility=Visibility.Restricted,
        access={"institutions": {}, "users": {}},
    )
    restricted_study.save()
    try:
        response = client.get(
            "/api/harmony", query_string={"studies": restricted_study.id}
        )
        assert response.status_code == 200
        assert response.json["harmony"] == []
        assert response.json["omitted"] == [restricted_study.id]
    finally:
        restricted_study.delete(hard_delete=True)
        other_owner.delete()
        test_owner.cleanup()
