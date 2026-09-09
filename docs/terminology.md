# Terminology

Endpoints for managing terminologies -- collections of codes, their
mappings to public ontologies, and related metadata (rename, filters,
preferred terminology, provenance, user input on mappings).

## Terminologies:

### https://[APPURL]/api/Terminology

#### GET - Return all terminologies

Returns all terminologies user is allowed access to. (as of Apr 2024, the user has
access too all terminologies)

example:

```json
[
  {
    "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition_status",
    "description": null,
    "codes": [
      {
        "display": "Current",
        "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition_status",
        "code": "Current"
      },
      {
        "display": "Resolved",
        "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition_status",
        "code": "Resolved"
      },
      {
        "display": "History Of",
        "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition_status",
        "code": "History Of"
      }
    ],
    "id": "tm--2VjOxekLP8m28EPRqk95",
    "resource_type": "Terminology",
    "name": "condition_status"
  },
  {
    "url": "www.test.com/Sex",
    "description": null,
    "codes": [
      {
        "display": "",
        "system": "www.test.com/Sex",
        "code": "Female"
      },
      {
        "display": "",
        "system": "www.test.com/Sex",
        "code": "Male"
      },
      {
        "display": "",
        "system": "www.test.com/Sex",
        "code": "Other"
      },
      {
        "display": "",
        "system": "www.test.com/Sex",
        "code": "Unknown"
      }
    ],
    "id": "tm-5AKcaQ-QLe3REWzaJYoUA",
    "resource_type": "Terminology",
    "name": "Sex"
  }
]
```

#### POST - Create new Terminology

Create a new terminology. The new terminology should be sent in the body of the request.

```json
{
  "url": "www.test.com/Sex",
  "description": null,
  "codes": [
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Female"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Male"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Other"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Unknown"
    }
  ],
  "name": "Sex"
}
```

When POSTing, the API will create an ID for new entry.

### https://[APPURL]/api/Terminology/[id]

Actions relating to a specific terminology based on the ID

#### GET

Returns the terminology

```json
{
  "url": "www.test.com/Sex",
  "description": null,
  "codes": [
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Female"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Male"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Other"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Unknown"
    }
  ],
  "id": "tm-5AKcaQ-QLe3REWzaJYoUA",
  "resource_type": "Terminology",
  "name": "Sex"
}
```

#### PUT

Replace terminology at the given ID

```json
{
  "url": "www.test.com/Sex",
  "description": null,
  "codes": [
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Female"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Male"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Other"
    },
    {
      "display": "",
      "system": "www.test.com/Sex",
      "code": "Unknown"
    }
  ],
  "id": "tm-5AKcaQ-QLe3REWzaJYoUA",
  "resource_type": "Terminology",
  "name": "Sex",
  "editor": "test_editor"
}
```

#### DELETE

Removes a terminology from the database. This will remove all mappings that
have been assigned to the terminology.

WARNING: As of April 2024, deleting a Terminology does not remove it from
tables that reference it.

## Terminology Edit

For convenience, one can add and remove codes from a terminology using basic
PUT and DELETE calls

### https://[APPURL]/api/Terminology/[id]/code/[code]

#### PUT

Adds a new code (with a matching display) to the terminology.

```json
{
  "display": "New Code's Display"
}
```

Response will be the entire Terminology including the newly added code.

```json (response)
{
  "id": "tm-r5l1w5u-dJ0yNEkrkCcZu",
  "name": "condition",
  "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition",
  "description": null,
  "codes": [
    {
      "code": "Participant External ID",
      "display": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Event ID",
      "display": "Identifier for event (Visit, Survey completion, Sample collection, etc.) to which the Condition data are linked, if applicable. There may be multiple events linked to a Participant.",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Measure Value",
      "display": "Numeric value of Measure",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Measure Unit",
      "display": "Unit that is associated with Measure Value (e.g. kg, cm, %, x10^9/L, etc.)",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "newcode",
      "display": "New Code's Display",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    }
  ],
  "resource_type": "Terminology"
}
```

If the code exists already, the system fails with a 400 error.

#### DELETE

Removes a code from the terminology (this will also remove all mappings for
that code)

Return is the entire terminology minus the deleted code.

If the code doesn't exist, a 404 error is returned.

