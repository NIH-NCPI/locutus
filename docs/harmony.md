# Harmony Files
Harmony files provide a one to one relationship between ontology terms. We 
typically use them to annotate data-dictionary fields and enumerations to 
terms from public ontologies such as HPO, LOINC, etc. 

We current support two different columnar formats: *Whistle* and *FTD*. Each 
of which can be exported as **JSON** or **CSV**. 

## Harmony Endpoints
All harmony related endpoints support the following optional params:

* format - **Whistle** or **FTD**  - This just changes the header names
* file-format - **JSON** or **CSV** 

Defaults are **Whistle** as **JSON**

### https://[APPURL]/api/Study/[id]/harmony
This will create a single harmony file built from all tables found inside
all data-dictionaries that make up a single Study. 

### https://[APPURL]/api/DataDictionary/[id]/harmony
This will create a single harmony file built from all tables found inside
the specified data-dictionary. 

### https://[APPURL]/api/Table/[id]/harmony
This will create a single harmony file built from the specified table. 

### https://[APPURL]/api/harmony?[params]
This endpoint provides a single call to generate a harmony file based on any
combination of studies, data dictionaries and tables. Users provide a comma
separated list those as parameters to get the desired harmony content. 

One or more of the following parameters is required: 
* studies
* datadictionaries 
* tables 

For requesting harmony from more than one of the same type, simply separate
multiple IDs using a comma. For example, the following would return harmony
for a single study along with content from two additional tables:

> api/harmony?studies=st-12345&tables=tb-54321,tb-6543r21

## Harmony File Format
The locutus version > v2.2.2 and higher support exporting **CSV** and **JSON**
directly from the endpoints. 

When exporting as CSV, the first row will contain the header and the subsequent
rows contain a single mapping. 

## Harmony Data Format
While all of the endpoints export the same width of data, only some columns 
are only available at the study or data-dictionary level. 

### Whistle
The **Whistle** format is the original format based on Google's Whistle example
documentation. The original format had only 6 columns, but our needs required
a total of 8. With the recent discussion of using harmony data within our 
DBT workflows, we expanded the column count to 16 (with locutus > 2.2.2). This
is the default for all locutus harmony endpoints. 

We are currently keeping this format around until we have migrated all FHIR 
tooling to be able to correctly use the newer column names. 

    * study_title
    * study_name
    * study_id
    * dd_name
    * dd_id
    * version
    * table_id
    * local code
    * text
    * table_name
    * parent_varname
    * local code system
    * mapping_relationship
    * code
    * display
    * code system
    * comment

### FTD
The **FTD** format is based on our team members' request for clearer purpose 
for each of the columns. 

    * study_title
    * study_name
    * study_id
    * dd_name
    * dd_id
    * version
    * table_id
    * source_text
    * source_description
    * source_domain
    * parent_varname
    * source_system
    * mapping_relationship
    * mapped_code
    * mapped_display
    * mapped_system
    * comment

### Column Meaning
The column names can be found below (Whistle variants in parens where they 
differ)

#### study_title
Study title. This will only be present if the export was from a Study

#### study_name
Study name. This will only be present if the export was from a Study

#### study_id
Study ID. This will only be present if the export was from a Study

This ID will be the locutus ID associated with the study in Map Dragon. 

#### dd_name
Data Dictionary name. This will only be present if the export was from a Study
or a data dictionary. 

#### dd_id
Data Dictionary ID. This will only be present if the export was from a Study
or a data dictionary. 

#### version
Currently this will be the date the export was made. 

#### table_id
The ID associated with the table the the source text/variable is from.

#### source_text (local code)
This is the "Code" or Variable that ontological terms are being mapped to. 

#### source_description (text)
This is the "Description" for the Code or Variable that ontological terms are 
being mapped to. 

#### source_domain (table_name)
This is the table name associated with the code/variable being mapped to. 

#### parent_varname (parent_varname)
For enumerated values, this will be the variable name associated with the 
enumeration that is being mapped to. 

#### source_system (local code system)
This is the system from the source table for the code/variable being mapped to.

#### mapping_relationship
This is the relationship associated with the term and it's mapped codes such as 
Equivalent, Broader, Narrower. 

#### mapped_code (code)
This is the code for the term which is mapped to the local code/variable/enum.

#### mapped_display (display)
The display assocaited with the mapped term. 

#### mapped_system (system)
The system for the ontology from which the mapped code is found. 

#### comment
This is currently left blank. 