# Ontology API

Endpoints for the ontology-lookup services locutus can search against
(e.g. OLS), a user's default search preferences, and the generic
ontology search endpoint used by the front end's term picker.


## https://[APPURL]/api/OntologyAPI

### GET

Returns all availiable Ontology APIs and their details

```json
[
  {
    "api_name": "LOINC API",
    "api_id": "loinc",
    "api_url": "https://loinc.regenstrief.org/searchapi/",
    "ontologies": [
      {
        "ontology_code": "loinc",
        "ontology_title": "Logical Observation Identifiers, Names and Codes (LOINC)",
        "system": "https://loinc.regenstrief.org/searchapi/",
        "curie": "",
        "version": ""
      }
    ]
  },
  {
    "api_name": "Monarch API",
    "api_id": "monarch",
    "api_url": "https://api-v3.monarchinitiative.org/v3/api/search?q=",
    "ontologies": [
      {
        "ontology_code": "ecto",
        "ontology_title": "Environmental Conditions, Treatments and Exposures Ontology",
        "system": "https://api-v3.monarchinitiative.org/v3/api/search?q=",
        "curie": "ECTO",
        "version": ""
      }
    ]
  },
  {
    "api_name": "Ontology Lookup Service",
    "api_id": "ols",
    "api_url": "https://www.ebi.ac.uk/ols4/api/",
    "ontologies": [
      {
        "ontology_code": "ngbo",
        "ontology_title": " Next generation biobanking ontology(NGBO).",
        "system": "https://www.ebi.ac.uk/ols4/api/",
        "curie": "NGBO",
        "version": "http://purl.obolibrary.org/obo/ngbo/2022-10-05/ngbo.owl"
      }
    ]
  }
]
```

## https://[APPURL]/api/OntologyAPI/[API_ID]

### GET

Returns the details for the Ontology API denoted by the API_ID

```json
[
  {
    "api_name": "LOINC API",
    "api_id": "loinc",
    "api_url": "https://loinc.regenstrief.org/searchapi/",
    "ontologies": [
      {
        "ontology_code": "loinc",
        "ontology_title": "Logical Observation Identifiers, Names and Codes (LOINC)",
        "system": "https://loinc.regenstrief.org/searchapi/",
        "curie": "",
        "version": ""
      }
    ]
  },
  200,
  [["Content-Type", "application/fhir+json"]]
]
```

## https://[APPURL]/api/user/preferences/ontologies

### GET

Returns the default preferences for the user (TBD) or, if not set, then the application defaults.

```json
{
  "Application Default": {
    "api_preference": {
      "ols": ["mondo", "hp", "maxo", "ncit"]
    }
  }
}
```

In the example return above, no session existed, so we return this under the "Application Default". Otherwise, it will be associated with the user's ID (or email).

## https://[APPURL]/api/ontology_search?keyword=[KEYWORD]

### GET

Three parameters are available, the `keyword` parameter is required.

- keyword

  - Description: Keyword to search against the APIs
  - Required: YES

- selected_ontologies

  - Description: User selected Ontologies
  - Required: Yes

- selected_api

  - Description: APIs to include in the search
  - Choices:
    - `ols`: Gather data with the Ontology Lookup Service API.
  - Required: Yes

  - results_per_page

    - Description: Number of results requested from the ontology api.
    - Required: Yes

  - start_index
    - Description: The number/index of the first requested result.
    - Ex: with a results_per_page of 100, the first page of results would have a start_index of 0.
      For the second page of results the start_index would be 100.
    - Required: Yes

Example endpoint:

- https://[APPURL]/api/ontology_search?keyword=cat scratch fever&preferred_ontologies=CL,DUO&api=ols&results_per_page=100&start_index=0

The following are **example results** Not real data. <br>

```json
{
  "search_query": "https://www.ebi.ac.uk/ols4/api/search?q=cat%20scratch%20fever&ontology=CL,DUO",
  "results": [
    {
      "code": "NCBITaxon:9681",
      "system": "http://purl.obolibrary.org/obo/cl.owl",
      "code_iri": "http://purl.obolibrary.org/obo/NCBITaxon_9681",
      "display": "Felidae",
      "description": [],
      "ontology_prefix": "CL"
    },
    {
      "code": "NCBITaxon:9685",
      "system": "http://purl.obolibrary.org/obo/duo.owl",
      "code_iri": "http://purl.obolibrary.org/obo/NCBITaxon_9685",
      "display": "Felis catus",
      "description": [],
      "ontology_prefix": "DUO"
    }
  ],
  "results_per_ontology": {
    "CL": 1,
    "DUO": 1
  },
  "results_count": 2,
  "more_results_available": true
}
```