```json (response)
{
  "id": "tm-r5l1w5u-dJ0yNEkrkCcZu",
  "name": "condition",
  "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition",
  "description": null,
  "codes": [
    {
      "code": "Participant External ID",
      "display": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Event ID",
      "display": "Identifier for event (Visit, Survey completion, Sample collection, etc.) to which the Condition data are linked, if applicable. There may be multiple events linked to a Participant.",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Measure Value",
      "display": "Numeric value of Measure",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    },
    {
      "code": "Measure Unit",
      "display": "Unit that is associated with Measure Value (e.g. kg, cm, %, x10^9/L, etc.)",
      "system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/condition/condition"
    }
  ],
  "resource_type": "Terminology"
}
```

## Terminology Mappings

### https://[APPURL]/api/Terminology/[id]/mapping

#### GET

Returns all VALID mappings currently assigned to any code in the terminology.
Optionally, it can include additional user input data if the user_input parameter is provided.<br>
Example endpoint: https://[APPURL]/api/Terminology/[id]/mapping?user_input=True)

```json
{
  "terminology": {
    "Reference": "Terminology/tm-C8IP8Cw_0M_hHWeLl5WP3"
  },
  "mappings": [
    {
      "code": "Female",
      "codes": [
        {
          "code": "female",
          "display": "Female",
          "mapping_relationship": "",
          "system": "http://hl7.org/fhir/administrative-gender",
          "valid": true
        }
      ]
    }
  ]
}
```

User_input example output. An active session is required to retrieve the 'users_vote'.
If none exists, 'users_vote' will be an empty string.

```json
{
  "terminology": {
    "Reference": "Terminology/tm-C8IP8Cw_0M_hHWeLl5WP3"
  },
  "mappings": [
    {
      "code": "Female",
      "codes": [
        {
          "code": "female",
          "display": "Female",
          "mapping_relationship": "",
          "system": "http://hl7.org/fhir/administrative-gender",
          "valid": true,
          "user_input": {
            "comments_count": 1,
            "votes_count": {
              "up": 1,
              "down": 0
            },
            "users_vote": "up"
          }
        }
      ]
    }
  ]
}
```

#### DELETE

Soft deletes all mappings associated with all codes in the given terminology.
The 'valid' field for the mapping is set to 'false'

### https://[APPURL]/api/Terminology/[id]/mapping/[code]

#### GET

Returns VALID mappings for the specific code (from the terminology)
Optionally, it can include additional user input data if the user_input parameter is provided.<br>
Example endpoint: https://[APPURL]/api/Terminology/[id]/mapping/[code]?user_input=True)

```json
{
  "codes": [
    {
      "code": "female_ex",
      "codes": [
        {
          "code": "femalee",
          "display": "feMale",
          "mapping_relationship": "equivalent",
          "system": "http://hl7.org/fhir/administrative-gender",
          "valid": true
        }
      ]
    }
  ],
  "terminology": {
    "Reference": "Terminology/tm-C8IP8Cw_0M_hHWeLl5WP3"
  }
}
```

User_input example output. An active session is required to retrieve the 'users_vote'.
If none exists, 'users_vote' will be an empty string.

```json
{
  "codes": [
    {
      "code": "female_ex",
      "codes": [
        {
          "code": "femalee",
          "display": "feMale",
          "mapping_relationship": "equivalent",
          "system": "http://hl7.org/fhir/administrative-gender",
          "valid": true,
          "user_input": {
            "comments_count": 1,
            "votes_count": {
              "up": 1,
              "down": 0
            },
            "users_vote": "up"
          }
        }
      ]
    }
  ],
  "terminology": {
    "Reference": "Terminology/tm-C8IP8Cw_0M_hHWeLl5WP3"
  }
}
```

#### PUT

Set mappings for a specific code inside the given terminology. The body must
contain all codings (i.e. it replaces anything that may already be there)

Example Body:

```json
{
  "mappings": [
    {
      "code": "Major depressive disorder",
      "display": "",
      "description": "",
      "system": "https://anvil-all-terms.org/fhir/disease_1",
      "mapping_relationship": "equivalent"
    }
  ],
  "editor": "user525600"
}
```

The response from the PUT is a listing of all mappings for that terminology
after the change.

#### DELETE

Soft delete the mappings currently associated with the given code from the specified
terminology. The mappings 'valid' field will be set to 'false'

The response is a listing of all mappings for that terminology
after the change.

### https://[APPURL]/api/Terminology/[id]/rename

#### PATCH

Renames code(s) with new names.

