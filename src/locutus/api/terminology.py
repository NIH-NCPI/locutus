from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.terminology import CodeAlreadyPresent, Coding, Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers, delete_collection, get_editor

import pdb


class TerminologyEdit(Resource):
    def put(self, id, code):
        """Add a new code to an existing terminology."""
        body = request.get_json()
        display = body.get("display")
        description = body.get("description")

        editor = get_editor(body)

        t = Term.get(id)
        try:
            t.add_code(code=code, display=display, description=description, editor=editor)
        except CodeAlreadyPresent as e:
            return str(e), 400, default_headers

        return t.dump(), 201, default_headers

    def delete(self, id, code):
        """Remove a code from an existing terminology."""
        t = Term.get(id)
        body = request.get_json()
        editor = get_editor(body)

        try:
            t.remove_code(code, editor=editor)
        except KeyError as e:
            return str(e), 404, default_headers

        return t.dump(), 200, default_headers


class TerminologyRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        editor = get_editor(body)
        code_updates = body.get("code")
        display_updates = body.get("display")
        description_updates = body.get("description")

        t = Term.get(id)

        # pdb.set_trace()

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

        return t.dump(), 201, default_headers


class Terminologies(Resource):
    def get(self):
        return (
            [x.to_dict() for x in persistence().collection("Terminology").stream()],
            200,
            default_headers,
        )

    @cross_origin(allow_headers=["Content-Type"])
    def post(self):
        term = request.get_json()
        body = request.get_json()
        editor = get_editor(body)
        if "resource_type" in term:
            del term["resource_type"]
        if editor:
            self.add_provenance(
                Terminology.ChangeType.CreateTerminology, editor=editor, target="self"
            )

        t = Term(**term)
        t.save()
        return t.dump(), 201, default_headers


class Terminology(Resource):
    def get(self, id):
        response = Term.get(id, return_instance=False)

        if response is not None:
            return response, 200, default_headers
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
        mapref = (
            persistence().collection("Terminology").document(id).collection("mappings")
        )
        delete_collection(mapref)
        dref = persistence().collection("Terminology").document(id)
        t = dref.get().to_dict()

        time_of_delete = dref.delete()

        return t, 200, default_headers

class OntologyAPISearchPreferences(Resource):
    def get(self, id=None, code=None):
        t = Term.get(id)

        pref = t.get_preference(code=code)

        return (pref, 200, default_headers)
        
    def post(self, id, code=None):
        """Create or add an `api_preference` for a specific Terminology or Code."""
        body = request.get_json()
        t = Term.get(id)
        if "api_preference" not in body:
            return {"message": "api_preference is required"}, 400

        api_preference = body["api_preference"]

        t.add_or_update_pref(api_preference=api_preference, code=code)
        response = {
            "terminology": {"Reference": f"Terminology/{t.id}"},
            "onto_api_preference": api_preference,
        }

        return (response, 200, default_headers)

    def put(self, id, code=None):
        """Update an `api_preference` for a specific Terminology or Code."""
        body = request.get_json()
        t = Term.get(id)
        if "api_preference" not in body:
            return {"message": "api_preference is required"}, 400

        api_preference = body["api_preference"]

        t.add_or_update_pref(api_preference=api_preference, code=code)
        response = {
            "terminology": {"Reference": f"Terminology/{t.id}"},
            "onto_api_preference": api_preference,
        }

        return (response, 200, default_headers)

    def delete(self, id, code=None):
        """Remove an `api_preference` from a specific Terminology or Code."""
        t = Term.get(id)

        message = t.remove_pref(code=code)

        response = {
            "message": message,
            "terminology": {"Reference": f"Terminology/{t.id}"}
        }

        return (response, 200, default_headers)
    
class PreferredTerminology(Resource):
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
        t = Term.get(id)

        pref = t.get_preferred_terminology()

        return (pref, 200, default_headers)
        
    def put(self, id):
        """
        Creates one or more preferred terminologies to a specific Terminology.
        This will replace what already exists. Provinance exists for this.

        Args:
            id (str): The ID of the Term to which the preferred terminology will be added.
        
        Example Request Body:
        [
            {
                "preferred_terminology": "tm--example1"
            },
            {
                "preferred_terminology": "tm--example2"
            }
        ]

        Example Response:
        {
            "id": "term123",
            "references": [
                {
                    "preferred_terminology": "tm--example1"
                },
                {
                    "preferred_terminology": "tm--example2"
                }
            ]
        }
        """
        body = request.get_json()
        t = Term.get(id)

        if not isinstance(body, dict) or "editor" not in body or not isinstance(body.get("preferred_terminologies", []), list):
            return {"message": "'editor' is required and 'preferred_terminologies' should be a list"}, 400


        preferred_terminologies = body["preferred_terminologies"]

        # Ensure each item in preferred_terminologies contains the key 'preferred_terminology'
        if not all("preferred_terminology" in item for item in preferred_terminologies):
            return {"message": "Each item in 'preferred_terminologies' must contain 'preferred_terminology'"}, 400

        editor = body["editor"]

        # Replace all preferred terminologies and store the editor
        t.replace_preferred_terminology(editor=editor, preferred_terminology=preferred_terminologies)

        response = {
            "id": t.id,
            "references": preferred_terminologies
        }
        return (response, 200, default_headers)
    
    def delete(self, id):
        pref_terms = (
            persistence().collection("Terminology").document(id).collection("preferred_terminology")
        )
        delete_collection(pref_terms)

        response = {
            "message": f"The preferred_terminology collection was deleted for terminology {id}."}
        
        return response, 200, default_headers