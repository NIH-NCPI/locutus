# For now, we'll use my dumb JSON persistence storage
# from locutus.storage import JStore
from locutus.storage.firestore import persistence

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


"""
def persistence():
    global _persistence
    return _persistence


def init_base_storage(filepath="db"):
    global _persistence

    _persistence = JStore(filepath)

    return _persistence
"""
