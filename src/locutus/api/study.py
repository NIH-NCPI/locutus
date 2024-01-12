from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.study import Study as mStudyTerm
from locutus.api import default_headers


class Studies(Resource):
    def get(self):
        return (
            [x.dump() for x in persistence().collection("Study").documents()],
            200,
            default_headers,
        )

    def post(self):
        sty = request.get_json()
        if "resource_type" in sty:
            del sty["resource_type"]

        study = mStudyTerm(**sty)
        study.save()
        return study.dump(), 201, default_headers


class Study(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("Study").document(id)
        return t, 200, default_headers

    def put(self, study):
        sty = request.get_json()
        if "id" not in sty:
            sty["id"] = id

        del sty["resource_type"]

        study = mStudyTerm(**sty)
        study.save()
        return study.dump(), 201, default_headers

    def delete(self, id):
        t = persistence().collection("Study").delete(id)

        if t is not None:
            persistence().save()

        return t, 200, default_headers
