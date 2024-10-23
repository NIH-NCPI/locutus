import subprocess
import logging
import time
from google.cloud import firestore
from locutus_util.common import (COL_TIME_LIMIT,SUB_TIME_LIMIT,BATCH_SIZE)


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

def delete_collection(coll_ref, batch_size=BATCH_SIZE, time_limit=COL_TIME_LIMIT):
    """
    Delete all documents in a collection, handling batches and subcollections.
    Includes a time limit to prevent infinite running.

    Args:
        coll_ref (CollectionReference): The Firestore collection reference.
        batch_size (int): The number of documents to delete per batch.
        time_limit (int): Maximum time in seconds to spend on deletion before stopping.
    """
    start_time = time.time()
    while True:
        # Checks the time limit has not expired
        if time.time() - start_time > time_limit:
            logging.warning(f"Timeout reached while deleting collection '{coll_ref.id}'. Stopping.")
            break
        
        # Gets document_ids from the collection reference
        docs = coll_ref.list_documents(page_size=batch_size)

        deleted = 0

        # Recursively delete any subcollections of the document
        for doc in docs:
            try:
                delete_subcollections(doc)  
                logging.info(f"Deleting document {doc.id} from collection '{coll_ref.id}'.")
                doc.delete()
                deleted += 1
            except Exception as e:
                logging.error(f"Failed to delete document {doc.id}: {e}")

        if deleted == 0:
            logging.info(f"No more documents to delete in collection '{coll_ref.id}'.")
            break

        logging.info(f"Deleted {deleted} documents from collection '{coll_ref.id}'.")

        # Continue if the number of deleted documents reached the batch size, otherwise stop
        if deleted < batch_size:
            break

def delete_subcollections(doc_ref, batch_size=BATCH_SIZE, time_limit=SUB_TIME_LIMIT):
    """
    Delete all subcollections of a given document, with a time limit to prevent infinite run
    
    Args:
        doc_ref (DocumentReference): The Firestore document reference.
        batch_size (int): The number of documents to delete per batch.
        time_limit (int): Maximum time in seconds to spend on deleting subcollections.
    """
    start_time = time.time()
    for subcollection in doc_ref.collections():
        if time.time() - start_time > time_limit:
            logging.warning(f"Timeout reached while deleting subcollections for document '{doc_ref.id}'. Stopping.")
            break

        logging.info(f"Deleting subcollection '{subcollection.id}' for document '{doc_ref.id}'.")
        delete_collection(subcollection, batch_size=batch_size, time_limit=time_limit)
