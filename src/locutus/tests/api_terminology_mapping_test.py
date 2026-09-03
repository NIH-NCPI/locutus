import pytest

from . import _Owner, client
from .test_terminology import ftd_concept_relationships, sample_terminology


def _set_mapping(client, term_id, code, mapped_code, editor="unit-test"):
    return client.put(
        f"/api/Terminology/{term_id}/mapping/{code}",
        json={
            "editor": editor,
            "mappings": [
                {
                    "code": mapped_code,
                    "display": f"Mapped Display {mapped_code}",
                    "system": "http://mapping.system",
                }
            ],
        },
        headers={"Content-Type": "application/json"},
    )


def test_terminology_mapping_put_and_get(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")
        assert response.status_code == 201

        response = client.get("/api/Terminology/ontology-one/mapping/C1")
        assert response.status_code == 200

        body = response.json
        assert body["code"] == "C1"
        assert len(body["mappings"]) == 1
        assert body["mappings"][0]["code"] == "MAPPED_CODE"
    finally:
        test_owner.cleanup()


def test_terminology_mapping_put_missing_system(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.put(
            "/api/Terminology/ontology-one/mapping/C1",
            json={
                "editor": "unit-test",
                "mappings": [{"code": "MAPPED_CODE", "display": "Mapped Display"}],
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_terminology_mapping_put_missing_editor(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            "/api/Terminology/ontology-one/mapping/C1",
            json={
                "mappings": [
                    {
                        "code": "MAPPED_CODE",
                        "display": "Mapped Display",
                        "system": "http://mapping.system",
                    }
                ]
            },
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_terminology_mapping_put_code_not_present(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = _set_mapping(client, "ontology-one", "C99", "MAPPED_CODE")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_mapping_get_user_input_requires_editor(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        headers = test_owner.token_headers()
        response = client.get(
            "/api/Terminology/ontology-one/mapping/C1",
            query_string={"user_input": "true"},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_terminology_mapping_delete(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        response = client.delete(
            "/api/Terminology/ontology-one/mapping/C1",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        response = client.get("/api/Terminology/ontology-one/mapping/C1")
        assert response.json["mappings"] == []
    finally:
        test_owner.cleanup()


def test_terminology_mapping_delete_missing_editor(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.delete(
            "/api/Terminology/ontology-one/mapping/C1",
            json={},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_terminology_mapping_delete_code_not_present(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.delete(
            "/api/Terminology/ontology-one/mapping/C99",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_mapping_get_missing_terminology_returns_404(client):
    # require_read_access now 404s before the handler runs, resolving the
    # AttributeError this used to document.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Terminology/not-there/mapping/C1")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_mapping_requires_write_access(
    client, ftd_concept_relationships, sample_terminology
):
    # sample_terminology's default owner_id is None -- a real, different,
    # logged-in user only gets Registered-visibility viewer access.
    test_owner = _Owner(client)
    try:
        response = _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_terminology_mappings_get_all(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        response = client.get("/api/Terminology/ontology-one/mapping")
        assert response.status_code == 200

        body = response.json
        codes_by_code = {entry["code"]: entry for entry in body["codes"]}
        assert len(codes_by_code["C1"]["mappings"]) == 1
        assert codes_by_code["C2"]["mappings"] == []
    finally:
        test_owner.cleanup()


def test_terminology_mappings_delete_all(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")
        _set_mapping(client, "ontology-one", "C2", "MAPPED_CODE_2")

        response = client.delete(
            "/api/Terminology/ontology-one/mapping",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        response = client.get("/api/Terminology/ontology-one/mapping")
        for entry in response.json["codes"]:
            assert entry["mappings"] == []
    finally:
        test_owner.cleanup()


def test_terminology_mappings_delete_missing_editor(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.delete(
            "/api/Terminology/ontology-one/mapping",
            json={},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_terminology_mappings_get_missing_terminology_returns_404(client):
    # require_read_access now 404s before the handler (and get_mappings,
    # which used to raise UnboundLocalError on a missing id) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Terminology/not-there/mapping")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_mappings_requires_write_access(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        response = client.delete(
            "/api/Terminology/ontology-one/mapping",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_raises_on_valid_request(
    client, ftd_concept_relationships, sample_terminology
):
    # Documents current behavior: this is the "happy path" (existing mapping,
    # valid relationship value, editor present) and it still crashes.
    # Coding.set_mapping_relationship iterates self.mappings (CodingMapping
    # instances) and does `mapping["code"]`, which isn't valid on an object
    # rather than a dict. The endpoint cannot succeed for any input today.
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        with pytest.raises(TypeError):
            client.put(
                "/api/Terminology/ontology-one/mapping_relationship/C1/mapping/MAPPED_CODE",
                json={"mapping_relationship": "equivalent", "editor": "unit-test"},
                headers={"Content-Type": "application/json"},
            )
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_missing_relationship_field(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        response = client.put(
            "/api/Terminology/ontology-one/mapping_relationship/C1/mapping/MAPPED_CODE",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_missing_editor(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            "/api/Terminology/ontology-one/mapping_relationship/C1/mapping/MAPPED_CODE",
            json={"mapping_relationship": "equivalent"},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_code_not_present(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.put(
            "/api/Terminology/ontology-one/mapping_relationship/C99/mapping/MAPPED_CODE",
            json={"mapping_relationship": "equivalent", "editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_invalid_relationship_value(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        _set_mapping(client, "ontology-one", "C1", "MAPPED_CODE")

        response = client.put(
            "/api/Terminology/ontology-one/mapping_relationship/C1/mapping/MAPPED_CODE",
            json={
                "mapping_relationship": "not-a-real-relationship",
                "editor": "unit-test",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_mapping_relationship_put_requires_write_access(
    client, ftd_concept_relationships, sample_terminology
):
    test_owner = _Owner(client)
    try:
        response = client.put(
            "/api/Terminology/ontology-one/mapping_relationship/C1/mapping/MAPPED_CODE",
            json={"mapping_relationship": "equivalent", "editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()
