import os
import inspect

base_path = os.path.dirname(
    os.path.abspath(inspect.getfile(inspect.currentframe())))


# Directory paths
LOCUTUS_PATH = os.path.join(base_path, 'locutus')
UTILS_PATH = os.path.join(LOCUTUS_PATH, 'utils')
UTILS_STORAGE_PATH = os.path.join(UTILS_PATH, 'storage')
UTILS_LOOKUP_PATH = os.path.join(UTILS_STORAGE_PATH, 'lookup_tables')

# File paths
ONTOLOGY_API_LOOKUP_TABLE_PATH = os.path.join(UTILS_LOOKUP_PATH, 'ontology_definition.csv')
