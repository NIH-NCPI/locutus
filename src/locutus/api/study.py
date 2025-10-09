from flask_restful import Resource
from flask import request
from locutus.model.study import Study as mStudyTerm
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat
from locutus.api import default_headers

from bson import json_util 
import json

class Studies(Resource):
    def get(self):
        return (
            json.loads(json_util.dumps(mStudyTerm.get(return_instance=False))),
            200,
            default_headers,
        )

    def post(self):
        sty = request.get_json()
        if "resource_type" in sty:
            del sty["resource_type"]

        return_code = 201
        msg = ""

        if "title" not in sty:
            return_code = 400
            msg = "Study Title Required"

        if "name" not in sty:
            return_code = 400
            msg = "Study Name Required"

        if return_code > 399:
            return msg, return_code, default_headers

        study = mStudyTerm(**sty)
        study.save()
        return json.loads(json_util.dumps(study.dump())), 201, default_headers

    def delete_dd_references(self, id):
        affected_ids = 0
        
        for study in mStudyTerm.get(return_instance=True):
            matched_references = study.remove_dd(id)

            if matched_references > 0:
                study.save()
                affected_ids += matched_references 

        return affected_ids


class Study(Resource):
    def get(self, id):
        study = mStudyTerm.get(id)
        if study is None:
            return (
                f"There is no Study, {id}.",
                404,
                default_headers,
            )
        return json.loads(json_util.dumps(study.dump())), 200, default_headers

    def put(self, id):
        sty = request.get_json()
        if "id" not in sty:
            sty["id"] = id

        if "resource_type" in sty:
            del sty["resource_type"]

        study = mStudyTerm(**sty)
        study.save()
        return json.loads(json_util.dumps(study.dump())), 201, default_headers

    def delete(self, id):
        study = mStudyTerm.get(id)
        t = study.dump()
        study.delete()

        return json.loads(json_util.dumps(t)), 200, default_headers


class StudyEdit(Resource):
    def delete(self, id, dd_id):
        study = mStudyTerm.get(id)
        count = study.remove_dd(dd_id)
        if count < 1:
            return (
                f"{dd_id} id is not found in Study, {study.name}.",
                404,
                default_headers,
            )
        study.save()
        return json.loads(json_util.dumps(study.dump())), 200, default_headers

class StudyHarmony(Resource):
    def get(self, id):
        data_format = request.args.get('format', 'Whistle')
        file_format = request.args.get('file-format', 'JSON')

        try:
            if data_format:
                data_format = HarmonyFormat(data_format)
            if file_format:
                file_format = HarmonyOutputFormat(file_format)
        except ValueError as e:
            return {"message_to_user": str(e)}, 400, default_headers

        print(f"Exporting Study Harmony: ")
        print(f"Harmony format: {data_format}")
        print(f"File format: {file_format}")
        t = mStudyTerm.get(id)

        try:
            harmony = t.as_harmony(harmony_format=data_format, harmony_output_format=file_format)
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return json.loads(json_util.dumps(harmony)), 200, default_headers
