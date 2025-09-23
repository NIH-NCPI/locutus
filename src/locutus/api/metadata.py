import os
from flask_restful import Resource
from locutus._version import __version__

class Version(Resource):
    def get(self):
        """Retrieve the VERSION environment variable. The version is set at
        deployment. """
        version = os.getenv('VERSION', __version__)
        return {'version': version}
