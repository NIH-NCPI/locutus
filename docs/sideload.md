# Side Loading Mappings
Users can use the API to "side load" mappings that they acquired using an external
application by way of populating a CSV file with the necessary details and passing
it on via POST. 

## File Format

| Column Name | Description | Required Y/N | Comment |
| ----------- | ----------- | ------------ | ------- |
| table_id    | This is the ID inside locutus where the source data can be found. | Y | |
| source_variable | Variable code or name from source table | Y | |
| source_enumeration | If mapping to value from an enumeration, this will be that enum value | N | Only required for enums, otherwise, it can be blank |
| code | The code from the external ontology | Y | |
| display | The human friendly text associated with the code | Y | |
| system | The system associated with the public ontology | Y | |
| mapping_relationship | N | Relationship of the mapped term to the source term | equivalent, source-is-narrower-than-target, source-is-broader-than-target | 
| provenance | The email or app name to attribute inside provenance | Y | |
| comment | This is not used by locutus but may be helpful for tracking on the user's end | N| |

While some columns are marked as Required = N, it is assumed the column will be 
present, but can be blank. Strings like 'NA' will be interpretted as strings
and should be filtered out before loading into the backend. 

### Note about Mapping Relationship
Given the verbage in the table above, the codes for the Mapping Relationship 
options will seem backwards. source-is-narrower-than-target is actually saying
that the **mapped code** is narrower than what it is being **mapped to**. 

## https://[APPURL]/api/SideLoad 
### POST

The body current must contain: 
* editor - This is the user submitting the job
* csvContents - JSON array of objects, each entry has the above columns as keys/properties. 
