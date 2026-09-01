from datetime import UTC, datetime, timedelta

import locutus
from locutus.model.lookups import OntologyAPICollection, ResourceSingletonBase

ONTOLOGY_API_CACHE_KEY = ("OntologyAPI", True)


def _seed_ontology_api(api_id):
    doc_ref = locutus.persistence().collection("OntologyAPI").document()
    doc_id = doc_ref.set({"api_id": api_id, "ontologies": {}})
    return str(doc_id)


def _clear_ontology_api_collection():
    for doc in locutus.persistence().collection("OntologyAPI").stream():
        locutus.persistence().collection("OntologyAPI").document(doc.id).delete()


def test_ontology_api_collection_caches_within_ttl():
    ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)
    _clear_ontology_api_collection()
    doc_id = _seed_ontology_api("ols")

    try:
        first_read = OntologyAPICollection().get_cached_resource()
        assert len(first_read) == 1

        # A second seed without expiring the cache should not be visible yet --
        # this is the caching behavior working as intended, not the bug.
        _seed_ontology_api("bioportal")
        still_cached = OntologyAPICollection().get_cached_resource()
        assert len(still_cached) == 1
    finally:
        locutus.persistence().collection("OntologyAPI").document(doc_id).delete()
        _clear_ontology_api_collection()
        ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)


def test_ontology_api_collection_refreshes_after_ttl_expires():
    """Pins the issues/021 fix: once _cache_ttl elapses, the next access
    re-fetches from the DB instead of serving stale data forever."""
    ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)
    _clear_ontology_api_collection()
    doc_id = _seed_ontology_api("ols")

    try:
        stale_count = len(OntologyAPICollection().get_cached_resource())
        assert stale_count == 1

        _seed_ontology_api("bioportal")

        # Force the cached instance to look expired without waiting out the
        # real TTL.
        instance = ResourceSingletonBase._instances[ONTOLOGY_API_CACHE_KEY]
        instance._cached_at = (
            datetime.now(UTC) - timedelta(seconds=1) - OntologyAPICollection._cache_ttl
        )

        refreshed = OntologyAPICollection().get_cached_resource()
        assert len(refreshed) == 2
    finally:
        locutus.persistence().collection("OntologyAPI").document(doc_id).delete()
        _clear_ontology_api_collection()
        ResourceSingletonBase._instances.pop(ONTOLOGY_API_CACHE_KEY, None)
