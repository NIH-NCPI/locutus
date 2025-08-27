from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from locutus.model.terminology import Terminology
from locutus.model.coding import Coding
from locutus.model import GlobalID

import pdb

def test_terminology_get(client, ftd_concept_relationships, sample_terminology):
    terms = client.get('/api/Terminology', content_type="application/json").json

    assert len(terms) >= 2

    term = client.get("/api/Terminology/ftd-concept-map-relationship")
    assert term.status_code == 200
    term = term.json
    assert term['id'] == "ftd-concept-map-relationship"
    assert len(term['codes']) == 3
    assert term['codes'][0]['code'] == "equivalent"
    assert term['codes'][1]['display'] == 'Source Is Narrower Than Target' 
    assert term['codes'][1]['description'] == "The source concept is narrower in meaning than the target concept."
    assert term['codes'][2]['system'] == "http://hl7.org/fhir/concept-map-relationship"

    term = client.get("/api/Terminology/ontology-one").json
    assert term['id'] == "ontology-one"
    assert term['name'] == "Ontology One"
    assert len(term['codes']) == 2

def test_terminology_rename(client):
    term_body={
        "id": "ontology-two",
        "name": "Ontology Two",
        "url": "http://example.com/ont1",
        "description": "A sample oncology terminology",
        "codes": [
            {
                "code": "C1",
                "display": "Code One",
                "description": "Description for C1"
            },
            {
                "code": "C2",
                "display": "Code Two",
                "description": "'Description for C2"
            }
        ],
        "editor": "test-user"
    }

    response = client.post("/api/Terminology", 
                            json=term_body, 
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 201

    response = client.patch(f"/api/Terminology/ontology-two/rename",
                            json={
                                "editor": "unit-test",
                                "code": {
                                    "C1": "Code01"
                                }
                            }, 
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 201

    term = Terminology.get("ontology-two")
    assert term.codes[0].code == "Code01"

    response = client.patch(f"/api/Terminology/ontology-two/rename",
                            json={
                                "editor": "unit-test",
                                "display": {
                                    "C2": "second code"
                                },
                                "description": {
                                    "C2": "second desc"
                                }
                            }, 
                            headers={"Content-Type": "application/json"})  

    assert response.status_code == 201

    term = Terminology.get("ontology-two")
    assert term.codes[1].display == "second code"
    assert term.codes[1].description == "second desc"

    term.delete(hard_delete=True)

def test_terminology_delete(client):
    term_body={
        "name": "Ontology Two",
        "url": "http://example.com/ont1",
        "description": "A sample oncology terminology",
        "codes": [
            {
                "code": "C1",
                "display": "Code One",
                "description": "Description for C1"
            },
            {
                "code": "C2",
                "display": "Code Two",
                "description": "'Description for C2"
            }
        ],
        "editor": "test-user"
    }

    response = client.post("/api/Terminology", 
                            json=term_body, 
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 201

    term = response.json
    term_id = term['id']

    get_term = client.get(f"/api/Terminology/{term_id}")
    response = client.delete(f"/api/Terminology/{term_id}")
    assert response.status_code == 200

    response = client.get(f"/api/Terminology/{term_id}")

    assert response.status_code == 404

    gid = GlobalID(resource_type="Terminology", 
                    key="http://example.com/ont1:Ontology Two")
    gid.delete()

def test_terminology_put(client):
    term_body={
        "id": "ontology-three",
        "name": "Ontology Three",
        "url": "http://example.com/ont3",
        "description": "A sample oncology terminology",
        "codes": [
            {
                "code": "C1",
                "display": "Code One",
                "description": "Description for C1"
            },
            {
                "code": "C2",
                "display": "Code Two",
                "description": "'Description for C2"
            }
        ],
        "editor": "test-user"
    }

    response = client.put("/api/Terminology/ontology-three", 
                            json=term_body, 
                            headers={"Content-Type": "application/json"})
    
    assert response.status_code == 200

    term = response.json
    assert term['id'] == "ontology-three"
    term_id = term['id']
    assert len(term['codes']) == 2

    get_term = client.get(f"/api/Terminology/{term_id}")
    assert len(term['codes']) == 2
    assert term['codes'][0]['code'] == "C1"
    assert term['codes'][1]['display'] == "Code Two"

    # response = client.delete(f"/api/Terminology/{term_id}")
    term = Terminology.get(term_id)
    term.delete(hard_delete=True)


def test_terminology_add_and_delete_code(client):
    term_body={
        "id": "ontology-three",
        "name": "Ontology Three",
        "url": "http://example.com/ont3",
        "description": "A sample oncology terminology",
        "codes": [
            {
                "code": "C1",
                "display": "Code One",
                "description": "Description for C1"
            },
            {
                "code": "C2",
                "display": "Code Two",
                "description": "'Description for C2"
            }
        ],
        "editor": "test-user"
    }

    response = client.put("/api/Terminology/ontology-three", 
                            json=term_body, 
                            headers={"Content-Type": "application/json"})
    
    assert response.status_code == 200

    term = response.json
    assert term['id'] == "ontology-three"
    term_id = term['id']
    assert len(term['codes']) == 2

    new_code = {
        "code": "C3",
        "display": "Code Three",
        "description": "Great Description",
        "editor": "unit-test"
    }
    response = client.put(f"/api/Terminology/ontology-three/code/{new_code['code']}",
                            json=new_code, 
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 201 

    term = client.get(f"/api/Terminology/{term_id}").json
    assert len(term['codes']) == 3
    assert term['codes'][2]['code'] == "C3"
    assert term['codes'][2]['display'] == "Code Three"

    new_coding_id = term['codes'][2]['id']

    response = client.delete(f"/api/Terminology/ontology-three/code/{new_code['code']}",
                            json={"editor": "unit-test"})
    assert response.status_code == 200 
    term = client.get(f"/api/Terminology/{term_id}").json
    assert len(term['codes']) == 2

    coding = Coding.get(new_coding_id)
    coding.delete()    

    # response = client.delete(f"/api/Terminology/{term_id}")
    term = Terminology.get(term_id)
    term.delete(hard_delete=True)

def test_terminology_post(client):
    term_body={
        "name": "Ontology Two",
        "url": "http://example.com/ont1",
        "description": "A sample oncology terminology",
        "codes": [
            {
                "code": "C1",
                "display": "Code One",
                "description": "Description for C1"
            },
            {
                "code": "C2",
                "display": "Code Two",
                "description": "'Description for C2"
            }
        ],
        "editor": "test-user"
    }

    response = client.post("/api/Terminology", 
                            json=term_body, 
                            headers={"Content-Type": "application/json"})
    assert response.status_code == 201

    term = response.json
    term_id = term['id']
    assert len(term['codes']) == 2

    get_term = client.get(f"/api/Terminology/{term_id}")
    assert len(term['codes']) == 2
    assert term['codes'][0]['code'] == "C1"
    assert term['codes'][1]['display'] == "Code Two"

    # response = client.delete(f"/api/Terminology/{term_id}")
    term = Terminology.get(term_id)
    term.delete(hard_delete=True)

    gid = GlobalID(resource_type="Terminology", 
                    key="http://example.com/ont1:Ontology Two")
    gid.delete()


