from .test_datadictionary import basic_datadictionary 
from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from .test_study import basic_study
from .test_table import basic_table 

def test_dd_get(client, basic_study, basic_datadictionary):
    response = client.get("/api/DataDictionary")
    assert response.status_code == 200 
    dds  = response.json 
    assert len(dds) >= 1

    response = client.get(f"/api/DataDictionary/{basic_datadictionary.id}")
    assert response.status_code == 200 
    dd = response.json 

    assert dd['id'] == basic_datadictionary.id 
    assert dd['name'] == basic_datadictionary.name  
    assert len(dd['tables']) == len(basic_datadictionary.tables)

    assert dd['tables'][0] == basic_datadictionary.tables[0].dump()

