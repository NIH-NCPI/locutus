from flask_restful import Resource

from locutus.api import get_editor


class UserPrefOntoFilters(Resource):
    def get(self):

        try:
            editor = get_editor({}, editor=None)
        except Exception:  # noqa: BLE001 - this endpoint must not fail regardless of cause
            editor = "Application Default"
        # For now, we will just return a constant
        return {editor: {"api_preference": {"ols": ["mondo", "hp", "maxo", "ncit"]}}}
