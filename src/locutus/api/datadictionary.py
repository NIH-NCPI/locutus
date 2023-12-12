from flask_restful import Resource
from locutus import persistence
from locutus.model.datadictionary import DataDictionary as DD


class DataDictionaries(Resource):
    def get(self):
        return [
            x.dump() for x in persistence().collection("DataDictionary").documents()
        ]

    def post(self):
        pass


class DataDictionary(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("DataDictionary").document(id)
        return t

    def put(self, study):
        t = DD(**study)
        t.save()

    def delete(self, id):
        pass
