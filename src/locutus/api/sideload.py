from flask_restful import Resource
from flask import request

from bson import json_util 
import json

from locutus.api import default_headers, get_editor
from locutus.utility.sideload import SetMappings

from locutus.model.exceptions import LackingRequiredParameter

class SideLoad(Resource):
    def post(self):
        mapping_data = request.get_json()
        editor = get_editor(body=mapping_data, editor=None)

        try:
            return SetMappings(mapping_data['csvContents'])
        except LackingRequiredParameter as e:
            return e.to_dict(), 400