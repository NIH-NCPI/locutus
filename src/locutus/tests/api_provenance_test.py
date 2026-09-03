from locutus.model.provenance import Provenance

from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_table_provenance_requires_auth(client, sample_terminology, basic_table):
    response = client.get(f"/api/Provenance/Table/{basic_table.id}")
    assert response.status_code == 401


def test_table_provenance_get(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.get(f"/api/Provenance/Table/{basic_table.id}")
        assert response.status_code == 200

        body = response.json
        assert body["table"]["Reference"] == f"Table/{basic_table.id}"
        assert body["provenance"]["self"]["target"] == "self"
    finally:
        test_owner.cleanup()


def test_table_var_provenance_get_all(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.get(f"/api/Provenance/Table/{basic_table.id}/code/ALL")
        assert response.status_code == 200
        assert "provenance" in response.json
    finally:
        test_owner.cleanup()


def test_table_var_provenance_get_specific_code(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.get(f"/api/Provenance/Table/{basic_table.id}/code/string_var")
        assert response.status_code == 200
        assert "provenance" in response.json
    finally:
        test_owner.cleanup()


def test_table_provenance_get_missing_table_returns_404(client):
    # require_read_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Provenance/Table/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_provenance_get(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        # Renaming a code (via the model, mirroring what the rename endpoint
        # does) generates a provenance entry to make the response non-trivial.
        sample_terminology.add_provenance(
            change_type=Provenance.ChangeType.EditTerm,
            target="self",
            old_value="before",
            new_value="after",
            editor="unit-test",
        )

        response = client.get(f"/api/Provenance/Terminology/{sample_terminology.id}")
        assert response.status_code == 200

        body = response.json
        assert (
            body["terminology"]["Reference"] == f"Terminology/{sample_terminology.id}"
        )
        assert len(body["provenance"]["self"]["changes"]) >= 1
    finally:
        test_owner.cleanup()


def test_terminology_code_provenance_get(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        response = client.get(
            f"/api/Provenance/Terminology/{sample_terminology.id}/code/C1"
        )
        assert response.status_code == 200
        assert "provenance" in response.json
    finally:
        test_owner.cleanup()


def test_terminology_provenance_get_missing_terminology_returns_404(client):
    # require_read_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Provenance/Terminology/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()
