import pytest

from locutus.model.ontologies_search import OntologyAPI

from . import _Owner, client


@pytest.fixture
def ontology_apis():
    # These tests previously relied on OntologyAPI documents being pre-seeded
    # by hand in the target database. Seed the minimum records here so the
    # suite is self-contained and passes against a fresh database (e.g. in CI).
    apis = [
        OntologyAPI(
            api_id="ols", api_url="https://www.ebi.ac.uk/ols4/api", api_name="OLS"
        ),
        OntologyAPI(
            api_id="umls", api_url="https://uts-ws.nlm.nih.gov/rest", api_name="UMLS"
        ),
    ]
    for api in apis:
        api.save()
    yield apis
    for api in apis:
        api.delete(hard_delete=True)


def test_ontoapi_get_requires_auth(client):
    response = client.get("/api/OntologyAPI")
    assert response.status_code == 401


def test_ontoapi_get(client, ontology_apis):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/OntologyAPI")
        assert response.status_code == 200

        apis = response.json
        assert len(apis) >= 2
    finally:
        test_owner.cleanup()


def test_ontoapi_get_with_id(client, ontology_apis):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/OntologyAPI/ols")
        assert response.status_code == 200

        apis = response.json
        assert len(apis) == 1
    finally:
        test_owner.cleanup()


def test_ontoapi_get_with_id_not_found(client, ontology_apis):
    test_owner = _Owner(client)
    try:
        response = client.get("/api/OntologyAPI/not-a-real-api")
        assert response.status_code == 404
    finally:
        test_owner.cleanup()
