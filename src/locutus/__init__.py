# For now, we'll use my dumb JSON persistence storage
# from locutus.storage import JStore
from locutus.storage.firestore import persistence
import logging

_persistence = None


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

# Set the logging config
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
# Create a logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
# Create a console handler for logging to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(logging.Formatter(LOGGING_FORMAT))
# Add handlers to the logger
logger.addHandler(console_handler)

"""
def persistence():
    global _persistence
    return _persistence


def init_base_storage(filepath="db"):
    global _persistence

    _persistence = JStore(filepath)

    return _persistence
"""
