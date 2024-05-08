# Locutus 
Locutus provides the backend for a web based terminology mapping tool in the very early stages of development. The goal of the application is to provide a collaborative environment to harmonize dataset terms with public ontologies such as MeSH, HPO and others. 

There isn't much here at this time, but there are some example data based on a real research data-dictionary along with standard CRUD functionality. 

API Functionality: 

## Terminologies: 
### https://locutus-l2xv5td7oq-uc.a.run.app/api/Terminology 
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

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Terminology/<id>
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

## Terminology Mappings
### https://locutus-l2xv5td7oq-uc.a.run.app/api/Terminology/<id>/mapping
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

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Terminology/<id>/mapping/<code>
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

## Table
### https://locutus-l2xv5td7oq-uc.a.run.app/api/Table
#### GET
List all tables found in the database that the user can read.

```json
[{
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
}]
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



### https://locutus-l2xv5td7oq-uc.a.run.app/api/Table/<id>
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

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Table/<id>/harmony
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

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Study
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

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Study/<id>
#### GET
Returns a study assocaited with the specified id. 

### https://locutus-l2xv5td7oq-uc.a.run.app/api/Study/<id>
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

  
## DataDictionary: 
### https://locutus-l2xv5td7oq-uc.a.run.app/api/DataDictionary
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
        ],
    }
]

### https://locutus-l2xv5td7oq-uc.a.run.app/api/DataDictionary/<id>
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
