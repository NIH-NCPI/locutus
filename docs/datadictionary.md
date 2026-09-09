# Data Dictionary


## https://[APPURL]/api/DataDictionary

### GET

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

### POST

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

## https://[APPURL]/api/DataDictionary/[id]

### GET

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

### PUT

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

### DELETE

Removes the specified data dictionary associated with the given ID