This PATCH method does not conform to the standard guidelines which permit
updates to any property within the resource. Instead it is intended solely
for renaming codes inside a terminology. The body of the call will be an object 
with one to three keys, "code", "display" or "description" (a valid rename must
have one of the two). Each of those keys will point to an object whose keys
match a term within the current terminology. Those key's values represent the
new value after the change.

For Example:

```json
{
  "code": {
    "Female": "Woman"
  },
  "display": {
    "Female": "Woman"
  }
}
```

Will replace the code, _Female_, with _Woman_ as well as update the display to
match. This includes assigning all mappings from the code, _Female_, to the
newly named code, _Woman_. The body object can contain more than one key/value
pair which will indicate the intent to rename multiple codes in a single PATCH
call.

If one or more of the "Old Code" entries doesn't exist in the terminology,
a 404 "Not Found" error is returned.

If the root object in the body is missing both the "code" and the "display",
a 400 error is returned.

Upon completion, 200 is returned along with the full set of mappings for the
terminology.

```json
{
  "terminology": {
    "Reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
  },
  "codes": [
    {
      "code": "Male",
      "mappings": [
        {
          "code": "male",
          "display": "Male",
          "system": "http://hl7.org/fhir/administrative-gender"
        }
      ]
    },
    {
      "code": "Woman",
      "mappings": [
        {
          "code": "female",
          "display": "Female",
          "system": "http://hl7.org/fhir/administrative-gender"
        }
      ]
    }
  ]
}
```

### https://[APPURL]/api/Terminology/[id]/filter

<h4 id="term_id_filter_get">GET</h4>

Return the api search preference for the terminology (specified by id).<br>
Returns the api search preferences at the Terminology("self") level. <br> Expected return example below.

Optionally, the endpoint can be implemented to fallback to the `Table`s preferrences if the `table_id` is provided.<br> The endpoint will 'fallback' only if there are no preferences for the `Terminology`.

Example endpoint: https://[APPURL]/api/Terminology/[id]/filter?table_id=[table_id]

```json
{
  "self": {
    "api_preference": {
      "ex_api": ["ontology1", "onto2"]
    }
  }
}
```

#### PUT

