from flask_restful import Resource
from locutus import persistence
from locutus.model.study import Study as mStudy


class Studies(Resource):
    def get(self):
        return [x.dump() for x in persistence().collection("Study").documents()]

    def post(self):
        pass


class Study(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("Study").document(id)
        return t

    def put(self, study):
        t = mStudy(**study)
        t.save()

    def delete(self, id):
        pass
