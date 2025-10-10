from flask_restful import Resource
from flask import request

from bson import json_util 
import json

from locutus.utility.sideload import SetMappings

Class SideLoad(Resource):
    def post(self):
        mapping_data = request.get_json()
        editor = get_editor(body=mapping_data, editor=None)

        return SetMappings(mapping_data['csvContents'])