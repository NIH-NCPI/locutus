from .test_datadictionary import basic_datadictionary 
from . import client
from .test_terminology import ftd_concept_relationships, sample_terminology
from .test_study import basic_study
from .test_table import basic_table 

from locutus.model.table import Table 

def test_loading_table(client, ftd_concept_relationships):
    mini_table = {
        "name": "mini table",
        "url": "https://mini.table",
        "csvContents": [
            {
                "variable_name": "Participant Global ID",
                "description": "Unique INCLUDE global identifier for the participant, assigned by DCC",
                "data_type": "String",
                "enumerations": "",
                "min": "",
                "max": ""
            },
            {
                "variable_name": "Sample Type",
                "description": "Type of biological material comprising the Sample (e.g. Plasma, White blood cells, Red blood cells, DNA, RNA, Peripheral blood mononuclear cells, CD4+ Tconv cells, NK cells, Monocytes, CD8+ T cells, B cells, Granulocytes, Treg cells)",
                "data_type": "String",
                "enumerations": "ATACseq;B cells Cryo;Blood Smear Slide;Buffy Coat;CD4+ Tconv cells;CD8+ T cells;CYTOF Ready White Blood Cells;DNA;Granulocytes;Monocytes;NK cells;PAXgene Whole Blood DNA;PAXgene Whole Blood DNA Tube;PAXgene Whole Blood RNA;PAXgene Whole Blood RNA Tube;PBMC;Peripheral Blood Mononuclear Cells;Peripheral Whole Blood;Plasma;Red Blood Cells;RNA;Saliva;Salivette;Skin Tape;Tongue Swab;Tregs;White Blood Cells;White Blood Cells Cryo;White Blood Cells DNA;White Blood Cells Protein;White Blood Cells RNA;Whole Blood;Whole Blood EDTA",
                "min": "",
                "max": ""
            },
            {
                "variable_name": "Participant External ID",
                "description": "Unique, de-identified identifier for the participant, assigned by data contributor. External IDs must be two steps removed from personal information in the study records.",
                "data_type": "string",
                "enumerations": "",
                "min": "",
                "max": ""
            },
            {
                "variable_name": "Age at Biospecimen Collection",
                "description": "Age in days of participant at time of biospecimen collection",
                "data_type": "integer",
                "enumerations": "",
                "min": "",
                "max": ""
            }
        ],
        "filename": "good_table_mini.csv",
        "editor": "unit-test"
    }

    response = client.post("/api/LoadTable",
                            json=mini_table, 
                            headers={"Content-Type": "application/json"}
                        )
    assert response.status_code == 201 
    table = response.json 

    assert table['name'] == mini_table['name']
    assert len(table['variables']) == len(mini_table['csvContents'])

    t = Table.get(table['id'])
    assert t.name == mini_table['name']
    
    term = t.terminology.dereference()
    assert len(term.codes) == len(mini_table['csvContents'])

    # cleanup 
    term.global_id().delete()
    term.delete(hard_delete=True)

    enum = t.variables[1].enumerations.dereference()
    enum.global_id().delete()
    enum.delete(hard_delete=True)

    t.global_id().delete()
    t.delete(hard_delete=True)




