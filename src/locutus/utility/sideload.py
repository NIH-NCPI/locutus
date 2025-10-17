"""
Allow users to side load mappings from CSV file
"""

from locutus.model.table import Table 
from locutus import persistence
from locutus.model.exceptions import LackingRequiredParameter
from locutus.model.variable import Variable 
from collections import defaultdict 

from pathlib import Path 
import argparse
from csv import DictReader 
import os 

def GetTerminology(table, source_variable, source_enum):
    if source_enum == source_variable:
        term = table.terminology.dereference()
    else:
        variable = table.get_variable(source_variable)
 
        if variable.data_type == Variable.DataType.ENUMERATION:
            term = variable.get_terminology()
        else:
            raise TypeError(f"Variable, {source_variable} is not an enumerated variable and therefor will not contain {source_enumeration}")

    return term 

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

    mappings = dict()

    # Let's verify the prov is present for all of them before starting
    # just to prevent having duplicates if some do have prov at the start
    for row in mapping_entries:
        source_variable = row["source_variable"]
        source_enumeration = row["source_enumeration"]
        if row['provenance'].strip() == "":
            # We will try to tolerate empty lines
            if row['source_variable'].strip() != "":
                raise LackingRequiredParameter("provenance")

        # If we are trying to map to nothing, then we have a problem
        if row['code'].strip() != "" and source_variable.strip() == "" and source_enumeration.strip() == "":
            raise LackingRequiredParameter("source_enumeration or source_variable")

    for row in mapping_entries:
        if _cur_table is None or _cur_table.id != row['table_id']:
            _cur_table = Table.get(row['table_id'])
        source_variable = row['source_variable']
        source_enumeration = row['source_enumeration']

        if source_enumeration == "":
            source_enumeration = source_variable

        # Avoid letting blank lines kill us.
        if row['code'] != "":

            term = GetTerminology(_cur_table, source_variable, source_enumeration)

            key = f"{term.id}-{source_enumeration}"
            if key not in mappings:
                mappings[key] = {
                    "terminology": term,
                    "source_enumeration": source_enumeration,
                    "provenance": row['provenance'],
                    "mappings": []
                }
            mappings[key]['mappings'].append({
                "code": row['code'],
                "display": row['display'],
                "system": row['system'],
                "mapping_relationship": row['mapping_relationship'],
            })

    for key, mapping_data in mappings.items():
        term = mapping_data['terminology']
        source_enumeration = mapping_data['source_enumeration']
        prov = mapping_data['provenance']
        term_mappings = mapping_data['mappings']

        term.set_mapping(source_enumeration, term_mappings, prov)

def sideload_csv(csvfile):
    reader = DictReader(csvfile, delimiter=',', quotechar='"')


    SetMappings(list(reader))

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
        required=True,
        help="CSV File containing mapping information"
    )
    args = parser.parse_args()
    os.environ['MONGO_URI'] = args.database_uri

    client = persistence(mongo_uri=args.database_uri, missing_ok=False)

    sideload_csv(args.file)

if __name__ == "__main__":
    exec()
