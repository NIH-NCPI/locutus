from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.study import Study as mStudyTerm
from locutus.api import default_headers


class Studies(Resource):
    def get(self):
        return (
            [doc.to_dict() for doc in persistence().collection("Study").stream()],
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
        return study.dump(), 201, default_headers

    def delete_dd_references(self, id):
        affected_ids = 0
        for resource in persistence().collection("Study").stream():
            resource_dict = resource.to_dict()
            if "resource_type" in resource_dict:
                del resource_dict["resource_type"]
            obj = mStudyTerm(**resource_dict)

            matched_references = obj.remove_dd(id)

            if matched_references > 0:
                obj.save()

                affected_ids += 1

        return affected_ids


class Study(Resource):
    def get(self, id):
        t = persistence().collection("Study").document(id).get()
        if t.exists:
            t_dict = t.to_dict()
            t_dict.pop("_id", None)
            return t_dict, 200, default_headers
        return {"error": "Study not found"}, 404, default_headers

    def put(self, id):
        sty = request.get_json()
        if "id" not in sty:
            sty["id"] = id

        if "resource_type" in sty:
            del sty["resource_type"]

        study = mStudyTerm(**sty)
        study.save()
        return study.dump(), 201, default_headers

    def delete(self, id):
        dref = persistence().collection("Study").document(id)
        t = dref.get().to_dict()
        time_of_delete = dref.delete()
        # if t is not None:
        #    persistence().save()

        return t, 200, default_headers


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
        return study.dump(), 200, default_headers
