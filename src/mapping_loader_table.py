#!/usr/bin/env python

import argparse
import csv
import logging
from datetime import datetime
from google.cloud import firestore
from locutus.model.table import Table
from locutus.model.user_input import MappingConversations
from locutus.model.terminology import Terminology as Term, Coding
from locutus import persistence, clean_varname
from locutus.model.helpers import set_logging_config, update_gcloud_project

import pdb

locutus_project = {
    "DEV": "locutus-dev",
    "UAT": "locutus-uat",
    "PROD": "locutus-407820",
    "ALPHA": "locutus-alpha",
}


class ExtendedCoding(Coding):
    def __init__(
        self,
        system=None,
        code=None,
        display=None,
        comment=None,
        editor=None,
        variable_name=None,
        enumerated_value=None,
    ):
        super().__init__(system=system, code=code, display=display)
        self.comment = comment
        self.editor = editor
        # self.variable_name = variable_name
        # self.enumerated_value = enumerated_value

    def to_dict(self):
        coding_dict = super().to_dict()

        coding_dict["comment"] = self.comment
        coding_dict["editor"] = self.editor
        # coding_dict['variable_name'] = self.variable_name
        # coding_dict['enumerated_value'] = self.enumerated_value

        return coding_dict


def process_csv_and_load_to_locutus(file):
    logging.info(f"Processing CSV file: {file.name}")

    csv_reader = csv.DictReader(file)
    for row in csv_reader:
        source_variable = row["source_variable"]  # Terminology
        source_enumeration = clean_varname(
            row["source_enumeration"].strip()
        )  # Mapped Subject
        system = row.get("system")
        code = row["code"]
        display = row.get("display")
        editor = row["provenance"]
        comment = row["comment"]

        logging.debug(f"Processing row: variable_name={source_variable}, code={code}")

        try:
            codings = [
                ExtendedCoding(
                    system=system,
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
            logging.info(
                f"Updating mapping for source_variable: {source_variable}, "
                f"source_enumeration: {source_enumeration}, code: {code}"
            )

            # Update Firestore with the list of coding dictionaries
            mapping_ref.set({"codings": codings_dicts}, merge=True)

        except Exception as e:
            logging.error(
                f"Error processing row for mapping: {source_variable}, "
                f"mapped value: {source_enumeration}. Exception: {e}"
            )


def process_csv(file, table):
    # Build a lookup that we can use to map the variable names to
    # their respective terminologies
    enumerations = {}

    # varname => reference to terminology
    for variable in table.variables:
        if "/" in variable.code:
            print(f"Whoops! {variable.code}")
            pdb.set_trace()
        enumerations[variable.code] = variable.enumerations

    print(enumerations)
    # pdb.set_trace()

    csv_reader = csv.DictReader(file)
    user_input = MappingConversations()
    for row in csv_reader:
        source_variable = row["source_variable"]  # Terminology
        source_enumeration = clean_varname(
            row["source_enumeration"].strip()
        )  # Mapped Subject
        system = row.get("system")
        codes = [x.strip() for x in row["code"].split(",")]
        displays = row.get("display").split(",")
        editor = row["provenance"]
        comment = row["comment"]

        if (
            row["display"]
            == "dyskinesia with orofacial involvement, dyskinesia with orofacial involvement, autosomal dominant"
        ):
            displays = (
                "dyskinesia with orofacial involvement, autosomal dominant".split(",")
            )

        index = 0
        if len(codes) == 1:
            displays = [row.get("display")]
        assert len(codes) == len(
            displays
        ), f"Error! Does not compute! \n{row}\n\t{len(codes)} != {len(displays)}"
        for code in codes:
            display = displays[index]

            index += 1
            if source_variable in enumerations:
                if "/" in source_enumeration:
                    print(f"Skipping {source_variable} due to slash problem")
                else:
                    if code != "NA":
                        print(
                            f"{source_variable}.{source_enumeration} + {code}({display})"
                        )
                        t = enumerations[source_variable].dereference()

                        codings = [
                            x
                            for x in t.mappings(source_enumeration)[source_enumeration]
                            if x.code != code
                        ]
                        codings.append(
                            Coding(code=code, display=display, system=system)
                        )
                        # pdb.set_trace()
                        t.set_mapping(
                            source_enumeration, codings=codings, editor=editor
                        )
                        if comment is not None and comment != "NA":
                            user_input.create_or_replace_user_input(
                                resource_type="Terminology",
                                collection_type="user_input",
                                id=t.id,
                                code=code,
                                type="mapping_conversations",
                                body=comment,
                            )


def load_data(project_id, table_id, file):
    _log_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{project_id}_data_load.log"

    # Set logging configs
    set_logging_config(log_file=_log_file)
    logging.info(f"Log file created: {_log_file}")

    # Set the correct project
    logging.info(f"Setting GCP project: {project_id}")
    update_gcloud_project(project_id)

    # Grab the Table from the database via the usual model backend stuff
    # pdb.set_trace()
    logging.info(f"Starting CSV processing for file: {file.name}")
    table = Table.get(table_id)
    process_csv(file, table)
    logging.info("CSV processing completed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load CSV data into Firestore.")
    parser.add_argument(
        "-e",
        "--env",
        choices=["DEV", "UAT", "ALPHA", "PROD"],
        help="Locutus environment to use",
    )
    parser.add_argument(
        "-p",
        "--project-id",
        help="GCP Project to edit (if not part of a standard environment)",
    )
    parser.add_argument("-f", "--file", type=argparse.FileType("rt"))
    parser.add_argument(
        "-t", "--table-id", help="Which table the data can be found in."
    )

    args = parser.parse_args()

    if args.env is not None:
        project_id = locutus_project[args.env]
    else:
        project_id = args.project_id

    load_data(project_id=project_id, table_id=args.table_id, file=args.file)
