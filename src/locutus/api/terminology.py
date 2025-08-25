from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import Coding, Terminology as Term
from locutus.model.exceptions import *
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection, get_editor
from bson import json_util 
import json

class TerminologyEdit(Resource):
    def put(self, id, code):
        """Add a new code to an existing terminology."""        
        body = request.get_json()
        display = body.get("display")
        description = body.get("description")

        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)

            t = Term.get(id)
            t.add_code(
                code=code, display=display, description=description, editor=editor
            )
            return json.loads(json_util.dumps(t.dump())), 201, default_headers

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

    def delete(self, id, code):
        """Remove a code from an existing terminology."""
        t = Term.get(id)
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
            t.remove_code(code, editor=editor)
        except KeyError as e:
            return str(e), 404, default_headers
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return json.loads(json_util.dumps(t.dump())), 200, default_headers


class TerminologyRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
            code_updates = body.get("code")
            display_updates = body.get("display")
            description_updates = body.get("description")

            t = Term.get(id)
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        print(f"Code Updates requested: {code_updates}")
        print(f"Display Updates requested: {display_updates}")
        print(f"Description updates requested: {description_updates}")

        # We MUST have at least a code or a display component to be a valid
        # PATCH
        if code_updates is None and display_updates is None:
            return (
                "Must provide codes and/or displays to be PATCHed.",
                400,
                default_headers,
            )

        if code_updates is None:
            code_updates = {}
        if display_updates is None:
            display_updates = {}
        if description_updates is None:
            description_updates = {}

        code_list = sorted(
            list(
                set(
                    list(code_updates.keys())
                    + list(display_updates.keys())
                    + list(description_updates.keys())
                )
            )
        )
        try:
            for code in code_list:
                original_code = code
                new_code = code_updates.get(original_code)

                if new_code is None:
                    new_code = original_code

                if not t.rename_code(
                    editor=editor,
                    original_code=original_code,
                    new_code=new_code,
                    new_display=display_updates.get(original_code),
                    new_description=description_updates.get(original_code),
                ):
                    return (
                        f"{original_code} was not found in the terminology.",
                        404,
                        default_headers,
                    )
        except APIError as e:
            return e.to_dict(), e.status_code, default_headers

        return json.loads(json_util.dumps(t.dump())), 201, default_headers


class Terminologies(Resource):
    def get(self):
        return (
            json.loads(json_util.dumps(Term.get(return_instance=False))),
            200,
            default_headers,
        )

    @cross_origin(allow_headers=["Content-Type"])
    def post(self):
        term = request.get_json()
        body = request.get_json()
        try:
            editor = get_editor(body=body, editor=None)
            if editor is None:
                raise LackingUserID(editor)
            if "resource_type" in term:
                del term["resource_type"]

            term['editor'] = editor
            t = Term(**term)
            t.save()

        except APIError as e:
            return e.to_dict(), e.status_code, default_headers
        return t.dump(), 201, default_headers


class Terminology(Resource):
    def get(self, id):
        response = Term.get(id, return_instance=False)

        if response is not None:
            return json.loads(json_util.dumps(response)), 200, default_headers
        
        return (response, 404, default_headers)

    def put(self, id):
        term = request.get_json()
        if "id" not in term:
            term["id"] = id

        if "resource_type" in term:
            del term["resource_type"]
        t = Term(**term)
        t.save()
        return t.dump(), 200, default_headers

    # @cross_origin()
    def delete(self, id):
        t = Term.get(id, return_instance=True)

        if t:
            t = t.delete()

        return json.loads(json_util.dumps(t)), 200, default_headers
