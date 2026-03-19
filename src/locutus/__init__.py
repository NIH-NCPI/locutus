# For now, we'll use my dumb JSON persistence storage
# from locutus.storage import JStore
import io
import logging
import logging.config
import os
import sys
import traceback
from os import getenv
from pathlib import Path

from flask import g, has_request_context

try:
    from pythonjsonlogger import jsonlogger

    HAS_JSON_LOGGER = True
except ImportError:
    HAS_JSON_LOGGER = False

# from search_dragon import logger as getlogger

PROVENANCE_TIMESTAMP_FORMAT = "%Y-%m-%d %I:%M:%S%p"


try:
    from rich.logging import RichHandler

    IS_RICH = True
except ImportError:
    IS_RICH = False

from typing import Callable, DefaultDict, Dict, List, TypeVar


def is_interactive():
    try:
        return hasattr(sys.stdin.isatty(), "ps1") or os.isatty(sys.stdin.fileno())
    except (AttributeError, io.UnsupportedOperation, ValueError, OSError):
        return False


default_headers = [
    ("Content-Type", "application/fhir+json"),
]


class RequestIDFilter(logging.Filter):
    def filter(self, record):
        # If we are inside a Flask request, grab the ID from 'g'
        if has_request_context():
            record.request_id = getattr(g, "request_id", "n/a")
        else:
            record.request_id = "out-of-context"
        return True


def setup_logging(level="INFO", log_file="output/log.txt"):
    """If rich is installed and we are running inside a tty, we'll use rich's
    built in handler for logging and will simplify the format since otherwise,
    there is duplicated information.

    Log information is streamed and written to file, unless log_file is None"""
    use_rich = is_interactive() and IS_RICH
    use_json = not use_rich and HAS_JSON_LOGGER

    config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {"request_id": {"()": RequestIDFilter}},
        "formatters": {
            "rich": {"datefmt": "%H:%M:%S"},
            "detailed": {"format": "%(asctime)s %(levelname)s [%(name)s] %(message)s"},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "detailed",
                "level": level,
            },
        },
        "root": {
            "handlers": ["console"],
            "level": level,
        },
    }
    if use_rich:
        config["handlers"]["console"]["class"] = "rich.logging.RichHandler"
        config["handlers"]["console"]["formatter"] = "rich"
        config["handlers"]["console"]["rich_tracebacks"] = True
        config["handlers"]["console"]["markup"] = True
    elif use_json:
        # This should be better suited for GCP and AWS logs
        config["formatters"]["json"] = {
            "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
        }
        config["handlers"]["console"]["formatter"] = "json"
    else:
        config["handlers"]["console"]["formatter"] = "detailed"

    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        config["handlers"]["file"] = {
            "class": "logging.FileHandler",
            "filename": log_file,
            "formatter": "json" if not use_rich and HAS_JSON_LOGGER else "detailed",
            "level": level,
        }
        config["root"]["handlers"].append("file")

    logging.config.dictConfig(config)


def strip_none(value):
    if value is None or value.strip() == "":
        return ""
    return value


# Full match strings that are encoded by the frontend
FTD_PLACEHOLDERS = {
    "<FTD-DOT>": ".",
    "<FTD-DOT-DOT>": "..",
}

# Partial match strings that must be encoded by the frontend
FTD_PLACEHOLDERS_PARTIAL_MATCH = {"<FTD-HASH>": "#"}

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

    for placeholder, char in FTD_PLACEHOLDERS_PARTIAL_MATCH.items():
        code = code.replace(placeholder, char)

    return code


# Special character mappings. UTF-8 Hex
sp_char_mappings_indexes = {"/": "0x2F"}


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
    logging.warning(f"get_code_index call: \n{''.join(traceback.format_stack()[-2])}")
    return code
    # Ensure any codes with designated placeholders have them in place at indexing.
    if code in REVERSE_FTD_PLACEHOLDERS:
        code = REVERSE_FTD_PLACEHOLDERS[code]
    for placeholder, char in FTD_PLACEHOLDERS_PARTIAL_MATCH.items():
        code = code.replace(char, placeholder)

    code_index = code
    for key, value in sp_char_mappings_indexes.items():
        code_index = code_index.replace(key, value)
    return code_index


# Set the logging config
LOGGING_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"


def format_ftd_code(code, curie):
    """
    Ensure the code is in CUR:123456 format using the ontology lookup.
    If already formatted, return as-is. Otherwise, use the system to find the correct CUR prefix.
    """
    if ":" in code:
        return code
    if code and curie != "":
        return f"{curie}:{code}"
    if code and curie == "":
        return code
    else:
        logging.warning(
            f"Something went wrong trying to format the ftd_code. {curie}:{code}"
        )
        return code


# Create a logger
# llevel = getenv("LOCUTUS_LOGLEVEL", logging.WARN)
# logger = getlogger(logformat=LOGGING_FORMAT, loglevel=llevel)
# logger.info(f"Logger instanced with level: {llevel}")

"""
def persistence():
    global _persistence
    return _persistence


def init_base_storage(filepath="db"):
    global _persistence

    _persistence = JStore(filepath)

    return _persistence
"""
from .storage import persistence
