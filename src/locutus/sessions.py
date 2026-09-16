import logging
import os
import secrets
from datetime import UTC, datetime, timedelta

from flask import Flask, session
from flask_session import Session

import locutus

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Manages session handling including: initiation, termination,
    and configuration based on user affiliation.
    """

    def __init__(self, app: Flask):
        self.app = app
        # Sessions will persist beyond browser close
        self.app.config["SESSION_PERMANENT"] = True

        # Generates a secure 32-character hex key to encrypt session data
        self.app.config["SECRET_KEY"] = secrets.token_hex(16)

        # Store sessions in MongoDB (Auth Requirements spec, M10) -- a
        # filesystem or in-memory store doesn't survive a multi-instance
        # deployment. locutus.persistence() must be called before
        # Session(app) below so the singleton MongoClient already exists;
        # forcing that here (rather than depending on app.py's call order)
        # keeps the invariant local to this class instead of scattered
        # across startup sequencing elsewhere.
        db = locutus.persistence()
        self.app.config["SESSION_TYPE"] = "mongodb"
        self.app.config["SESSION_MONGODB"] = db.client
        self.app.config["SESSION_MONGODB_DB"] = db.db_name
        self.app.config["SESSION_MONGODB_COLLECT"] = "sessions"

        # Deployment-specific lifetime, set once via env var rather than in
        # code -- GCP/VUMC and AWS/KF are expected to want different values.
        # Sliding expiration (the default with SESSION_PERMANENT=True) resets
        # this on every request, so an active user is never logged out
        # mid-work. Defaults conservatively to 1 day until each deployment's
        # actual requirement is confirmed.
        lifetime_days = int(os.environ.get("SESSION_LIFETIME_DAYS", "1"))
        self.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=lifetime_days)

        # Extra security
        self.app.config["SESSION_COOKIE_HTTPONLY"] = True
        self.app.config["SESSION_COOKIE_SECURE"] = True
        self.app.config["SESSION_COOKIE_SAMESITE"] = "Lax"  # Option: 'Strict'

        Session(self.app)

    def initiate_session(self, user_id: str, affiliation: str | None = None):
        """
        Initiates a session for a user and sets the session timeout based on
        their affiliation. If the affiliation is not provided, it defaults to 'basic'.

        Args:
            user_id (str): The unique identifier of the user.
            affiliation (str, optional): The user's affiliation, which influences
              session timeout.

        Returns:
            A dictionary with a success message and HTTP status code 200.
        """
        if not affiliation:
            affiliation = "basic"
        logger.info(f"Setting the session user_id to {user_id}")
        logger.info(f"Setting the session affiliation to {affiliation}")
        session["user_id"] = user_id
        session["affiliation"] = affiliation

        # Adjust session timeout based on affiliation.
        self.set_timeout_based_on_affiliation(affiliation)

        return {
            "message": f"Session started for user {user_id} with the {affiliation} affiliation "
        }, 200

    def set_timeout_based_on_affiliation(self, affiliation: str) -> None:
        # Dynamically adjust timeout based on affiliation
        if affiliation == "premium":
            timeout_hours = 24
        elif affiliation == "basic":
            timeout_hours = 16
        else:
            # If no affiliation is recognized
            timeout_hours = 8
        logger.info(f"Session timeout is being set for {timeout_hours} hours.")
        self.app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(hours=timeout_hours)

    def terminate_session(self):
        user_id = session["user_id"]
        logger.info(f"Terminating the Session for user:{user_id}")
        session.clear()
        return {"message": "Session terminated"}, 200

    def get_session_status(self):
        """
        Sets the session timeout based on the user's affiliation.

        Premium users receive a 24-hour session timeout, basic users receive a 16-hour timeout,
        and unaffiliated or other users receive an 8-hour timeout.

        Args:
            affiliation (str): The user's affiliation, which determines the session timeout.
        """
        if "user_id" in session:
            return {
                "message": "Session active",
                "user_id": session.get("user_id"),
                "affiliation": session.get("affiliation"),
            }, 200
        else:
            return {"message": f"No active session. Session object: {session}"}, 404

    @staticmethod
    def create_user_id(editor: str | None) -> str | None:
        """
        Attempts to retrieve the user ID from the session or the provided editor ID.
        Args:
            editor (str, optional): The editor specified by the request body, if provided.
        Returns:
            editor="editor" or editor=None
        """
        try:
            if "user_id" in session:
                logger.info(f"The session is active. Session object: {session}")
                return session["user_id"]
            elif editor:
                logger.info(
                    f"The session is not active. Falling back to the existing editor: {editor}"
                )
                return editor
            else:
                logger.info(
                    f"The session is not active. There is no editor defined. editor: {editor}"
                )
                return None
        except RuntimeError:
            if editor:
                logger.info(
                    f"The session is not active. Falling back to the existing editor: {editor}"
                )
                return editor
            else:
                logger.info(
                    f"The session is not active. There is no editor defined. editor: {editor}"
                )
                return None

    @staticmethod
    def create_current_datetime() -> str:
        """
        Creates a formatted string of the current date and time.
        Returns:
            str: The current date and time as a string.
        """
        current_date = datetime.now(UTC).strftime("%b %d, %Y, %I:%M:%S.%f %p")
        return current_date
