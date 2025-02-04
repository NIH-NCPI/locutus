import subprocess
import logging
import time
from google.cloud import firestore


def set_logging_config(log_file):

    LOGGING_FORMAT='%(asctime)s - %(levelname)s - %(message)s'

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Create a file handler for logging to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    
    # Create a console handler for logging to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
    
    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

# Initialize Firestore client
db = firestore.Client()

def update_gcloud_project(project_id):
    """Update the active Google Cloud project."""
    command = ["gcloud", "config", "set", "project", project_id]
    
    try:
        logging.info(f"Updating Google Cloud project to: {project_id}")
        subprocess.run(command, check=True)
        logging.info(f"Project updated successfully: {project_id}")
    except subprocess.CalledProcessError as e:
        logging.error(f"Error updating project: {e}")

def clean_varname(name):
    # Does not lower the var name as the locutus function does.
    return (
        name.replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
        .replace('"', "")
    )