from flask_restful import Resource
from flask import request
from locutus.model.exceptions import *
from locutus.api import get_editor, default_headers

class SessionStart(Resource):
    """API resource for starting a user session.

    Attributes:
        session_manager (SessionManager): Manages session operations. :)
    """
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def post(self):
        """Starts a session for the user.

        This method expects a POST request with a JSON payload containing a
         `user_id` and an optional `affiliation`.

        Returns:
            dict: A message indicating whether the session was successfully 
            started, along with HTTP status code.
        """
        body = request.get_json()
        
        try:
            user_id = body.get('user_id')
            if "user_id" not in body:
                raise LackingUserID(user_id)

            affiliation = body.get('affiliation')

            return self.session_manager.initiate_session(user_id, affiliation)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

class SessionTerminate(Resource):
    """API resource for terminating a user session.

    Attributes:
        session_manager (SessionManager): Manage session operations. :)
    """
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def post(self):
        """Terminates the current user session.

        Clears the session data for the current user.

        Returns:
            dict: A message indicating that the session was terminated, along 
            with HTTP status code.
        """
        return self.session_manager.terminate_session()

class SessionStatus(Resource):
    """API resource for checking the status of the current user session.

    Attributes:
        session_manager (SessionManager): The session manager used to manage
        session operations.
    """
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def get(self):
        """Checks the status of the current user session.

        If a session is active, returns the session details including user ID
        and affiliation.

        Returns:
            dict: A message indicating the session status, user ID, and 
            affiliation, along with HTTP status code.
        """
        return self.session_manager.get_session_status()
