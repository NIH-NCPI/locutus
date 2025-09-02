import pytest
import json
from .test_terminology import ftd_concept_relationships, sample_terminology
from locutus.model.table import Table 
from locutus.model.terminology import Terminology
from locutus.model.global_id import GlobalID
from locutus.model.exceptions import InvalidValueError
from locutus.model.variable import Variable

@pytest.fixture 
def basic_table(sample_terminology):
    table = Table(
        name="FTD Table 01",
        url="http://ftd.unit.tests/basic_table/01",
        description="Simple Test Table",
        editor="unit-test",
        variables=[
            {
                "name": "String Var",
                "data_type": "string",
                "code": "string_var",
                "description": "String Variable Description"
            },
            {
                "name": "Integer Var",
                "data_type": "integer",
                "code":  "integer-var",
                "description": "Integer Variable Description"
            },
            {
                "name": "Enum Var",
                "data_type": "enumeration",
                "code": "enum_var",
                "description": "Enumeration Variable Description",
                "enumerations": {
                    "reference": f"Terminology/{sample_terminology.id}"
                }
            }
        ]
    )
    table.save()
    yield table 
    table.global_id().delete()

    t = Terminology.get(table.terminology.reference_id())
    t.global_id().delete()
    t.delete(hard_delete=True)

    table.delete(hard_delete=True)

def test_table_basics(sample_terminology):
    table = Table(
        name="FTD Table Basic",
        url="http://ftd.unit.tests/basic_table/basic",
        description="Simple Test Table",
        editor="unit-test",
        variables=[
            {
                "name": "String Var",
                "data_type": "string",
                "code": "string_var",
                "description": "String Variable Description"
            },
            {
                "name": "Integer Var",
                "data_type": "integer",
                "code":  "integer-var",
                "description": "Integer Variable Description"
            },
            {
                "name": "Enum Var",
                "data_type": "enumeration",
                "code": "enum_var",
                "description": "Enumeration Variable Description",
                "enumerations": {
                    "reference": f"Terminology/{sample_terminology.id}"
                }
            }
        ]
    )
    table.save()

    assert table.id is not None
    assert table.name == "FTD Table Basic"
    assert table.url == "http://ftd.unit.tests/basic_table/basic"
    assert table.description == "Simple Test Table"
    assert table.variables[0].name == "String Var"
    assert table.variables[1].data_type == Variable.DataType.INTEGER
    assert table.variables[2].description == "Enumeration Variable Description"
    enums = table.variables[2].get_terminology()
    assert len(enums.codes) == 2
    assert enums.codes[0].dereference().code == "C1"
    assert enums.codes[0].dereference().display == "Code One"
    assert enums.codes[0].dereference().system == "http://example.com/ont1"
    assert enums.codes[0].dereference().description == "Description for C1"
    assert enums.codes[1].dereference().code == "C2"

    shadow = table.terminology.dereference()
    shadow_id = shadow.id 

    assert len(shadow.codes) == 3
    assert shadow.codes[2].dereference().code == "enum_var"
    
    t = Table.get(table.id)
    assert t.id == table.id 

    t.global_id().delete()
    t.delete(hard_delete=True)
    t = Table.get(table.id)

    assert t is None

    t = Terminology.get(shadow_id)
    # We are currently not deleting shadow terminologies, since they may have not
    # been created specifically for the table
    assert t is not None 
    t.global_id().delete()
    t.delete(hard_delete=True)
    t = Terminology.get(shadow_id)
    assert t is None



def test_table_get(basic_table):
    table = Table.get(basic_table.id)
    assert table.id == basic_table.id 
    assert table.name == basic_table.name 
    assert len(table.variables) == len(basic_table.variables)

    shadow_terminology = table.terminology.dereference()
    assert shadow_terminology.id == table.terminology.reference_id()
    assert len(shadow_terminology.codes) == len(basic_table.variables)

