# For now, we'll use my dumb JSON persistence storage
from locutus.storage import JStore

_persistence = None


def persistence():
    global _persistence
    return _persistence


def init_base_storage(filepath="db"):
    global _persistence

    _persistence = JStore(filepath)

    return _persistence
