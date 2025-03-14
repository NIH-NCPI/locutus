# For now, we'll use my dumb JSON persistence storage
# from locutus.storage import JStore
from locutus.storage.firestore import persistence
import logging

_persistence = None

PROVENANCE_TIMESTAMP_FORMAT = "%Y-%m-%d %I:%M:%S%p"

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

# Special character mappings. UTF-8 Hex
sp_char_mappings = {'/': '0x2F', 
                    '.': '0x2E' # Note: '..' will become '0x2E0x2E'
                    }

def get_code_index(code):
    """
     Cleans the identifier for db path referencing

    Codes that are within the main request url to locutus might come in with 
    special characters that cannot be used in a firestore resource path.
    Ex: `Ontology/Code` 

    Args:
      code(str): code. Ex: `given/code`

    Output:
      code_index(str): Ex: `given0x2Fcode'
    """
    code_index = code 
    for key, value in sp_char_mappings.items():
        code_index = code_index.replace(key, value)
    return code_index

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

"""
def persistence():
    global _persistence
    return _persistence


def init_base_storage(filepath="db"):
    global _persistence

    _persistence = JStore(filepath)

    return _persistence
"""
