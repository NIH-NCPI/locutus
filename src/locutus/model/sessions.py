from flask import session
from flask_session import Session

import secrets
from datetime import timedelta

class SessionManager:
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
        if not affiliation:
            affiliation = 'basic'
        
        session['user_id'] = user_id
        session['affiliation'] = affiliation

        # Adjust session timeout based on affiliation.
        self.set_timeout_based_on_affiliation(affiliation)
        
        return {"message": f"Session started for user {user_id} with the
                 {affiliation} affiliation "}, 200

    def set_timeout_based_on_affiliation(self, affiliation):
        # Dynamically adjust timeout based on affiliation
        if affiliation == 'premium':
            timeout_hours = 24
        elif affiliation == 'basic':
            timeout_hours = 16
        else: 
            # If no affiliation is recognized
            timeout_hours = 8
        
        self.app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=timeout_hours)


    def terminate_session(self):
        session.clear()
        return {"message": "Session terminated"}, 200
    
    def get_session_status(self):
        # Hint: Remember the session is cleared when terminated. 
        if 'user_id' in session:
            return {
                "message": "Session active", 
                "user_id": session.get('user_id'), 
                "affiliation": session.get('affiliation')
            }, 200
        else:
            return {"message": "No active session"}, 404
