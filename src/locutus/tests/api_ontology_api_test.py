from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from .test_study import basic_study
from .test_table import basic_table 

# This test requires that the seed data has been loaded
def test_ontoapi_get(client):
    response = client.get("/api/OntologyAPI")
    assert response.status_code == 200 

    apis = response.json
    assert len(apis) >= 2

def test_ontoapi_get_with_id(client):
    response = client.get("/api/OntologyAPI/ols")
    assert response.status_code == 200 

    apis = response.json
    assert len(apis) == 1