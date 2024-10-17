import os
from flask_restful import Resource

class Version(Resource):
    def get(self):
        """Retrieve the VERSION environment variable. The version is set at
        deployment. """
        version = os.getenv('VERSION', 'Version not set')
        return {'version': version}
