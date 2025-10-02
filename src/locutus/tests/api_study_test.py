from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from .test_study import basic_study

from locutus.model.study import Study
from locutus.model import GlobalID


def test_study_none(client):
    response = client.get("/api/Study/not-there")
    assert response.status_code == 404

def test_study_get(client, sample_terminology, basic_study):
    response = client.get("/api/Study")
    assert response.status_code == 200 

    studies = response.json
    assert len(studies) >= 1

    response = client.get(f"/api/Study/{basic_study.id}")
    assert response.status_code == 200

    study = response.json
    assert study['id'] == basic_study.id 
    assert study['title'] == basic_study.title 
    assert study['name'] == basic_study.name

    assert study['description'] == basic_study.description
