# Study

Endpoints for managing studies, the top-level container that ties
together the data dictionaries used to describe a dataset.

## https://[APPURL]/api/Study

### GET

Returns all studies accessible by the user

```json
[
  {
    "identifier_prefix": "https://includedcc.org/fhir/htp",
    "description": "The Crnic Institute Human Trisome Project\u00ae (HTP) is an in-depth study of people with Down syndrome using the latest technologies in precision medicine.",
    "id": "HTP",
    "resource_type": "Study",
    "url": "https://includedcc.org/studies/human-trisome-project",
    "title": "Crnic Institute Human Trisome Project",
    "datadictionary": {
      "reference": "DataDictionary/INCLUDE"
    },
    "name": null
  }
]
```

### POST

Creates a new table resource. The body must contain the resource itself.

```json
[
  {
    "identifier_prefix": "https://includedcc.org/fhir/htp",
    "description": "The Crnic Institute Human Trisome Project\u00ae (HTP) is an in-depth study of people with Down syndrome using the latest technologies in precision medicine.",
    "url": "https://includedcc.org/studies/human-trisome-project",
    "title": "Crnic Institute Human Trisome Project",
    "datadictionary": {
      "reference": "DataDictionary/INCLUDE"
    },
    "name": null
  }
]
```

## https://[APPURL]/api/Study/[id]

### GET

Returns a study assocaited with the specified id.

## https://[APPURL]/api/Study/[id]

### PUT

Replaces the study at id with the resource contained in the body.

```json
[
  {
    "id": "htp",
    "identifier_prefix": "https://includedcc.org/fhir/htp",
    "description": "The Crnic Institute Human Trisome Project\u00ae (HTP) is an in-depth study of people with Down syndrome using the latest technologies in precision medicine.",
    "url": "https://includedcc.org/studies/human-trisome-project",
    "title": "Crnic Institute Human Trisome Project",
    "datadictionary": {
      "reference": "DataDictionary/INCLUDE"
    },
    "name": null
  }
]
```

### DELETE

Deletes the study at the given id

## https://[APPURL]/api/Study/[id]/dd/[datadictionary_id]

### DELETE

Removes a data dictionary from the study.

If successful, the entire study is returned (and the deletion should be
reflected in the response).

If the data dictionary doesn't exist, then a 404 error is returned.

