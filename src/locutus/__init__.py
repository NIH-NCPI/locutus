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


FTD_PLACEHOLDERS = {
    "<FTD-DOT>": ".",
    "<FTD-DOT-DOT>": "..",
    "<FTD-HASH>": "#"
    }

REVERSE_FTD_PLACEHOLDERS = {v: k for k, v in FTD_PLACEHOLDERS.items()}

def normalize_ftd_placeholders(code):
    """
    Replaces special FTD placeholders if the entire code matches them.
    
    Args:
        code(str): The input code.

    Returns:
        str: The normalized code.

    """
    if code in FTD_PLACEHOLDERS:
        return FTD_PLACEHOLDERS[code]
    else:
        return code
    

# Special character mappings. UTF-8 Hex
sp_char_mappings_indexes = {'/': '0x2F'}

def get_code_index(code):
    """
    Cleans the code identifier, for db path referencing

    Background: Codes from various inputs(request url, sideload, ect.)
    might contain special characters that cannot be used in a firestore resource
    path. i.e. `Ontology/Code` Use this function to clean them. Note that
    Codings(i.e. Table Variables) and CodingMappings(i.e. Mapping objects) 
    should not have transformed codes, another function exists for those transformations.

    Args:
      code(str): code. 
      Examples: `given/code`, `..`, or `<FTD-DOT-DOT>

    Output:
      code_index(str): 
      Examples: `given0x2Fcode' or <FTD-DOT-DOT>`
    """

    # Ensure any codes with designated placeholders have them in place at indexing.
    if code in REVERSE_FTD_PLACEHOLDERS:
        code = REVERSE_FTD_PLACEHOLDERS[code] 

    code_index = code 
    for key, value in sp_char_mappings_indexes.items():
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
