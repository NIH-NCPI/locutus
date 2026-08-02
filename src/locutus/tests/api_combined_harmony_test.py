from . import client
from .test_study import basic_study
from .test_table import basic_table
from .test_terminology import sample_terminology


def test_combined_harmony_no_ids(client):
    response = client.get("/api/harmony")
    assert response.status_code == 200
    assert response.json == []


def test_combined_harmony_with_study(client, sample_terminology, basic_study):
    response = client.get("/api/harmony", query_string={"studies": basic_study.id})
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_combined_harmony_with_table(client, sample_terminology, basic_table):
    response = client.get("/api/harmony", query_string={"tables": basic_table.id})
    assert response.status_code == 200
    assert isinstance(response.json, list)


def test_combined_harmony_invalid_format(client):
    response = client.get("/api/harmony", query_string={"format": "not-a-format"})
    assert response.status_code == 400


def test_combined_harmony_unknown_ids_skip_silently(client):
    # Unlike almost every other resource in this codebase, build_combined_harmony
    # checks each id for None before using it, so unknown ids are silently
    # skipped rather than causing a crash or a 404.
    response = client.get(
        "/api/harmony",
        query_string={
            "studies": "not-there",
            "datadictionaries": "not-there",
            "tables": "not-there",
        },
    )
    assert response.status_code == 200
    assert response.json == []
