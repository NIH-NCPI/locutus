import pytest
import json
from .test_terminology import ftd_concept_relationships, sample_terminology
from locutus.model.study import Study 
from locutus.model.datadictionary import DataDictionary 
from .test_study import basic_study 
from .test_table import basic_table 

@pytest.fixture 
def basic_datadictionary(basic_study, basic_table):
    dd = DataDictionary(
        name="basic-dd",
        description="A Very basic DD with one table",
        tables = [
            {"reference": f"Table/{basic_table.id}"}
        ]
    )
    dd.save()

    yield dd 

    dd.global_id().delete()
    dd.delete(hard_delete=True)

def test_dd_basics(basic_datadictionary, basic_study, basic_table):
    dd = DataDictionary.get(basic_datadictionary.id)
    assert dd.id == basic_datadictionary.id 
    assert dd.name == basic_datadictionary.name  
    assert len(dd.tables) == len(basic_datadictionary.tables)

    assert dd.tables[0].dereference().dump() == basic_table.dump()


