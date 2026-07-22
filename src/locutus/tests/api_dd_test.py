def test_dd_get(client, basic_study, basic_datadictionary):
    response = client.get("/api/DataDictionary")
    assert response.status_code == 200
    dds = response.json
    assert len(dds) >= 1

    response = client.get(f"/api/DataDictionary/{basic_datadictionary.id}")
    assert response.status_code == 200
    dd = response.json

    assert dd["id"] == basic_datadictionary.id
    assert dd["name"] == basic_datadictionary.name
    assert len(dd["tables"]) == len(basic_datadictionary.tables)

    assert dd["tables"][0] == basic_datadictionary.tables[0].dump()
