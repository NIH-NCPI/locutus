""" Generic Harmony export that allows users to specify one or more IDs to add to a single harmony result"""

from flask_restful import Resource
from flask import request
from locutus.model.study import build_combined_harmony
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat
from locutus.api import default_headers

from bson import json_util 
import json
class CombinedHarmony(Resource):
    def get(self):
        data_format = request.args.get('format', 'Whistle')
        file_format = request.args.get('file-format', 'JSON')
        study_ids = request.args.get('studies', "")
        dd_ids = request.args.get('datadictionaries', "")
        table_ids = request.args.get('tables', "")

        import pdb 
        pdb.set_trace()
        try:
            if data_format:
                data_format = HarmonyFormat(data_format)
            if file_format:
                file_format = HarmonyOutputFormat(file_format)

            harmony = build_combined_harmony(study_ids=study_ids, 
                    dd_ids=dd_ids, 
                    table_ids=table_ids, 
                    harmony_format=data_format, 
                    harmony_output_format=file_format)

        except ValueError as e:
            return {"message_to_user": str(e)}, 400, default_headers



        return json.loads(json_util.dumps(harmony)), 200, default_headers