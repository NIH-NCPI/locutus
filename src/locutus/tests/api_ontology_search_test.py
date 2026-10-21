import pytest
from term_wyrm import SearchService
from term_wyrm.apis import ApiError

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


class FakeHttp:
    """Stands in for term-wyrm's HTTP client; answers every OLS search with
    one MONDO term and records the parameters it was sent."""

    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def get_json(self, url, params=None):
        self.calls.append((url, dict(params or {})))
        if self.error:
            raise self.error
        return {
            "response": {
                "numFound": 100,
                "docs": [
                    {
                        "obo_id": "MONDO:0005015",
                        "ontology_prefix": "MONDO",
                        "iri": "http://purl.obolibrary.org/obo/MONDO_0005015",
                        "label": "diabetes mellitus",
                        "description": ["A metabolic disease."],
                    }
                ],
            }
        }


@pytest.fixture
def fake_http(monkeypatch):
    http = FakeHttp()
    monkeypatch.setattr(
        "locutus.model.ontologies_search.SearchService",
        lambda apis: SearchService(apis, http=http),
    )
    return http


def test_ontology_search_success(client, seeded_ontology_apis, test_owner, fake_http):
    response = client.get(
        "/api/ontology_search",
        query_string=_search_query(results_per_page="10", start_index="2"),
    )
    assert response.status_code == 200

    # start_index is a 0-based page number; OLS takes a row offset.
    [(url, params)] = fake_http.calls
    assert url.endswith("/search")
    assert params == {"q": "diabetes", "ontology": "mondo", "start": 20, "rows": 10}

    body = response.json
    assert body["results"] == [
        {
            "code": "MONDO:0005015",
            "system": "http://purl.obolibrary.org/obo/mondo.owl",
            "code_iri": "http://purl.obolibrary.org/obo/MONDO_0005015",
            "display": "diabetes mellitus",
            "description": ["A metabolic disease."],
            "ontology_prefix": "MONDO",
        }
    ]
    assert body["results_count"] == 1
    assert body["results_per_ontology"] == {"MONDO": 1}
    assert body["more_results_available"] is True
    assert body["search_query"].startswith("https://www.ebi.ac.uk/ols4/api/search?")
    assert body["failures"] == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"selected_api": "nope"},
        {"selected_api": "olsd"},  # hierarchy only; can't search
        {"start_index": "first"},
        {"start_index": "-1"},
        {"results_per_page": "501"},
    ],
)
def test_ontology_search_bad_values_return_400(
    client, seeded_ontology_apis, test_owner, fake_http, overrides
):
    response = client.get(
        "/api/ontology_search", query_string=_search_query(**overrides)
    )
    assert response.status_code == 400
    assert fake_http.calls == []


def test_ontology_search_all_apis_failed_returns_502(
    client, seeded_ontology_apis, test_owner, fake_http
):
    fake_http.error = ApiError("HTTP 503", "https://www.ebi.ac.uk/ols4/api/search", 503)
    response = client.get("/api/ontology_search", query_string=_search_query())
    assert response.status_code == 502
    assert "ols: HTTP 503" in response.json["message"]


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
