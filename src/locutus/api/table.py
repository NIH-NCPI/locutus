from flask_restful import Resource
from locutus import persistence
from locutus.model.table import Table as mTable


class Tables(Resource):
    def get(self):
        return [x.dump() for x in persistence().collection("Table").documents()]

    def post(self):
        pass


class Table(Resource):
    def get(self, id):
        # pdb.set_trace()
        t = persistence().collection("Table").document(id)
        return t

    def put(self, term):
        t = mTable(**term)
        t.save()

    def delete(self, id):
        pass
