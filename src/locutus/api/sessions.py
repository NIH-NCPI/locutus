from flask_restful import Resource


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
