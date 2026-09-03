from unittest.mock import patch

import pytest

import locutus
from locutus.model.lookups import ResourceSingletonBase

from . import _Owner, client

ONTOLOGY_API_CACHE_KEY = ("OntologyAPI", True)


@pytest.fixture
def seeded_ontology_apis():
    # OntologyAPICollection is a singleton that caches the "OntologyAPI"
    # collection and only re-fetches once its TTL elapses (issues/021) --
    # too slow for a test. Popping its cache entry before and after this
    # fixture forces an immediate fresh read of what we seed here, and stops
    # this test from poisoning the cache for whatever test runs next.
    ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)

    doc_ref = locutus.persistence().collection("OntologyAPI").document()
    doc_id = doc_ref.set(
        {
            "api_id": "ols",
            "ontologies": {
                "MONDO": {
                    "system": "http://purl.obolibrary.org/obo/mondo.owl",
                    "curie": "MONDO",
                }
            },
        }
    )

    yield

    locutus.persistence().collection("OntologyAPI").document(str(doc_id)).delete()
    ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)


@pytest.fixture
def test_owner(client):
    owner = _Owner(client)
    yield owner
    owner.cleanup()


def _search_query(**overrides):
    query = {
        "keyword": "diabetes",
        "selected_ontologies": "MONDO",
        "selected_api": "ols",
        "results_per_page": "10",
        "start_index": "0",
    }
    query.update(overrides)
    return query


def test_ontology_search_requires_auth(client, seeded_ontology_apis):
    response = client.get("/api/ontology_search", query_string=_search_query())
    assert response.status_code == 401


def test_ontology_search_success(client, seeded_ontology_apis, test_owner):
    with patch(
        "locutus.model.ontologies_search.run_search",
        return_value={"results": [], "total": 0},
    ) as mock_run_search:
        response = client.get("/api/ontology_search", query_string=_search_query())

    assert response.status_code == 200
    assert response.json == {"results": [], "total": 0}
    mock_run_search.assert_called_once()


def test_ontology_search_missing_keyword(client, seeded_ontology_apis, test_owner):
    query = _search_query()
    del query["keyword"]
    response = client.get("/api/ontology_search", query_string=query)
    assert response.status_code == 400


def test_ontology_search_missing_selected_ontologies(
    client, seeded_ontology_apis, test_owner
):
    query = _search_query()
    del query["selected_ontologies"]
    response = client.get("/api/ontology_search", query_string=query)
    assert response.status_code == 400


def test_ontology_search_missing_selected_api(client, seeded_ontology_apis, test_owner):
    query = _search_query()
    del query["selected_api"]
    response = client.get("/api/ontology_search", query_string=query)
    assert response.status_code == 400


def test_ontology_search_missing_results_per_page(
    client, seeded_ontology_apis, test_owner
):
    query = _search_query()
    del query["results_per_page"]
    response = client.get("/api/ontology_search", query_string=query)
    assert response.status_code == 400


def test_ontology_search_missing_start_index(client, seeded_ontology_apis, test_owner):
    query = _search_query()
    del query["start_index"]
    response = client.get("/api/ontology_search", query_string=query)
    assert response.status_code == 400


def test_ontology_search_invalid_ontology_curie(
    client, seeded_ontology_apis, test_owner
):
    response = client.get(
        "/api/ontology_search",
        query_string=_search_query(selected_ontologies="NOT-A-REAL-ONTOLOGY"),
    )
    assert response.status_code == 400
