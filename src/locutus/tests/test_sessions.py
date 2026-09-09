"""
Focused coverage for the Auth Requirements M10 session-storage migration:
sessions are now written to MongoDB rather than the local filesystem, which
is what makes them readable across separate app instances (the actual
guarantee a multi-instance deployment needs). This intentionally exercises
the storage mechanism directly via client.session_transaction() rather than
through a login endpoint -- real identity/access-control coverage lives in
test_auth.py and api_auth_test.py (Phase 3.3/Google login), which is a
separate concern from "does Flask-Session correctly persist to Mongo."
"""

import os

import locutus
from locutus.app import create_app


def _sessions_collection():
    db = locutus.persistence()
    return db.client[db.db_name]["sessions"]


def test_session_persists_to_mongodb():
    app = create_app()
    app.config["TESTING"] = True

    with app.test_client() as client:
        try:
            with client.session_transaction() as sess:
                sess["user_id"] = "u-mongo-persist-test"

            docs = list(_sessions_collection().find())
            assert len(docs) == 1
            assert set(docs[0].keys()) >= {"id", "val", "expiration"}
        finally:
            _sessions_collection().delete_many({})


def test_session_readable_from_a_separate_app_instance():
    """The real point of the M10 migration: a session started against one
    Flask app instance must be readable from a completely separate instance
    sharing only the session cookie -- proving it isn't tied to one
    process's filesystem or memory."""
    app_a = create_app()
    app_a.config["TESTING"] = True
    app_b = create_app()
    app_b.config["TESTING"] = True

    with app_a.test_client() as client_a:
        try:
            with client_a.session_transaction() as sess:
                sess["user_id"] = "u-cross-instance-test"
            session_cookie = client_a.get_cookie("session")
            assert session_cookie is not None

            with app_b.test_client() as client_b:
                client_b.set_cookie(
                    domain="localhost",
                    key="session",
                    value=session_cookie.value,
                )
                response = client_b.get("/api/session/status")
                assert response.status_code == 200
                assert response.json is not None
                assert response.json["user_id"] == "u-cross-instance-test"
        finally:
            _sessions_collection().delete_many({})


def test_session_lifetime_days_env_var(monkeypatch):
    monkeypatch.setenv("SESSION_LIFETIME_DAYS", "30")
    app = create_app()
    assert app.config["PERMANENT_SESSION_LIFETIME"].days == 30


def test_session_lifetime_defaults_to_one_day(monkeypatch):
    monkeypatch.delenv("SESSION_LIFETIME_DAYS", raising=False)
    app = create_app()
    assert app.config["PERMANENT_SESSION_LIFETIME"].days == 1
