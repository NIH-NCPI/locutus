from flask import session
from datetime import timedelta

class SessionManager:
    def __init__(self, app):
        self.app = app
        self.app.config['SESSION_PERMANENT'] = True

    def initiate_session(self, user_id, affiliation=None):
        if not affiliation:
            affiliation = 'basic'
        
        session['user_id'] = user_id

        if affiliation:
            session['affiliation'] = affiliation
        else:
            session['affiliation'] = 'Not affiliated'

        # Adjust session timeout based on affiliation.
        self.set_timeout_based_on_affiliation(affiliation)
        
        return {"message": f"Session started for user {user_id} with the {affiliation} affiliation "}, 200

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
# 
    def get_session_status(self):
        # Hint: Remember the session is cleared when terminated. 
        if 'user_id' in session:
            return {
                "message": "Session active", 
                "user_id": session['user_id'], 
                "affiliation": session['affiliation']
            }, 200
        else:
            return {"message": "No active session"}, 404
