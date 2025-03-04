# For now, we'll use my dumb JSON persistence storage
# from locutus.storage import JStore
# from locutus.storage.firestore import persistence
# from locutus.storage.mongo import persistence
# from locutus.storage.firestore import persistence

import logging
import os
# _persistence = None


db_type = os.getenv("DB_TYPE", "firestore").lower()

if db_type == "mongodb":
    from locutus.storage.mongo import persistence
    print("Using MongoDB")
else:
    from locutus.storage.firestore import persistence
    print("Using Firestore")




def strip_none(value):
    if value is None or value.strip() == "":
        return ""
    return value


def fix_varname(varname):
    return varname.strip().replace(" ", "_")


def clean_varname(name):
    return (
        name.lower()
        .replace(" ", "_")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
        .replace('"', "")
    )

# def initialize_persistence():
#     global _persistence
#     if _persistence is not None:
#         return


#     _persistence = persistence()
    
# # Initialize persistence on module load
# initialize_persistence()


# def get_persistence():
#     return _persistence


# Set the logging config
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

# Create a console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
# Add handlers to the logger
logger.addHandler(console_handler)
logger.info("Logger loggingingingingingingingingin")


# def persistence():
#     global _persistence
#     return _persistence


# def init_base_storage(filepath="db"):
#     global _persistence

#     _persistence = JStore(filepath)

#     return _persistence

