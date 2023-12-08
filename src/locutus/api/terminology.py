from flask_restful import Resource
from locutus.api import persistence
from locutus.model.terminology import Terminology as Term

import pdb


class Terminologies(Resource):
    def get(self):
        return [x.dump() for x in persistence().collection("Terminology").documents()]

    def post(self):
        pass


class Terminology(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("Terminology").document(id)
        return t

    def put(self, term):
        t = Term(**term)
        t.save()

    def delete(self, id):
        pass
