from flask_restful import Resource
from locutus.api import get_editor


class UserPrefOntoFilters(Resource):
    def get(self):

        try:
            editor = get_editor({})
        except Exception:
            editor = "Application Default"
        # For now, we will just return a constant
        return {editor: {"api_preference": {"ols": ["mondo", "hp", "maxo", "ncit"]}}}
