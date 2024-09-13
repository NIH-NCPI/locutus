from flask_restful import Resource
from flask import request

class SessionStart(Resource):
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def post(self):
        body = request.get_json()

        user_id = body.get('user_id')
        if "user_id" not in body:
            return {"message": "user_id is required"}, 400

        affiliation = body.get('affiliation')

        return self.session_manager.initiate_session(user_id, affiliation)

class SessionTerminate(Resource):
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def post(self):
        return self.session_manager.terminate_session()

class SessionStatus(Resource):
    def __init__(self, session_manager):
        self.session_manager = session_manager

    def get(self):
        return self.session_manager.get_session_status()
