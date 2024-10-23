import argparse
import csv
import logging
from datetime import datetime
from google.cloud import firestore
from locutus.model.terminology import Terminology as Term, Coding
from locutus import persistence
from locutus.model.helpers import set_logging_config, update_gcloud_project

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
            variable_name = row['source_variable'] # Terminology
            enumerated_value = row['source_enumeration'] # Mapped Subject
            system = row.get('system')
            code = row['code']
            display = row.get('display')
            editor = row['provenance']
            comment = row['comment']

            logging.debug(f"Processing row: variable_name={variable_name}, code={code}")

            try:
                codings = [
                    ExtendedCoding(system=system,
                                   code=code,
                                   display=display,
                                   comment=comment,
                                   editor=editor,
                                #    variable_name=variable_name,
                                #    enumerated_value=enumerated_value
                                   )
                ]

                tref = persistence().collection("Terminology").document(variable_name)
                logging.info(f"Fetching Terminology for variable_name: {variable_name}")

                term = tref.get().to_dict()

                if term is None:
                    logging.warning(f"No existing Terminology found for variable_name: {variable_name}")
                    continue

                t = Term(**term)

                logging.info(f"Setting mapping for code: {enumerated_value} with editor: {editor}")
                t.set_mapping(enumerated_value, codings, editor=editor)

            except Exception as e:
                logging.error(f"Error processing row for mapping: {variable_name}, mapped value: {enumerated_value}. Exception: {e}")

def load_data(project_id):
    _log_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id}_data_load.log"

    # Set logging configs
    set_logging_config(log_file=_log_file)
    logging.info(f"Log file created: {_log_file}")

    # Set the correct project
    logging.info(f"Setting GCP project: {project_id}")
    update_gcloud_project(project_id)

    # Process CSV file
    csv_file_path = 'test_data.csv'
    logging.info(f"Starting CSV processing for file: {csv_file_path}")
    process_csv_and_load_to_locutus(csv_file_path)
    logging.info("CSV processing completed.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Load CSV data into Firestore.")
    parser.add_argument('-p', '--project_id', required=True, help="GCP Project to edit")
    
    args = parser.parse_args()

    load_data(project_id=args.project_id)
