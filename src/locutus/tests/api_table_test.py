from urllib.parse import quote

from locutus.model.table import Table
from locutus.model.terminology import Terminology

from . import client
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_table_get(client, sample_terminology, basic_table):
    response = client.get("/api/Table")
    assert response.status_code == 200

    tables = response.json
    assert len(tables) >= 1

    response = client.get(f"/api/Table/{basic_table.id}")
    assert response.status_code == 200

    table = response.json
    assert table["id"] == basic_table.id
    assert table["name"] == basic_table.name


def test_table_get_missing_returns_null_with_200(client):
    # Documents current behavior: unlike Study/Terminology, Table.get does not
    # check for a None result, so a missing id returns 200/null instead of 404.
    response = client.get("/api/Table/not-there")
    assert response.status_code == 200
    assert response.json is None


def test_table_post_creates_table(client, sample_terminology):
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

    table = Table.get(created["id"])
    assert table is not None

    terminology = table.terminology.dereference()
    table.delete(hard_delete=True)
    terminology.delete(hard_delete=True)


def test_table_post_missing_editor(client):
    body = {
        "name": "No Editor Table",
        "url": "http://ftd.unit.tests/api_table/no_editor",
    }

    response = client.post(
        "/api/Table", json=body, headers={"Content-Type": "application/json"}
    )
    assert response.status_code == 400


def test_table_put_updates_table(client, sample_terminology, basic_table):
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
    assert table.description == "Updated Description"


def test_table_put_missing_editor(client, sample_terminology, basic_table):
    updated = dict(client.get(f"/api/Table/{basic_table.id}").json)

    response = client.put(
        f"/api/Table/{basic_table.id}",
        json=updated,
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_delete(client, sample_terminology):
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


def test_table_delete_missing_editor(client, sample_terminology, basic_table):
    response = client.delete(
        f"/api/Table/{basic_table.id}",
        json={},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400

    # The table must still exist since the delete should have been rejected.
    assert Table.get(basic_table.id) is not None


def test_table_edit_put_adds_variable(client, sample_terminology, basic_table):
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
    variable = table.get_variable("new_field")
    assert variable is not None
    assert variable.description == "A brand new field"


def test_table_edit_put_missing_editor(client, sample_terminology, basic_table):
    response = client.put(
        f"/api/Table/{basic_table.id}/variable/new_field",
        json={"data_type": "string", "description": "A brand new field"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_edit_delete_variable(client, sample_terminology, basic_table):
    # TableEdit.delete matches on the variable's *name*, not its code, despite
    # the route/parameter being called "code".
    response = client.delete(
        f"/api/Table/{basic_table.id}/variable/{quote('String Var')}",
        json={"editor": "unit-test"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200

    table = Table.get(basic_table.id)
    assert table.get_variable("String Var") is None


def test_table_edit_delete_variable_not_found(client, sample_terminology, basic_table):
    response = client.delete(
        f"/api/Table/{basic_table.id}/variable/does_not_exist",
        json={"editor": "unit-test"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404


def test_table_edit_delete_missing_editor(client, sample_terminology, basic_table):
    response = client.delete(
        f"/api/Table/{basic_table.id}/variable/{quote('String Var')}",
        json={},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400

    table = Table.get(basic_table.id)
    assert table.get_variable("String Var") is not None


def test_table_rename_code_updates_name_and_description(
    client, sample_terminology, basic_table
):
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
    variable = table.get_variable("Renamed String Var")
    assert variable is not None
    assert variable.description == "Renamed Description"


def test_table_rename_code_requires_variable_or_description(
    client, sample_terminology, basic_table
):
    response = client.patch(
        f"/api/Table/{basic_table.id}/rename",
        json={"editor": "unit-test"},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_rename_code_missing_editor(client, sample_terminology, basic_table):
    response = client.patch(
        f"/api/Table/{basic_table.id}/rename",
        json={"variable": {"String Var": "Renamed String Var"}},
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_table_rename_code_variable_not_found(client, sample_terminology, basic_table):
    response = client.patch(
        f"/api/Table/{basic_table.id}/rename",
        json={
            "editor": "unit-test",
            "variable": {"Does Not Exist": "New Name"},
        },
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404


def test_harmony_table_csv_default(client, sample_terminology, basic_table):
    response = client.get(f"/api/Table/{basic_table.id}/harmony")
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_harmony_table_csv_invalid_format(client, sample_terminology, basic_table):
    response = client.get(
        f"/api/Table/{basic_table.id}/harmony", query_string={"format": "not-a-format"}
    )
    assert response.status_code == 400
