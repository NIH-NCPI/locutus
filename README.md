# Locutus

Locutus provides the backend for a web based terminology mapping tool in the very early stages of development. The goal of the application is to provide a collaborative environment to harmonize dataset terms with public ontologies such as MeSH, HPO and others.

There isn't much here at this time, but there are some example data based on a real research data-dictionary along with standard CRUD functionality.

API Functionality:

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
  "name": "Sex"
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

Returns all mappings currently assigned to any code in the terminology.

```json
{
  "terminology": {
    "Reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
  },
  "codes": [
    {
      "code": "Female",
      "mappings": [
        {
          "code": "female",
          "display": "Female",
          "system": "http://hl7.org/fhir/administrative-gender"
        }
      ]
    },
    {
      "code": "Male",
      "mappings": [
        {
          "code": "male",
          "display": "Male",
          "system": "http://hl7.org/fhir/administrative-gender"
        }
      ]
    }
  ]
}
```

#### DELETE

Removes all mappings associated with all codes in the given terminology.

### https://[APPURL]/api/Terminology/[id]/mapping/[code]

#### GET

Returns mappings for the specific code (from the terminology)

```json
{
  "code": "Female",
  "mappings": [
    {
      "code": "female",
      "display": "Female",
      "system": "http://hl7.org/fhir/administrative-gender"
    }
  ]
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
      "code": "male",
      "display": "Male",
      "system": "http://hl7.org/fhir/administrative-gender"
    }
  ]
}
```

The response from the PUT is a listing of all mappings for that terminology
after the change.

#### DELETE

Remove the mappings currently associated with the given code from the specified
terminology.

The response is a listing of all mappings for that terminology
after the change.

### https://[APPURL]/api/Terminology/[id]/rename

#### PATCH

Renames code(s) with new names.

