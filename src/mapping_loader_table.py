import argparse
import csv
import logging
from datetime import datetime
from google.cloud import firestore
from locutus.model.terminology import Terminology as Term, Coding
from locutus import persistence
from locutus.model.helpers import set_logging_config, update_gcloud_project

csv_file_path = '../data/test_data_ori.csv'
class ExtendedCoding(Coding):
    def __init__(self, system=None, code=None, display=None, comment=None, editor=None,
                 variable_name=None, enumerated_value=None):
        super().__init__(system=system, code=code, display=display)
        self.comment = comment
        self.editor = editor 
        # self.variable_name = variable_name
        # self.enumerated_value = enumerated_value

    def to_dict(self):
        coding_dict = super().to_dict()

        coding_dict['comment'] = self.comment
        coding_dict['editor'] = self.editor
        # coding_dict['variable_name'] = self.variable_name
        # coding_dict['enumerated_value'] = self.enumerated_value

        return coding_dict

def process_csv_and_load_to_locutus(file_path):
    logging.info(f"Processing CSV file: {file_path}")

    with open(file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            source_variable = row['source_variable'] # Terminology
            source_enumeration = row['source_enumeration'] # Mapped Subject
            system = row.get('system')
            code = row['code']
            display = row.get('display')
            editor = row['provenance']
            comment = row['comment']

            logging.debug(f"Processing row: variable_name={source_variable}, code={code}")

            try:
                codings = [
                    ExtendedCoding(system=system,
                                   code=code,
                                   display=display,
                                   comment=comment,
                                   editor=editor,
                                #    source_variable=source_variable,
                                #    source_enumeration=source_enumeration
                                   )
                ]

                # Get reference to the 'Table' document and 'mappings' subcollection
                table_ref = persistence().collection("Table").document(source_variable)
                mapping_ref = table_ref.collection("mappings").document(source_enumeration)

                # Convert each ExtendedCoding object to a dictionary using the `to_dict()` method
                codings_dicts = [coding.to_dict() for coding in codings]

                # Add or update the mapping document
                logging.info(f"Updating mapping for source_variable: {source_variable}, "
                             f"source_enumeration: {source_enumeration}, code: {code}")
                             
                # Update Firestore with the list of coding dictionaries
                mapping_ref.set({'codings': codings_dicts}, merge=True)

            except Exception as e:
                logging.error(f"Error processing row for mapping: {source_variable}, "
                              f"mapped value: {source_enumeration}. Exception: {e}")
def load_data(project_id):
    _log_file = f"../data/logging/data_load.log"

    # Set logging configs
    set_logging_config(log_file=_log_file)
    logging.info(f"Log file created: {_log_file}")

    # Set the correct project
    logging.info(f"Setting GCP project: {project_id}")
    update_gcloud_project(project_id)

    # Process CSV file
    logging.info(f"Starting CSV processing for file: {csv_file_path}")
    process_csv_and_load_to_locutus(csv_file_path)
    logging.info("CSV processing completed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Load CSV data into Firestore.")
    parser.add_argument('-p', '--project_id', required=True, help="GCP Project to edit")
    
    args = parser.parse_args()

    load_data(project_id=args.project_id)
