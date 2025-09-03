from flask_restful import Resource
from flask import request
from locutus.model.table import Table as mTable
from locutus.api import default_headers, get_editor, delete_collection
from locutus.model.exceptions import *
from bson import json_util 
import json


class TableOntologyAPISearchPreferences(Resource):
    def get(self, id, code=None):
        t = mTable.get(id)

        try:
            prefs = t.get_preference(code=code)
        
            if "self" not in prefs:
                prefs = {
                    "self": prefs
                }
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers

        return json.loads(json_util.dumps(prefs)), 200, default_headers

    def post(self, id, code=None):
        """Create or add an `api_preference` for a specific Table or code."""
        body = request.get_json()
        t = mTable.get(id)
        if "api_preference" not in body:
            return {"message": "api_preference is required"}, 400

        api_preference = body["api_preference"]

        t.add_or_update_pref(api_preference=api_preference, code=code)
        response = {
            "table": {"Reference": f"Table/{t.id}"},
            "onto_api_preference": api_preference,
        }

        return (response, 200, default_headers)

    def put(self, id, code=None):
        """Update an `api_preference` for a specific Table or code."""
        body = request.get_json()
        t = mTable.get(id)
        if "api_preference" not in body:
            return {"message": "api_preference is required"}, 400

        api_preference = body["api_preference"]

        t.add_or_update_pref(api_preference=api_preference, code=code)
        response = {
            "table": {"Reference": f"Table/{t.id}"},
            "onto_api_preference": api_preference,
        }

        return (response, 200, default_headers)

    def delete(self, id, code=None):
        """Remove an `api_preference` from a specific Table or code."""
        t = mTable.get(id)

        message = t.remove_pref(code=code)

        response = {"message": message, "table": {"Reference": f"Table/{t.id}"}}

        return (response, 200, default_headers)


class TablePreferredTerminology(Resource):
    def get(self, id=None):
        """
        Retrieve the preferred terminology for a specific Terminology

        Args:
            id (str): Defines the terminology of interest

        Example Response:
        {
            "references": [
                {
                    "reference": "Terminology/tm--example1"
                },
                {
                    "reference": "Terminology/tm--example2"
                }
            ]
        }
        """
        t = mTable.get(id)

        pref = t.get_preferred_terminology()

        return (json.loads(json_util.dumps(pref)), 200, default_headers)

    def put(self, id):
        """
        Creates one or more preferred terminologies to a specific Terminology.
        This will replace what already exists. Provinance exists for this.

        Args:
            id (str): The ID of the Term to which the preferred terminology will be added.

        Example Request Body:
        {
            "editor": "me",
            "preferred_terminologies": [
                {
                    "preferred_terminology": "tm--example1"
                },
                {
                    "preferred_terminology": "tm--example6"
                }
            ]
        }
        """
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            t = mTable.get(id)

            if not isinstance(body, dict) or not isinstance(
                body.get("preferred_terminologies", []), list
            ):
                return {"message": "'preferred_terminologies' should be a list"}, 400

            preferred_terminologies = body["preferred_terminologies"]

            # Ensure each item in preferred_terminologies contains the key 'preferred_terminology'
            if not all(
                "preferred_terminology" in item for item in preferred_terminologies
            ):
                return {
                    "message": "Each item in 'preferred_terminologies' must contain 'preferred_terminology'"
                }, 400

            # Replace all preferred terminologies and store the editor
            t.replace_preferred_terminology(
                editor=editor, preferred_terminology=preferred_terminologies
            )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        response = {"id": t.id, "references": preferred_terminologies}
        return (response, 200, default_headers)

    def delete(self, id):
        t = mTable.get(id)

        t.remove_preferred_terminology()

        response = {
            "message": f"The preferred_terminology collection was deleted for: {id}."
        }

        return response, 200, default_headers
