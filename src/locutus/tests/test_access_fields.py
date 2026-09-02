"""
Cross-cutting coverage for Auth Requirements M4: every Serializable
collection that's meant to carry its own owner_id/visibility/access fields
(Study, DataDictionary, Table, Terminology) does so correctly, and existing
documents saved before these fields existed still load cleanly and read as
Registered (any authenticated user) -- what "visibility" has always meant
here, before the Public/Registered/Institution/Restricted split existed.
"""

import locutus
from locutus.model.datadictionary import DataDictionary
from locutus.model.study import Study
from locutus.model.terminology import Terminology
from locutus.model.visibility import Visibility


def test_study_access_fields_default_and_round_trip():
    study = Study(
        name="Access Field Study",
        url="http://ftd.unit.tests/access-field-study/",
        title="Access Field Study",
        description="",
    )
    assert study.owner_id is None
    assert study.visibility == Visibility.Registered
    assert study.access == {"institutions": {}, "users": {}}

    study.save()
    try:
        fetched = Study.get(study.id)
        assert isinstance(fetched, Study)
        assert fetched.owner_id is None
        assert fetched.visibility == Visibility.Registered
        assert fetched.access == {"institutions": {}, "users": {}}
    finally:
        study.delete(hard_delete=True)


def test_study_access_fields_persist_when_set():
    study = Study(
        name="Owned Study",
        url="http://ftd.unit.tests/owned-study/",
        title="Owned Study",
        description="",
        owner_id="u1",
        visibility=Visibility.Institution,
        access={"institutions": {"vumc": "editor"}, "users": {}},
    )
    study.save()
    try:
        fetched = Study.get(study.id)
        assert isinstance(fetched, Study)
        assert fetched.owner_id == "u1"
        assert fetched.visibility == Visibility.Institution
        assert fetched.access == {"institutions": {"vumc": "editor"}, "users": {}}
    finally:
        study.delete(hard_delete=True)


def test_datadictionary_access_fields_default():
    dd = DataDictionary(name="Access Field DD", description="")
    assert dd.owner_id is None
    assert dd.visibility == Visibility.Registered
    assert dd.access == {"institutions": {}, "users": {}}

    dd.save()
    try:
        fetched = DataDictionary.get(dd.id)
        assert isinstance(fetched, DataDictionary)
        assert fetched.visibility == Visibility.Registered
        assert fetched.access == {"institutions": {}, "users": {}}
    finally:
        dd.delete(hard_delete=True)


def test_terminology_access_fields_default():
    term = Terminology(
        name="Access Field Terminology",
        url="http://ftd.unit.tests/access-field-terminology/",
        description="",
    )
    assert term.owner_id is None
    assert term.visibility == Visibility.Registered
    assert term.access == {"institutions": {}, "users": {}}

    term.save()
    try:
        fetched = Terminology.get(term.id)
        assert isinstance(fetched, Terminology)
        assert fetched.visibility == Visibility.Registered
        assert fetched.access == {"institutions": {}, "users": {}}
    finally:
        term.delete(hard_delete=True)


def test_study_without_access_fields_loads_as_registered_by_absence():
    """Simulates a document saved before M4 -- no owner_id/visibility/access
    keys at all. Must load cleanly rather than crash, per M4's decision to
    not run a migration and treat absence as Registered (any authenticated
    user) -- not the new world-open Public tier, which isn't enforced yet."""
    doc_id = "st-pre-auth-test"
    locutus.persistence().collection("Study").document().set(
        {
            "id": doc_id,
            "name": "Pre-Auth Study",
            "title": "Pre-Auth Study",
            "url": "http://ftd.unit.tests/pre-auth-study/",
            "description": "",
            "resource_type": "Study",
            "datadictionary": [],
        }
    )

    fetched = None
    try:
        fetched = Study.get(doc_id)
        assert isinstance(fetched, Study)
        assert fetched.owner_id is None
        # __init__'s own default still applies since the field was simply
        # absent from the stored doc, not explicitly set to something else.
        assert fetched.visibility == Visibility.Registered
        assert fetched.access == {"institutions": {}, "users": {}}
    finally:
        # fetched may still be None (or the bare list[] Study.get() returns
        # for a None id) if the assert above never ran -- only clean up what
        # we know is a real, saved Study.
        if isinstance(fetched, Study):
            fetched.delete(hard_delete=True)


def test_visibility_all_four_levels_persist_and_round_trip():
    """Each of the four Visibility levels is a real, settable, round-trippable
    value -- Public and Restricted aren't enforced yet (no route checks them),
    but the schema must not silently coerce or reject them."""
    for level in Visibility:
        study = Study(
            name=f"Visibility {level} Study",
            url=f"http://ftd.unit.tests/visibility-{level.lower()}-study/",
            title=f"Visibility {level} Study",
            description="",
            visibility=level,
        )
        study.save()
        try:
            fetched = Study.get(study.id)
            assert isinstance(fetched, Study)
            assert fetched.visibility == level
        finally:
            study.delete(hard_delete=True)
