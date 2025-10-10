
"""
Allow users to side load mappings from CSV file
"""

from locutus.model.table import Table 
from locutus import persistence

from pathlib import Path 
import argparse
from csv import DictReader 
import os 

def SetMappings(mapping_entries):
    """Add mappings to source codes to values from content
    
    Input format-Dict with following columns: 
        * table_id
        * source_variable
        * source_enumeration
        * code
        * display
        * system
        * mapping_relationship
        * provenance
        * comment
    """

    _cur_table = None 
    table_term = None 
    for row in content:
        if _cur_table is None or _cur_table.id != row['table_id']:
            _cur_table = Table.get(row['table_id'])
            table_term = _cur_table.terminology.dereference()

        source_variable = row['source_variable']
        source_enumeration = row['source_enumeration']

        if source_enumeration in ["", source_variable]:
            term = table_term 
        else:
            # Actual enumerated var
            variable = _cur_table.get_variable(source_variable)
            if variable.data_type == Variable.DataType.ENUMERATION:
                term = variable.get_terminology()
            else:
                raise TypeError(f"Variable, {source_variable} is not an enumerated variable and therefor will not contain {source_enumeration}")

        mapping = {
            "code": row['code'],
            "display": row['display'],
            "system": row['system'],
            "mapping_relationship": row['mapping_relationship']
        }
        term.set_mapping(source_enumeration, [mapping], row['provenance'])

def sideload_csv(filename):
    with open(filename, 'rt') as file:
        reader = DictReader(file, delimiter=',', quotechar='"')

        SetMappings(reader)

def exec():
    parser = argparse.ArgumentParser(description="Load mappings from CSV and apply them to terms in locutus")
    parser.add_argument(
        "-db", "--database-uri",
        type=str,
        required=True,
        help="MONGO DB URI to initialize locutos with"
    )
    parser.add_argument(
        "-f", 
        "--file",
        type=argparse.FileType('rt'),
        required=true,
        help="CSV File containing mapping information"
    )
    args = parser.parse_args()
    os.environ['MONGO_URI'] = args.db 

    client = persistence(mongo_uri=args.db, missing_ok=False)

    sideload_csv(args.file)
