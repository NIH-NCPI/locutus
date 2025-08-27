from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from .test_table import basic_table
from locutus.model.table import Table
from locutus.model import GlobalID

def test_table_get(client, sample_terminology, basic_table):
    response = client.get("/api/Table")
    assert response.status_code == 200 

    tables = response.json
    assert len(tables) >= 1

    response = client.get(f"/api/Table/{basic_table.id}")
    assert response.status_code == 200 

    table = response.json 
    assert table['id'] == basic_table.id 
    assert table['name'] == basic_table.name