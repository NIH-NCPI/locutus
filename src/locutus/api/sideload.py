from flask import request
from flask_restful import Resource

from locutus.api import get_editor
from locutus.model.exceptions import APIError, LackingRequiredParameter
from locutus.utility.sideload import SetMappings


class SideLoad(Resource):
    def post(self):
        mapping_data = request.get_json()
        get_editor(body=mapping_data, editor=None)

        try:
            return SetMappings(mapping_data["csvContents"])
        except LackingRequiredParameter as e:
            return e.to_dict(), 400
        except APIError as e:
            return e.to_dict(), 400
