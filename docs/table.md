# Table


The following end points are available for manipulating tables within locutus.
For all relevant functions, any change to the table will result in a change
to the underlying "shadow" terminology.

## https://[APPURL]/api/Table

### GET

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

### POST

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

## https://[APPURL]/api/Table/[id]

### GET

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

### PUT

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

### DELETE

Deletes the table from the database. This will remove all references to the table
from any Data Dictionaries it is contained within.

## https://[APPURL]/api/Table/[id]/variable/[variable_name]

### PUT

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

### DELETE

Removes a variable from the table.

If successful, the entire table is returned (and the deletion should be
reflected in the response).

If the variable doesn't exist, then a 404 error is returned.

It should be noted that if you delete an enumerated variable, the terminology
referenced will not be deleted. The reason being that we can theoretically have
many variables using the same terminology for similar variables.

## https://[APPURL]/api/Table/[id]/harmony

### GET

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

## https://[APPURL]/api/Table/[id]/mapping

Manage the mappings associated with the columns of a given table.

Technically, the underlying functionality is done at the terminology level
and, as such, the behavior is identical to the matching terminology f
functionality including body and responses. The only difference is that the
end points themselves will be related to the table and it's ID.

### GET

Returns a list of all mappings from the table and their associated 'user_input'
if requested. (See example of the matching
terminology endpoint for details.)

### DELETE

Soft delete all mappings associated with codes from the table's shadow terminology.
The mappings 'valid' field is set to 'false'

## https://[APPURL]/api/Table/[id]/mapping/[code]

### GET

Returns mappings for a specific code and their associated 'user_input'
if requested. (from the shadow terminology. See example of the matching
terminology endpoint for details.)
Optionally, it can include additional user input data if the user_input parameter is provided.
Example endpoint: https://[APPURL]/api/Table/[id]/mapping?user_input=True&user=[user]

### PUT

Set mappings for a specific code inside the given shadow terminology. The body
must contain all codings (i.e. it replaces anything that may already be there)

See corresponding endpoint for Terminology for more details.

### DELETE

Soft delete the mappings currently associated with a given code from the table's
shadow terminology. The mappings 'valid' field is set to 'false'.

## https://[APPURL]/api/Table/[id]/user_input/[code]/mapping/[mapped_code]/[type]

- id (str): The document ID.
- code (str): The target document (mapping) identifier.
- mapped_code (str): The code being mapped to the target.
- type (str): The type of input to retrieve
  - currently available: "mapping_conversations","mapping_votes".

### GET

Return the reference to the `user_input` `type` related to the `Table` (specified by id).
Returns all records of the `type` at the `code` level, in reverse order
from whence they were stored, with newer records on top.

Expected return for type `mapping_votes` below

```json
{
  "Table": "tb-SwBjPP_pLv0sOdybjsUMR",
  "code": "participant_external_id",
  "mapped_code": "NCIT:C25599",
  "mapping_votes": {
    "user123": {
      "date": "Feb 25, 2025, 03:32:09.015505 PM",
      "vote": "up"
    }
  }
}
```

Expected return for type `mapping_conversations` below

```json
{
  "Table": "tb-SwBjPP_pLv0sOdybjsUMR",
  "code": "participant_external_id",
  "mapped_code": "NCIT:C25599",
  "mapping_conversations": [
    {
      "user_id": "user123",
      "date": "Feb 25, 2025, 03:35:11.682232 PM",
      "note": "I don't like this mapping"
    },
    {
      "user_id": "user456",
      "date": "Feb 25, 2025, 03:33:53.504690 PM",
      "note": "I like this mapping"
    }
  ]
}
```

### PUT

Create a `user_input` record of the `type` specified in `Table`(specified by id).

Request body example for `mapping_conversations` :

# editor is only required if not using sessions

```json
{
  "editor": "user456",
  "note": "I dont like this mapping"
}
```

Request body example for `mapping_votes` :

# editor is only required if not using sessions

```json
{
  "editor": "user123",
  "vote": "up"
}
```

## https://[APPURL]/api/Table/[id]/rename

### PATCH

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

## https://[APPURL]/api/Table/[id]/filter

<h4 id="table_id_filter_get">GET</h4>

Return the api search preferences for a specific table (with a given id). <br>
Returns the api search preferences at the Table("self") level.
Below is an example result body.

```json
{
  "self": {
    "api_preference": {
      "ex_api": ["ontology1", "onto2"]
    }
  }
}
```

### PUT

Create a api search preference for a specific table (with a given id). <br>
See the [POST request](#table_id_filter_post) an example request body for this endpoint.

<h4 id="table_id_filter_post">POST</h4>

Update the api search preferences for a specific table (with a given id). <br>
Request body example:

```json
{
  "api_preference": {
    "ex_api": ["ontology1", "onto2"]
  }
}
```

### DELETE

Delete the api search preferences for a specific table (with a given id). An example of the data after removal shown below.

```json
{}
```

## https://[APPURL]/api/Table/[id]/filter/[code]

<h4 id="table_id_filter_code_get">GET</h4>

Return the api search preference for the variable (specified by code) within
a specific table (specified by id). <br>
The response below would be the result of specifying 'study_code' as the `code`
in the request. <br> **Note:** If no preferences for the code(ie 'study_code') exist the
request will retrieve any existing preferences for at the Table level. [Example results](#table_id_filter_get)

```json
{
  "study_code": {
    "api_preference": {
      "ex_api": ["ontology1", "onto2"]
    }
  }
}
```

### PUT

Update a api search preference for the variable (specified by code) within
a specific table (specified by id).
See the [POST request](#table_id_filter_code_post) for an example request body.

<h4 id="table_id_filter_code_post">POST</h4>

Create the api search preferences for the variable (specified by code) within
a specific table (specified by id). <br>
Specifying 'study_code' as the `code` in the request will add this preference
to the variable as seen in this endpoints [GET request](#table_id_filter_code_get). <br>
Request body example:

```json
{
  "api_preference": {
    "ex_api": ["ex_onto", "ex_onto2"]
  }
}
```

### DELETE

Delete the api search preference for the variable (specified by code) within
a specific table (specified by id).  
This is the expected result after removing preferences with the URL code specifying
'study_code'.

```json
{
  "study_code": {}
}
```

## https://[APPURL]/api/Table/[id]/preferred_terminology

### GET

Return the reference to the preferred_terminology related to the `Table` (specified by id).<br>
Returns the preferred_terminology at the Table("self") level. <br> Expected return example below.

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

### PUT

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

### DELETE

Running the DELETE request will remove the preferred_terminology collection
from the `Table` specified by the id

## https://[APPURL]/api/Provenance/Table/[id]

### GET

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

## https://[APPURL]/api/Provenance/Table/[id]/code/[code]

### GET

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
