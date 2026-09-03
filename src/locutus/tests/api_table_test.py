from urllib.parse import quote

from locutus.model.table import Table
from locutus.model.terminology import Terminology

from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_table_get(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table")
        assert response.status_code == 200

        tables = response.json
        assert len(tables) >= 1

        response = client.get(f"/api/Table/{basic_table.id}")
        assert response.status_code == 200

        table = response.json
        assert table["id"] == basic_table.id
        assert table["name"] == basic_table.name
    finally:
        test_owner.cleanup()


def test_table_get_requires_auth(client):
    response = client.get("/api/Table/not-there")
    assert response.status_code == 401


def test_table_get_missing_returns_404(client):
    """Pins the issues/001 fix: now that Table.get is behind
    require_read_access, a nonexistent id 404s before the handler (which
    never itself checked for None) can even run."""
    test_owner = _Owner(client)
    try:
        response = client.get("/api/Table/not-there")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_post_creates_table(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        body = {
            "name": "API Created Table",
            "url": "http://ftd.unit.tests/api_table/created",
            "description": "Created via POST",
            "editor": "unit-test",
        }

        response = client.post(
            "/api/Table", json=body, headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 201

        created = response.json
        assert created["name"] == "API Created Table"
        assert created["id"] is not None
        # The creator is stamped as owner automatically (M4) -- never
        # trusted from the request body.
        assert created["owner_id"] == test_owner.user.id

        table = Table.get(created["id"])
        assert table is not None

        terminology = table.terminology.dereference()
        table.delete(hard_delete=True)
        terminology.delete(hard_delete=True)
    finally:
        test_owner.cleanup()


def test_table_post_requires_auth(client):
    body = {
        "name": "No Auth Table",
        "url": "http://ftd.unit.tests/api_table/no_auth",
    }
    response = client.post(
        "/api/Table", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 401


def test_table_post_missing_editor(client):
    test_owner = _Owner(client)
    try:
        body = {
            "name": "No Editor Table",
            "url": "http://ftd.unit.tests/api_table/no_editor",
        }

        response = client.post(
            "/api/Table", json=body, headers=test_owner.token_headers()
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_put_updates_table(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        updated = dict(client.get(f"/api/Table/{basic_table.id}").json)
        updated["description"] = "Updated Description"
        updated["editor"] = "unit-test"

        response = client.put(
            f"/api/Table/{basic_table.id}",
            json=updated,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json["description"] == "Updated Description"

        table = Table.get(basic_table.id)
        assert table is not None
        assert table.description == "Updated Description"
        # PUT must not let the client reassign ownership via the body.
        assert table.owner_id == test_owner.user.id
    finally:
        test_owner.cleanup()


def test_table_put_requires_write_access(client, sample_terminology, basic_table):
    """basic_table's default owner_id is None -- a real, different,
    logged-in user only gets Registered-visibility viewer access, not
    editor, so a write must 403."""
    test_owner = _Owner(client)
    try:
        updated = dict(client.get(f"/api/Table/{basic_table.id}").json)
        updated["editor"] = "unit-test"

        response = client.put(
            f"/api/Table/{basic_table.id}",
            json=updated,
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_put_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        updated = dict(client.get(f"/api/Table/{basic_table.id}").json)

        response = client.put(
            f"/api/Table/{basic_table.id}",
            json=updated,
            headers=test_owner.token_headers(),
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_delete(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        body = {
            "name": "Table To Delete",
            "url": "http://ftd.unit.tests/api_table/to_delete",
            "editor": "unit-test",
        }
        created = client.post(
            "/api/Table", json=body, headers={"Content-Type": "application/json"}
        ).json
        table_id = created["id"]
        terminology_id = created["terminology"]["reference"].split("/")[-1]

        response = client.delete(
            f"/api/Table/{table_id}",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json["id"] == table_id

        assert Table.get(table_id) is None

        remaining_terminology = Terminology.get(terminology_id)
        if remaining_terminology is not None:
            remaining_terminology.delete(hard_delete=True)
    finally:
        test_owner.cleanup()


def test_table_delete_requires_write_access(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.delete(
            f"/api/Table/{basic_table.id}",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
        assert Table.get(basic_table.id) is not None
    finally:
        test_owner.cleanup()


def test_table_delete_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.delete(
            f"/api/Table/{basic_table.id}",
            json={},
            headers=test_owner.token_headers(),
        )
        assert response.status_code == 400

        # The table must still exist since the delete should have been rejected.
        assert Table.get(basic_table.id) is not None
    finally:
        test_owner.cleanup()


def test_table_edit_put_adds_variable(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.put(
            f"/api/Table/{basic_table.id}/variable/new_field",
            json={
                "data_type": "string",
                "description": "A brand new field",
                "editor": "unit-test",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

        table = Table.get(basic_table.id)
        assert table is not None
        variable = table.get_variable("new_field")
        assert variable is not None
        assert variable.description == "A brand new field"
    finally:
        test_owner.cleanup()


def test_table_edit_put_requires_write_access(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.put(
            f"/api/Table/{basic_table.id}/variable/new_field",
            json={
                "data_type": "string",
                "description": "A brand new field",
                "editor": "unit-test",
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_edit_put_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.put(
            f"/api/Table/{basic_table.id}/variable/new_field",
            json={"data_type": "string", "description": "A brand new field"},
            headers=test_owner.token_headers(),
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_edit_delete_variable(client, sample_terminology, basic_table):
    # TableEdit.delete matches on the variable's *name*, not its code, despite
    # the route/parameter being called "code".
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.delete(
            f"/api/Table/{basic_table.id}/variable/{quote('String Var')}",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200

        table = Table.get(basic_table.id)
        assert table is not None
        assert table.get_variable("String Var") is None
    finally:
        test_owner.cleanup()


def test_table_edit_delete_variable_not_found(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.delete(
            f"/api/Table/{basic_table.id}/variable/does_not_exist",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_edit_delete_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.delete(
            f"/api/Table/{basic_table.id}/variable/{quote('String Var')}",
            json={},
            headers=test_owner.token_headers(),
        )
        assert response.status_code == 400

        table = Table.get(basic_table.id)
        assert table is not None
        assert table.get_variable("String Var") is not None
    finally:
        test_owner.cleanup()


def test_table_rename_code_updates_name_and_description(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.patch(
            f"/api/Table/{basic_table.id}/rename",
            json={
                "editor": "unit-test",
                "variable": {"String Var": "Renamed String Var"},
                "description": {"String Var": "Renamed Description"},
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 201

        table = Table.get(basic_table.id)
        assert table is not None
        variable = table.get_variable("Renamed String Var")
        assert variable is not None
        assert variable.description == "Renamed Description"
    finally:
        test_owner.cleanup()


def test_table_rename_code_requires_write_access(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.patch(
            f"/api/Table/{basic_table.id}/rename",
            json={
                "editor": "unit-test",
                "variable": {"String Var": "Renamed String Var"},
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_rename_code_requires_variable_or_description(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.patch(
            f"/api/Table/{basic_table.id}/rename",
            json={"editor": "unit-test"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_rename_code_missing_editor(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.patch(
            f"/api/Table/{basic_table.id}/rename",
            json={"variable": {"String Var": "Renamed String Var"}},
            headers=test_owner.token_headers(),
        )
        assert response.status_code == 400
    finally:
        test_owner.cleanup()


def test_table_rename_code_variable_not_found(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)

        response = client.patch(
            f"/api/Table/{basic_table.id}/rename",
            json={
                "editor": "unit-test",
                "variable": {"Does Not Exist": "New Name"},
            },
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_harmony_table_csv_default(client, sample_terminology, basic_table):
    response = client.get(f"/api/Table/{basic_table.id}/harmony")
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_harmony_table_csv_invalid_format(client, sample_terminology, basic_table):
    response = client.get(
        f"/api/Table/{basic_table.id}/harmony", query_string={"format": "not-a-format"}
    )
    assert response.status_code == 400
