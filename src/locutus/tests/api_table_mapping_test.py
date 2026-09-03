import pytest

from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def _set_mapping(client, table_id, code, mapped_code, editor="unit-test"):
    return client.put(
        f"/api/Table/{table_id}/mapping/{code}",
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


def test_table_mapping_put_and_get(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        response = _set_mapping(client, basic_table.id, "string_var", "MAPPED_CODE")
        assert response.status_code == 201

        response = client.get(f"/api/Table/{basic_table.id}/mapping/string_var")
        assert response.status_code == 200

        body = response.json
        assert body["code"] == "string_var"
        assert len(body["mappings"]) == 1
        assert body["mappings"][0]["code"] == "MAPPED_CODE"
    finally:
        test_owner.cleanup()


def test_table_mapping_put_missing_system_raises(
    client, sample_terminology, basic_table
):
    # Documents current behavior: unlike TerminologyMapping.put, TableMapping.put
    # doesn't validate that each mapping has a 'system' key before constructing
    # CodingMapping, which itself blows up on a None system.
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        with pytest.raises(AttributeError):
            client.put(
                f"/api/Table/{basic_table.id}/mapping/string_var",
                json={
                    "editor": "unit-test",
                    "mappings": [{"code": "MAPPED_CODE", "display": "Mapped Display"}],
                },
                headers={"Content-Type": "application/json"},
            )
    finally:
        test_owner.cleanup()


def test_table_mapping_put_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            f"/api/Table/{basic_table.id}/mapping/string_var",
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


def test_table_mapping_get_user_input_requires_editor(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        response = client.get(
            f"/api/Table/{basic_table.id}/mapping/string_var",
            query_string={"user_input": "true"},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_mapping_delete(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        _set_mapping(client, basic_table.id, "string_var", "MAPPED_CODE")

        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping/string_var",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        response = client.get(f"/api/Table/{basic_table.id}/mapping/string_var")
        assert response.json["mappings"] == []
    finally:
        test_owner.cleanup()


def test_table_mapping_delete_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping/string_var",
            json={},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_mapping_get_missing_table_returns_404(client):
    # require_read_access now 404s before the handler runs, resolving the
    # AttributeError this used to document.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table/not-there/mapping/string_var")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_mappings_get_all(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        _set_mapping(client, basic_table.id, "string_var", "MAPPED_CODE")

        response = client.get(f"/api/Table/{basic_table.id}/mapping")
        assert response.status_code == 200

        codes_by_code = {entry["code"]: entry for entry in response.json["codes"]}
        assert len(codes_by_code["string_var"]["mappings"]) == 1
        assert codes_by_code["integer-var"]["mappings"] == []
    finally:
        test_owner.cleanup()


def test_table_mappings_delete_all(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        _set_mapping(client, basic_table.id, "string_var", "MAPPED_CODE")

        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        # Documents current behavior: delete_mappings() has no return statement,
        # so mappings_removed is always None regardless of how many were removed.
        assert response.json["mappings_removed"] is None

        response = client.get(f"/api/Table/{basic_table.id}/mapping")
        for entry in response.json["codes"]:
            assert entry["mappings"] == []
    finally:
        test_owner.cleanup()


def test_table_mappings_delete_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping",
            json={},
            headers=headers,
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_mappings_get_missing_table_returns_404(client):
    # require_read_access now 404s before the handler runs, resolving the
    # AttributeError this used to document.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table/not-there/mapping")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_mapping_requires_auth(client, sample_terminology, basic_table):
    response = client.get(f"/api/Table/{basic_table.id}/mapping/string_var")
    assert response.status_code == 401


def test_table_mapping_put_requires_write_access(
    client, sample_terminology, basic_table
):
    # basic_table's default owner_id is None (Registered visibility) --
    # a real, logged-in, non-owning user only gets viewer access.
    test_owner = _Owner(client)
    try:
        response = _set_mapping(client, basic_table.id, "string_var", "MAPPED_CODE")
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_mapping_delete_requires_write_access(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping/string_var",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_mappings_delete_requires_write_access(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.delete(
            f"/api/Table/{basic_table.id}/mapping",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()
