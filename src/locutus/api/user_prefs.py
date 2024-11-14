from flask_restful import Resource
from flask import request
from locutus.api import default_headers, get_editor


class UserPrefOntoFilters(Resource):
    def get(self):

        try:
            editor = get_editor({})
        except:
            editor = "Application Default"
        # For now, we will just return a constant
        return {editor: {"api_preference": {"ols": ["mondo", "hp", "maxo", "ncit"]}}}
