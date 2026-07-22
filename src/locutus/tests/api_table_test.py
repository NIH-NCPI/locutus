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
