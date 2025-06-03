import logging
import os



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



#logging
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
logger.addHandler(console_handler)

