from flask import session
from flask_session import Session

import secrets
from datetime import timedelta, datetime
import logging

class SessionManager:
    """
    Manages session handling including: initiation, termination,
    and configuration based on user affiliation.
    """
    def __init__(self, app):
        self.app = app
        # Sessions will persist beyond browser close
        self.app.config['SESSION_PERMANENT'] = True

        # Generates a secure 32-character hex key to encrypt session data
        self.app.config['SECRET_KEY'] = secrets.token_hex(16)

        # Store session info on server filesystem
        self.app.config['SESSION_TYPE'] = 'filesystem'

        # Extra security
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_SECURE'] = True
        self.app.config['SESSION_COOKIE_SAMESITE'] = 'Lax' # Option: 'Strict'

        Session(self.app)

    def initiate_session(self, user_id, affiliation=None):
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
            affiliation = 'basic'
        logging.info(f"Setting the session user_id to {user_id}")
        logging.info(f"Setting the session affiliation to {affiliation}")
        session['user_id'] = user_id
        session['affiliation'] = affiliation

        # Adjust session timeout based on affiliation.
        self.set_timeout_based_on_affiliation(affiliation)

        return {
            "message": f"Session started for user {user_id} with the {affiliation} affiliation "
        }, 200

    def set_timeout_based_on_affiliation(self, affiliation):
        # Dynamically adjust timeout based on affiliation
        if affiliation == 'premium':
            timeout_hours = 24
        elif affiliation == 'basic':
            timeout_hours = 16
        else: 
            # If no affiliation is recognized
            timeout_hours = 8
        logging.info(f"Session timeout is being set for {timeout_hours} hours.")
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=timeout_hours)

    def terminate_session(self):
        user_id = session["user_id"]
        logging.info(f"Terminating the Session for user:{user_id}")
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
        if 'user_id' in session:
            return {
                "message": "Session active", 
                "user_id": session.get('user_id'), 
                "affiliation": session.get('affiliation')
            }, 200
        else:
            return {"message": f"No active session. Session object: {session}"}, 404

    
    def create_user_id(editor):
        """
        Attempts to retrieve the user ID from the session or the provided editor ID.
        Args:
            editor (str, optional): The editor specified by the request body, if provided.
        Returns:
            editor="editor" or editor=None
        """
        try:
            if 'user_id' in session:
                logging.info(f"The session is active. Session object: {session}")
                return session['user_id']
            elif editor:
                logging.info(
                    f"The session is not active. Falling back to the existing editor: {editor}"
                )
                return editor
            else:
                logging.info(
                    f"The session is not active. There is no editor defined. editor: {editor}"
                )
                return None
        except RuntimeError as e:
            if editor:
                logging.info(
                    f"The session is not active. Falling back to the existing editor: {editor}"
                )
                return editor
            else:
                logging.info(
                    f"The session is not active. There is no editor defined. editor: {editor}"
                )
                return None    

    def create_current_datetime():
        """
        Creates a formatted string of the current date and time.
        Returns:
            str: The current date and time as a string.
        """
        current_date = datetime.now().strftime("%b %d, %Y, %I:%M:%S.%f %p")
        return current_date    