This PATCH method does not conform to the standard guidelines which permit
updates to any property within the resource. Instead it is intended solely
for renaming codes inside a terminology. The body of the call will include will
be an object with one or two keys, "code" and "display" (a valid rename must
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

#### GET

Return the api search preference for the terminology (specified by id).
Returns the api search preferences at the Terminology level

```json
{
    "ex_api": [
        "ex_onto",
        "ex_onto2"
    ]
}
```

#### PUT

Create a api search preference for the terminology (specified by id). 
The request body and results will look very similar to the examples given 
with the POST request for this endpoint.

#### POST

Update the api search preference for the terminology (specified by id). 
Define the api_preference at the Terminology level.
```json
{
    "api_preference": {
        "ex_api": [
            "ex_onto",
            "ex_onto2"
        ]
    },
    "codes": [
        
    ],
    "description": null,
    "id": "tm-4rFpmPLohHdOb3fllr1l7",
    "name": "Down_Syndrome_Status",
    "resource_type": "Terminology",
    "url": "www.test.com/Down_Syndrome_Status"
}
```
#### DELETE

Delete the api search preference for the terminology (specified by id).
Checkout this endpoint's POST request to see an example of the data that 
would be removed.

### https://[APPURL]/api/Terminology/[id]/filter/[code]

#### GET

Return the api search preference for the code within a specific terminology
(specified by id).

```json
{
    "ex_api": [
        "ex_onto",
        "ex_onto2"
    ]
}
```

#### PUT

Create a api search preference for the code within a specific terminology (specified by id).
The request body and results will look very similar to the examples given 
with the POST request for this endpoint.

#### POST

Update the api search preference for the code within a specific terminology
(specified by id).
In the example below T21 was specified as the code.
```json
{
    "codes": [
        {
            "api_preference": {
                "ex_api": [
                    "ex_onto",
                    "ex_onto2"
                ]
            },
            "code": "T21", 
            "description": "",
            "display": "Trisomy 21 (Down syndrome)",
            "system": "www.test.com/Down_Syndrome_Status"
        }
    ],
}
```

#### DELETE

Delete the api search preference for the code within a specific terminology 
(specified by id).  
Checkout this endpoint's POST request to see an example of the data that 
would be removed.

## Terminology Provenance
Provenance is tracked for all changes to a terminology or one of the terms 
associated with the terminology. This includes adding and removing codes, 
editing code properties as well as adding and removing mappings. 

### https://[APPURL]/api/Provenance/Terminology/[id]
#### GET
This endpoint will return changes to the terminology itself, including adding,
editing and removing codes. 

Please see the documentation for the Table provenance for more details.

### https://[APPURL]/api/Provenance/Terminology/[id]/code/[code]
This endpoint will return the provenance associated with the mappings of a 
single code within the terminology. 

Please see the documentation for the Table provenance for more details.

## Table

The following end points are available for manipulating tables within locutus.
For all relevant functions, any change to the table will result in a change
to the underlying "shadow" terminology.

### https://[APPURL]/api/Table

#### GET

List all tables found in the database that the user can read.

```json
[
  {
    "description": null,
    "id": "INCLUDE:participant",
    "resource_type": "Table",
    "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant",
    "variables": [
      {
        "description": "Unique identifer for the study, assigned by DCC",
        "data_type": "STRING",
        "name": "Study Code"
      },
      {
        "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
        "data_type": "STRING",
        "name": "Participant Global ID"
      },
      {
        "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
        "data_type": "STRING",
        "name": "Participant External ID"
      },
      {
        "description": "Unique identifer for family to which Participant belongs, assigned by data contributor",
        "data_type": "STRING",
        "name": "Family ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-LpeLjQdupwpW5N9Gx5qT3"
        },
        "description": "Structure of family members participating in the study",
        "data_type": "ENUMERATION",
        "name": "Family Type"
      },
      {
        "description": "Participant External ID for Participant's father (NA if Participant is not the proband)",
        "data_type": "STRING",
        "name": "Father ID"
      },
      {
        "description": "Participant External ID for Participant's mother (NA if Participant is not the proband)",
        "data_type": "STRING",
        "name": "Mother ID"
      },
      {
        "description": "Participant External ID for Participant's sibling(s) (NA if Participant is not the proband)",
        "data_type": "STRING",
        "name": "Sibling ID"
      },
      {
        "description": "Participant External ID for Participant's other family members (NA if Participant is not the proband)",
        "data_type": "STRING",
        "name": "Other Family Member ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-DCQHVrWz6DEW5HOVoeJus"
        },
        "description": "Relationship of Participant to proband",
        "data_type": "ENUMERATION",
        "name": "Family Relationship"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
        },
        "description": "Sex of Participant",
        "data_type": "ENUMERATION",
        "name": "Sex"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-uonGHeztn0SxCKrQzJTyc"
        },
        "description": "Race of Participant",
        "data_type": "ENUMERATION",
        "name": "Race"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-X7pYrNC641npqC0Kgt7Lz"
        },
        "description": "Ethnicity of Participant",
        "data_type": "ENUMERATION",
        "name": "Ethnicity"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-Ehs2nM9-LDe_EMm8OYIVI"
        },
        "description": "Down Syndrome status of participant",
        "data_type": "ENUMERATION",
        "name": "Down Syndrome Status"
      },
      {
        "max": null,
        "description": "Age in days of Participant at first recorded study event (enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
        "data_type": "INTEGER",
        "units": null,
        "min": null,
        "name": "Age at First Patient Engagement"
      },
      {
        "description": "Event for which Age at First Patient Engagement is given (e.g. enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
        "data_type": "STRING",
        "name": "First Patient Engagement Event"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-r1KS1XhFXHY2Vt6amUPOW"
        },
        "description": "Whether participant is alive or dead",
        "data_type": "ENUMERATION",
        "name": "Outcomes Vital Status"
      },
      {
        "max": null,
        "description": "Age in days when participant's vital status was last recorded",
        "data_type": "INTEGER",
        "units": null,
        "min": null,
        "name": "Age at Last Vital Status"
      }
    ],
    "filename": null,
    "name": "participant"
  },
  {
    "description": null,
    "id": "INCLUDE:specimen",
    "resource_type": "Table",
    "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/specimen",
    "variables": [
      {
        "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
        "data_type": "STRING",
        "name": "Participant Global ID"
      },
      {
        "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
        "data_type": "STRING",
        "name": "Participant External ID"
      },
      {
        "max": null,
        "description": "Age in days of participant at time of biospecimen collection",
        "data_type": "INTEGER",
        "units": null,
        "min": null,
        "name": "Age at Biospecimen Collection"
      },
      {
        "description": "INCLUDE global identifier for sample, assigned by DCC",
        "data_type": "STRING",
        "name": "Sample Global ID"
      },
      {
        "description": "Unique identifier for sample, assigned by data contributor. A sample is a unique biological material; two samples with two different IDs are biologically distinct.",
        "data_type": "STRING",
        "name": "Sample External ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-qVO-Iie3FUE2DuJFtIwMB"
        },
        "description": "Type of biological material comprising the Sample (e.g. Plasma, White blood cells, Red blood cells, DNA, RNA, Peripheral blood mononuclear cells, CD4+ Tconv cells, NK cells, Monocytes, CD8+ T cells, B cells, Granulocytes, Treg cells)",
        "data_type": "ENUMERATION",
        "name": "Sample Type"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-FHr-QnQgEhY59tSUEQ2TA"
        },
        "description": "Whether or not the sample is potentially available for sharing through\n      the Virtual Biorepository",
        "data_type": "ENUMERATION",
        "name": "Sample Availability"
      },
      {
        "description": "INCLUDE global identifier for the eldest sample in a lineage, assigned by DCC",
        "data_type": "STRING",
        "name": "Collection Global ID"
      },
      {
        "description": "Identifier for the eldest sample in a lineage of processed, pooled,\n      or aliquoted samples - typically the material actually collected from the Participant. This may be the same as Parent Sample ID or Sample ID\n      (if no processing was performed). Assigned by data contributor.",
        "data_type": "STRING",
        "name": "Collection External ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-zKsH0HIlNggsxfQwLebme"
        },
        "description": "Type of biological material comprising the Collected Sample (e.g. Whole blood, Not reported, Saliva, Derived cell line)",
        "data_type": "ENUMERATION",
        "name": "Collection Sample Type"
      },
      {
        "description": "INCLUDE global identifier for specific container/aliquot of sample, assigned by DCC",
        "data_type": "STRING",
        "name": "Container Global ID"
      },
      {
        "max": null,
        "description": "Identifier for specific container/aliquot of sample, assigned by data contributor.\n      For example, distinct aliquots of a sample will have the same Sample ID but\n      different Container IDs.",
        "data_type": "INTEGER",
        "units": null,
        "min": null,
        "name": "Container External ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-Bq5S8LkrTEbdy85EnQQnA"
        },
        "description": "Container Availability",
        "data_type": "ENUMERATION",
        "name": "Container Availability"
      },
      {
        "description": "INCLUDE global identifier for the direct parent from which Sample was derived, assigned by DCC",
        "data_type": "STRING",
        "name": "Parent Sample Global ID"
      },
      {
        "description": "Unique identifier for the parent sample, assigned by data contributor",
        "data_type": "STRING",
        "name": "Parent Sample External ID"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-U7qbw11EDknc5NTC-91_o"
        },
        "description": "Type of biological material comprising the Parent Sample (e.g. Peripheral Whole Blood, Derived Cell Line, Saliva, Whole blood, WBCs) ",
        "data_type": "ENUMERATION",
        "name": "Parent Sample Type"
      },
      {
        "description": "Procedure by which Sample was derived from Parent Sample (e.g. Centrifugation, RBC lysis, Lyse/fix buffer, FACS, PAXgene DNA, PAXgene RNA, Qiagen Allprep, Ficoll)",
        "data_type": "STRING",
        "name": "Laboratory Procedure"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-qQ7jKoalnr4hOlzrz2AKD"
        },
        "description": "Method by which Container is stored (e.g. Minus 80 degrees Celsius, Liquid nitrogen storage)",
        "data_type": "ENUMERATION",
        "name": "Biospecimen Storage"
      },
      {
        "max": null,
        "description": "Concentration of sample in container",
        "data_type": "QUANTITY",
        "units": null,
        "min": null,
        "name": "Concentration"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-lv60mNdaYpzDN5TGHcTV5"
        },
        "description": "Unit of sample concentration",
        "data_type": "ENUMERATION",
        "name": "Concentration_Unit"
      },
      {
        "max": null,
        "description": "Amount of sample in container",
        "data_type": "QUANTITY",
        "units": null,
        "min": null,
        "name": "Volume"
      },
      {
        "enumerations": {
          "reference": "Terminology/tm-VxCSebNidllU3LpIsB0ff"
        },
        "description": "Unit of sample volume",
        "data_type": "ENUMERATION",
        "name": "Volume Unit"
      }
    ],
    "filename": null,
    "name": "specimen"
  }
]
```

#### POST

Create new table

```json
{
  "description": null,
  "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant",
  "variables": [
    {
      "description": "Unique identifer for the study, assigned by DCC",
      "data_type": "STRING",
      "name": "Study Code"
    },
    {
      "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
      "data_type": "STRING",
      "name": "Participant Global ID"
    },
    {
      "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
      "data_type": "STRING",
      "name": "Participant External ID"
    },
    {
      "description": "Unique identifer for family to which Participant belongs, assigned by data contributor",
      "data_type": "STRING",
      "name": "Family ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-LpeLjQdupwpW5N9Gx5qT3"
      },
      "description": "Structure of family members participating in the study",
      "data_type": "ENUMERATION",
      "name": "Family Type"
    },
    {
      "description": "Participant External ID for Participant's father (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Father ID"
    },
    {
      "description": "Participant External ID for Participant's mother (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Mother ID"
    },
    {
      "description": "Participant External ID for Participant's sibling(s) (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Sibling ID"
    },
    {
      "description": "Participant External ID for Participant's other family members (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Other Family Member ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-DCQHVrWz6DEW5HOVoeJus"
      },
      "description": "Relationship of Participant to proband",
      "data_type": "ENUMERATION",
      "name": "Family Relationship"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
      },
      "description": "Sex of Participant",
      "data_type": "ENUMERATION",
      "name": "Sex"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-uonGHeztn0SxCKrQzJTyc"
      },
      "description": "Race of Participant",
      "data_type": "ENUMERATION",
      "name": "Race"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-X7pYrNC641npqC0Kgt7Lz"
      },
      "description": "Ethnicity of Participant",
      "data_type": "ENUMERATION",
      "name": "Ethnicity"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-Ehs2nM9-LDe_EMm8OYIVI"
      },
      "description": "Down Syndrome status of participant",
      "data_type": "ENUMERATION",
      "name": "Down Syndrome Status"
    },
    {
      "max": null,
      "description": "Age in days of Participant at first recorded study event (enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at First Patient Engagement"
    },
    {
      "description": "Event for which Age at First Patient Engagement is given (e.g. enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "STRING",
      "name": "First Patient Engagement Event"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-r1KS1XhFXHY2Vt6amUPOW"
      },
      "description": "Whether participant is alive or dead",
      "data_type": "ENUMERATION",
      "name": "Outcomes Vital Status"
    },
    {
      "max": null,
      "description": "Age in days when participant's vital status was last recorded",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at Last Vital Status"
    }
  ],
  "filename": null,
  "name": "participant"
}
```

### https://[APPURL]/api/Table/[id]

#### GET

Return a specific table (with a given id)

```json
{
  "description": null,
  "id": "INCLUDE:participant",
  "resource_type": "Table",
  "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant",
  "variables": [
    {
      "description": "Unique identifer for the study, assigned by DCC",
      "data_type": "STRING",
      "name": "Study Code"
    },
    {
      "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
      "data_type": "STRING",
      "name": "Participant Global ID"
    },
    {
      "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
      "data_type": "STRING",
      "name": "Participant External ID"
    },
    {
      "description": "Unique identifer for family to which Participant belongs, assigned by data contributor",
      "data_type": "STRING",
      "name": "Family ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-LpeLjQdupwpW5N9Gx5qT3"
      },
      "description": "Structure of family members participating in the study",
      "data_type": "ENUMERATION",
      "name": "Family Type"
    },
    {
      "description": "Participant External ID for Participant's father (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Father ID"
    },
    {
      "description": "Participant External ID for Participant's mother (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Mother ID"
    },
    {
      "description": "Participant External ID for Participant's sibling(s) (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Sibling ID"
    },
    {
      "description": "Participant External ID for Participant's other family members (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Other Family Member ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-DCQHVrWz6DEW5HOVoeJus"
      },
      "description": "Relationship of Participant to proband",
      "data_type": "ENUMERATION",
      "name": "Family Relationship"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
      },
      "description": "Sex of Participant",
      "data_type": "ENUMERATION",
      "name": "Sex"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-uonGHeztn0SxCKrQzJTyc"
      },
      "description": "Race of Participant",
      "data_type": "ENUMERATION",
      "name": "Race"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-X7pYrNC641npqC0Kgt7Lz"
      },
      "description": "Ethnicity of Participant",
      "data_type": "ENUMERATION",
      "name": "Ethnicity"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-Ehs2nM9-LDe_EMm8OYIVI"
      },
      "description": "Down Syndrome status of participant",
      "data_type": "ENUMERATION",
      "name": "Down Syndrome Status"
    },
    {
      "max": null,
      "description": "Age in days of Participant at first recorded study event (enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at First Patient Engagement"
    },
    {
      "description": "Event for which Age at First Patient Engagement is given (e.g. enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "STRING",
      "name": "First Patient Engagement Event"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-r1KS1XhFXHY2Vt6amUPOW"
      },
      "description": "Whether participant is alive or dead",
      "data_type": "ENUMERATION",
      "name": "Outcomes Vital Status"
    },
    {
      "max": null,
      "description": "Age in days when participant's vital status was last recorded",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at Last Vital Status"
    }
  ],
  "filename": null,
  "name": "participant"
}
```

#### PUT

Updates a table with the body (the contents of the body will replace the table
at the given id, completely)

```json
{
  "description": null,
  "id": "INCLUDE:participant",
  "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant",
  "variables": [
    {
      "description": "Unique identifer for the study, assigned by DCC",
      "data_type": "STRING",
      "name": "Study Code"
    },
    {
      "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
      "data_type": "STRING",
      "name": "Participant Global ID"
    },
    {
      "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
      "data_type": "STRING",
      "name": "Participant External ID"
    },
    {
      "description": "Unique identifer for family to which Participant belongs, assigned by data contributor",
      "data_type": "STRING",
      "name": "Family ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-LpeLjQdupwpW5N9Gx5qT3"
      },
      "description": "Structure of family members participating in the study",
      "data_type": "ENUMERATION",
      "name": "Family Type"
    },
    {
      "description": "Participant External ID for Participant's father (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Father ID"
    },
    {
      "description": "Participant External ID for Participant's mother (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Mother ID"
    },
    {
      "description": "Participant External ID for Participant's sibling(s) (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Sibling ID"
    },
    {
      "description": "Participant External ID for Participant's other family members (NA if Participant is not the proband)",
      "data_type": "STRING",
      "name": "Other Family Member ID"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-DCQHVrWz6DEW5HOVoeJus"
      },
      "description": "Relationship of Participant to proband",
      "data_type": "ENUMERATION",
      "name": "Family Relationship"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-aIzCqJJkThKoxC2LiI6pP"
      },
      "description": "Sex of Participant",
      "data_type": "ENUMERATION",
      "name": "Sex"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-uonGHeztn0SxCKrQzJTyc"
      },
      "description": "Race of Participant",
      "data_type": "ENUMERATION",
      "name": "Race"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-X7pYrNC641npqC0Kgt7Lz"
      },
      "description": "Ethnicity of Participant",
      "data_type": "ENUMERATION",
      "name": "Ethnicity"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-Ehs2nM9-LDe_EMm8OYIVI"
      },
      "description": "Down Syndrome status of participant",
      "data_type": "ENUMERATION",
      "name": "Down Syndrome Status"
    },
    {
      "max": null,
      "description": "Age in days of Participant at first recorded study event (enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at First Patient Engagement"
    },
    {
      "description": "Event for which Age at First Patient Engagement is given (e.g. enrollment, visit, observation, sample collection, survey completion, etc.). Age at enrollment is preferred, if available.",
      "data_type": "STRING",
      "name": "First Patient Engagement Event"
    },
    {
      "enumerations": {
        "reference": "Terminology/tm-r1KS1XhFXHY2Vt6amUPOW"
      },
      "description": "Whether participant is alive or dead",
      "data_type": "ENUMERATION",
      "name": "Outcomes Vital Status"
    },
    {
      "max": null,
      "description": "Age in days when participant's vital status was last recorded",
      "data_type": "INTEGER",
      "units": null,
      "min": null,
      "name": "Age at Last Vital Status"
    }
  ],
  "filename": null,
  "name": "participant"
}
```

#### DELETE

Deletes the table from the database. This will remove all references to the table
from any Data Dictionaries it is contained within.

### https://[APPURL]/api/Table/[id]/variable/[variable_name]

#### PUT

Add a variable to an existing Table. The variable will be contained within the
requests body and should have all the necessary components for the given data
type.

If one were to want to add the race variable as an enumerated type to a new
table, you would pass the following:

```json
{
  "enumerations": {
    "reference": "Terminology/tm-uonGHeztn0SxCKrQzJTyc"
  },
  "description": "Race of Participant",
  "data_type": "ENUMERATION",
  "name": "Race"
}
```

The entire table will be returned, including the new variable as a member of
the variables array.

If the variable already exists, a 400 error is returned.

#### DELETE

Removes a variable from the table.

If successful, the entire table is returned (and the deletion should be
reflected in the response).

If the variable doesn't exist, then a 404 error is returned.

It should be noted that if you delete an enumerated variable, the terminology 
referenced will not be deleted. The reason being that we can theoretically have
many variables using the same terminology for similar variables. 

### https://[APPURL]/api/Table/[id]/harmony

#### GET

Returns the harmony representation of all enumerations contained within the
table's variables.

```json
[
  {
    "local code": "Female",
    "text": "Female",
    "table_name": "participant",
    "parent_varname": "",
    "local code system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant/sex",
    "code": "female",
    "display": "Female",
    "code system": "http://hl7.org/fhir/administrative-gender",
    "comment": ""
  },
  {
    "local code": "Male",
    "text": "Male",
    "table_name": "participant",
    "parent_varname": "",
    "local code system": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant/sex",
    "code": "male",
    "display": "Male",
    "code system": "http://hl7.org/fhir/administrative-gender",
    "comment": ""
  }
]
```

### https://[APPURL]/api/Table/[id]/mapping

Manage the mappings associated with the columns of a given table.

Technically, the underlying functionality is done at the terminology level
and, as such, the behavior is identical to the matching terminology f
functionality including body and responses. The only difference is that the
end points themselves will be related to the table and it's ID.

#### GET

Returns a list of all mappings from the table (See example of the matching
terminology endpoint for details.)

#### DELETE

Remove all mappings associated with codes from the table's shadow terminology.

### https://[APPURL]/api/Table/[id]/mapping/[code]

#### GET

Returns mappings for a specific code (from the shadow terminology)

#### PUT

Set mappings for a specific code inside the given shadow terminology. The body
must contain all codings (i.e. it replaces anything that may already be there)

See corresponding endpoint for Terminology for more details.

#### DELETE

Remove the mappings currently associated with a given code from the table's
shadow terminology.

### https://[APPURL]/api/Table/[id]/rename

#### PATCH

Renames variable(s) in a table (as well as update descriptions)

This PATCH method does not conform to the standard guidelines which permit
updates to any property within the resource. Instead it is intended solely
for renaming variables inside a table. The body of the call will include will
be an object with one or two keys, "variable" and "description" (a valid rename
must have one of the two). Each of those keys will point to an object whose
keys match a term within the current table. Those key's values represent
the new value after the change.

For Example:

```json
{
  "variable": {
    "Female": "Woman"
  },
  "description": {
    "Female": "Woman"
  }
}
```

Will replace the name, _Female_, with _Woman_ as well as update the description
to match. This includes assigning all mappings from the code, _Female_ to the
newly named code, _Woman_ within the table's shadow terminology. The body
object can contain more than one key/value pair which will indicate the intent
to rename multiple variables in a single PATCH call.

If one or more of the "Old Name" entries doesn't exist in the table, a 404
"Not Found" error is returned.

If the root object in the body is missing both the "variable" and the
"description", a 400 error is returned.

Upon completion, 200 is returned along with the full table definition.

### https://[APPURL]/api/Table/[id]/filter

#### GET

Return the api search preferences for a specific table (with a given id). 
Below is an example result body
```json
{
    "ex_api": [
        "ontology1",
        "onto2"
    ]
}
```

#### PUT

Create a api search preference for a specific table (with a given id). 
The request body and results will look very similar to the examples given 
with the POST request for this endpoint.

#### POST

Update the api search preferences for a specific table (with a given id). 
Request body example
 ```json
 {
    "api_preference": {
        "ex_api": ["ontology1", "onto2"]
    }
}
```
The following JSON shows the api_preference is added at the table level.
```json
{
    "id": "tb-Fyf0T0ujF_-qOmWbPLGoN",
    "code": "participant_table",
    "name": "Participant Table",
    "url": "https://includedcc.org/fhir/CodeSystem/data-dictionary/participant",
    "filename": "participant.csv",
    "description": "The data-dictionary for participant demographics and basic participant level data",
    "variables": [],
    "resource_type": "Table",
    "terminology": {},
    "api_preference": {
        "ex_api": [
            "ontology1",
            "onto2"
        ]
    }
}
```
#### DELETE

Delete the api search preferences for a specific table (with a given id). 
Checkout this endpoint's POST request to see an example of the data that 
would be removed.

### https://[APPURL]/api/Table/[id]/filter/[code]

#### GET

Return the api search preference for the variable (specified by code) within 
a specific table (specified by id). 

```json
{
    "api_put6": [
        "onto3",
        "onto5"
    ]
}
```

### https://[APPURL]/api/Table/[id]/filter/[code]

#### PUT

Create a api search preference for the variable (specified by code) within 
a specific table (specified by id). 
The request body and results will look very similar to the examples given 
with the POST request for this endpoint.

### https://[APPURL]/api/Table/[id]/filter/[code]

#### POST

Update the api search preferences for the variable (specified by code) within 
a specific table (specified by id). 
Request body example
```json
{
    "api_preference": {
        "ex_api": ["ontology1", "onto2"]
    }
}
```
The following JSON shows the api_preference is added at the variable level.

```json
"variables": [
        {
            "name": "Study Code",
            "code": "study_code",
            "description": "Unique identifer for the study, assigned by DCC",
            "data_type": "ENUMERATION",
            "enumerations": {
                "reference": "Terminology/tm-bcOrPwPojdu_f8K3FT9-z"
            },
            "api_preference": {
                "api_put6": [
                    "onto3",
                    "onto5"
                ]
            }
        },
```

### https://[APPURL]/api/Table/[id]/filter/[code]

#### DELETE

Delete the api search preference for the variable (specified by code) within 
a specific table (specified by id).  
Checkout this endpoint's POST request to see an example of the data that 

### https://[APPURL]/api/Provenance/Table/[id]
#### GET
Returns the provenance for the table itself. This includes information relating
to adding, editing and removing variables. 

Example results:
```json
{
    "table": {
        "Reference": "Table/tb-Fyf0T0ujF_-qOmWbPLGoN"
    },
    "provenance": {
        "self": {
            "target": "self",
            "changes": [
                {
                    "target": "self",
                    "action": "Add Term",
                    "new_value": "junk",
                    "timestamp": "2024-Aug-01 11:41AM",
                    "editor": "eric.s.torstenson@vumc.org"
                },
                {
                    "target": "self",
                    "action": "Remove Term",
                    "new_value": "junk",
                    "timestamp": "2024-08-01 11:41AM",
                    "editor": "eric.s.torstenson@vumc.org"
                }
            ]
        }
    }
}
```

### https://[APPURL]/api/Provenance/Table/[id]/code/[code]
#### GET
To get the provenance of an individual variable inside a table, use this form
of the endpoint URL, where code is the variable's underlying code. A special 
variable has been created, ALL, which will return the provenance for all 
variables in the table. 

Example:
```
{
    "table": {
        "Reference": "Table/tb-Fyf0T0ujF_-qOmWbPLGoN"
    },
    "provenance": {
        "junk": {
            "target": "junk",
            "changes": [
                {
                    "target": "junk",
                    "action": "Remove Mapping",
                    "timestamp": "2024-08-01 04:13PM",
                    "old_value": "stuff",
                    "editor": "eric.s.torstenson@vumc.org"
                },
                {
                    "target": "junk",
                    "action": "Add Mapping",,
                    "timestamp": "2024-08-01 04:14PM",
                    "new_value": "stuff",
                    "old_value": "",
                    "editor": "eric.s.torstenson@vumc.org"
                },
                {
                    "target": "junk",
                    "action": "Remove Mapping",
                    "timestamp": "2024-08-01 04:16PM",
                    "old_value": "stuff",
                    "editor": "eric.s.torstenson@vumc.org"
                }
            ]
        }
    }
}
```

For ALL variables, each variable will appear as keys within the provenance object. 

A highly truncated example can be seen below. 
```
{
    "table": {
        "Reference": "Table/tb-Fyf0T0ujF_-qOmWbPLGoN"
    },
    "provenance": {
        "junk": {
            "target": "junk",
            "changes": [
                {
                    "target": "junk",
                    "action": "Remove Mapping",
                    "timestamp": "2024-08-01 04:13PM",
                    "old_value": "stuff",
                    "editor": "eric.s.torstenson@vumc.org"
                }]
        },
        "self": {
            "target": "self",
            "changes": [
                {
                    "target": "self",
                    "action": "Remove Term",
                    "new_value": "junk",
                    "timestamp": "2024-08-01 11:41AM",
                    "editor": "eric.s.torstenson@vumc.org"
                }
            ]
        }
    }
}
```


### https://[APPURL]/api/Study

#### GET

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

#### POST

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

### https://[APPURL]/api/Study/[id]

#### GET

Returns a study assocaited with the specified id.

### https://[APPURL]/api/Study/[id]

#### PUT

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

#### DELETE

Deletes the study at the given id

### https://[APPURL]/api/Study/[id]/dd/[datadictionary_id]

#### DELETE

Removes a data dictionary from the study.

If successful, the entire study is returned (and the deletion should be
reflected in the response).

If the data dictionary doesn't exist, then a 404 error is returned.

## DataDictionary:

### https://[APPURL]/api/DataDictionary

#### GET

Returns all data dictionaries the user has access to

```json
[
  {
    "description": null,
    "id": "INCLUDE",
    "tables": [
      {
        "reference": "Table/INCLUDE:participant"
      },
      {
        "reference": "Table/INCLUDE:condition"
      },
      {
        "reference": "Table/INCLUDE:specimen"
      },
      {
        "reference": "Table/INCLUDE:file_manifest"
      }
    ],
    "resource_type": "DataDictionary",
    "name": null
  }
]
```

#### POST

Creates a new data dictionary resource (contents sent in body)

```json
[
  {
    "tables": [
      {
        "reference": "Table/INCLUDE:participant"
      },
      {
        "reference": "Table/INCLUDE:condition"
      },
      {
        "reference": "Table/INCLUDE:specimen"
      },
      {
        "reference": "Table/INCLUDE:file_manifest"
      }
    ]
  }
]
```

### https://[APPURL]/api/DataDictionary/[id]

#### GET

Return a specific data dictionary with the given ID

```json
{
  "description": null,
  "id": "INCLUDE",
  "tables": [
    {
      "reference": "Table/INCLUDE:participant"
    },
    {
      "reference": "Table/INCLUDE:condition"
    },
    {
      "reference": "Table/INCLUDE:specimen"
    },
    {
      "reference": "Table/INCLUDE:file_manifest"
    }
  ],
  "resource_type": "DataDictionary",
  "name": null
}
```

#### PUT

Replace resource with the body at the given ID

```json
{
  "description": null,
  "id": "INCLUDE",
  "tables": [
    {
      "reference": "Table/INCLUDE:participant"
    },
    {
      "reference": "Table/INCLUDE:condition"
    },
    {
      "reference": "Table/INCLUDE:specimen"
    },
    {
      "reference": "Table/INCLUDE:file_manifest"
    }
  ],
  "resource_type": "DataDictionary",
  "name": null
}
```

#### DELETE

Removes the specified data dictionary associated with the given ID


## OntologyAPI:

### https://[APPURL]/api/OntologyAPI

#### GET

Returns all availiable Ontology APIs and their details

```json
[
    {
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
        "api_id": "ols",
        "api_url": "https://www.ebi.ac.uk/ols4/api/",
        "ontologies": [
            {
                "ontology_code": "ngbo",
                "ontology_title": " Next generation biobanking ontology(NGBO).",
                "system": "https://www.ebi.ac.uk/ols4/api/",
                "curie": "NGBO",
                "version": "http://purl.obolibrary.org/obo/ngbo/2022-10-05/ngbo.owl"
            },
        ]
    }      
]
```

### https://[APPURL]/api/OntologyAPI/[API_ID]

#### GET

Returns the details for the Ontology API denoted by the API_ID

```json
[
    {
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
    [
        [
            "Content-Type",
            "application/fhir+json"
        ]
    ]
]
```