Update a api search preference for the terminology (specified by id). <br>
See the [POST request](#term_id_filter_post) for this endpoint for a
request body example

<h4 id="term_id_filter_post">POST</h4>

Create the api search preference for the terminology (specified by id). <br>
Request body example:

```json
{
  "api_preference": {
    "ex_api": ["ex_onto", "ex_onto2"]
  }
}
```

#### DELETE

Delete the api search preference for the terminology (specified by id). <br>
This is the expected result after removing preferences with the URL without specifying a code.

```json
{}
```

### https://[APPURL]/api/Terminology/[id]/filter/[code]

<h4 id="term_id_filter_code_get">GET</h4>

Return the api search preference for the code within a specific terminology
(specified by id).<br>

The response below would be the result of specifying 'T21' as the `code` in the request.<br>

- If preferences for the `code` do not exist the endpoint will fallback to use any
  preferences found for the `Terminology`(code:'self'). Example seen [HERE](#httpsappurlapiterminologyidfilter)<br>
- If preferences for neither the `code` nor the `Terminology` exist an empty object
  is returned.<br>

Optionally, the endpoint can be implemented to fallback to the `Table`s preferrences if the `table_id` is provided.<br> The endpoint will 'fallback' only if there are no preferences for the `Terminology`.

Example endpoint: https://[APPURL]/api/Terminology/[id]/filter/[code]?table_id=[table_id]

```json
{
  "T21": {
    "api_preference": {
      "ex_api": ["ex_onto", "ex_onto2"]
    }
  }
}
```

#### PUT

Create a api search preference for the code within a specific terminology (specified by id). <br>
See [POST request](#term_id_filter_code_post) for an example request body.

<h4 id="term_id_filter_code_post">POST</h4>

Update the api search preference for the code within a specific terminology (specified by id). <br>
In the example below T21 was specified as the code.<br> Check out the [GET request](#term_id_filter_code_get) of this endpoint for a visual of the created preference.
Request body example:

```json
{
  "api_preference": {
    "ex_api": ["ex_onto", "ex_onto2"]
  }
}
```

#### DELETE

Delete the api search preference for the code within a specific terminology (specified by id). <br> \
This is the expected result after removing preferences with the URL code specifying 'T21'.

```json
{
  "T21": {}
}
```

### https://[APPURL]/api/Terminology/[id]/preferred_terminology

#### GET

Return the reference to the preferred_terminology related to the `Terminology` (specified by id).<br>
Returns the preferred_terminology at the Terminology("self") level. <br> Expected return example below.

Optionally, the endpoint can be implemented to fallback to the `Table`s preferrences if the `table_id` is provided.<br> The endpoint will 'fallback' only if there are no preferences for the `Terminology`.

Example endpoint: https://[APPURL]/api/Terminology/[id]/preferred_terminology?table_id=[table_id]

```json
{
  "references": [
    {
      "reference": "Terminology/tm--example1"
    },
    {
      "reference": "Terminology/tm--example2"
    }
  ]
}
```

#### PUT

Create or replace references to a prefered `Terminology` for the terminology (specified by id). <br>
Request body example:

```json
{
  "editor": "user24601",
  "preferred_terminologies": [
    {
      "preferred_terminology": "tm--example1"
    },
    {
      "preferred_terminology": "tm--example6"
    }
  ]
}
```

#### DELETE

Running the DELETE request will remove the preferred_terminology collection
from the `Terminology` specified by the id

### https://[APPURL]/api/Terminology/[id]/user_input/[code]/mapping/[mapped_code]/[type]

- id (str): The document ID.
- code (str): The target document (mapping) identifier.
- mapped_code (str): The code being mapped to the target.
- type (str): The type of input to retrieve
  - currently available: "mapping_conversations","mapping_votes".

#### GET

Return the reference to the `user_input` `type` related to the `Terminology` (specified by id).<br>
Returns all records of the `type` at the `code` level, in reverse order
from whence they were stored, with newer records on top.

Expected return for type `mapping_votes` below

```json
{
  "Terminology": "tm-C8IP8Cw_0M_hHWeLl5WP3",
  "code": "type 2 diabetes",
  "mapped_code": "Type 2 diabetes mellitus",
  "mapping_votes": {
    "user24601": {
      "date": "Nov 17, 2024, 01:58:39.197679 PM",
      "vote": "up"
    }
  }
}
```

Expected return for type `mapping_conversations` below

```json
{
  "Terminology": "tm--2VjOxekLP8m28EPRqk95",
  "code": "type 2 diabetes",
  "mapped_code": "Type 2 diabetes mellitus",
  "mapping_conversations": [
    {
      "date": "Oct 04, 2024, 04:17:43.043579 PM",
      "user_id": "user24601",
      "note": "I like this mapping"
    },
    {
      "date": "Oct 04, 2024, 04:21:15.460040 PM",
      "user_id": "user525600",
      "note": "I dont like this mapping"
    }
  ]
}
```

#### PUT

Create a `user_input` record of the `type` specified in `Terminology`(specified by id). <br>

Request body example for `mapping_conversations` :

# editor is only required if not using sessions

```json
{
  "editor": "user24601",
  "note": "I dont like this mapping"
}
```

Request body example for `mapping_votes` :

# editor is only required if not using sessions

```json
{
  "editor": "user525600",
  "vote": "up"
}
```

### https://[APPURL]/api/Terminology/[id]/mapping_relationship/[code]/mapping/[mapped_code]

There is not currently a endpoint for getting a mappings(code/mapped_code) relationship
alone. Use the endpoint for getting all mappings for a single code. [more here](#httpsappurlapiterminologyidmappingcode)

A mapping may not have the mapping_relationship value set. But a returned
mapping will always have a mapping_relationship attribute.

#### PUT - Updating a mapping_relationship

Mapping_relationship can be set to the codes in the `ftd-concept-map-relationship` `Terminology` or to an empty string "". <br>
Current `ftd-concept-map-relationship` codes(subject to change): [`equivalent`,`source-is-narrower-than-target`,`source-is-broader-than-target` ]

```json
{
  "mapping_relationship": "equivalent",
  "editor": "user24601"
}
```

## Terminology Provenance

Provenance is tracked for all changes to a terminology or one of the terms
associated with the terminology. This includes adding and removing codes,
editing code properties as well as adding and removing mappings.

### https://[APPURL]/api/Provenance/Terminology/[id]

#### GET

This endpoint will return changes to the terminology itself, including adding,
editing and removing codes.

See [Table](table.md) provenance for more details.

### https://[APPURL]/api/Provenance/Terminology/[id]/code/[code]

This endpoint will return the provenance associated with the mappings of a
single code within the terminology.

See [Table](table.md) provenance for more details.

