from flask_restful import Resource
from flask import request
from locutus import persistence
from locutus.model.table import Table as mTable
from locutus.api import default_headers, get_editor
from locutus.api.datadictionary import DataDictionaries
from copy import deepcopy

import pdb


class TableRenameCode(Resource):
    def patch(self, id):
        body = request.get_json()
        varname_updates = body.get("variable")
        description_updates = body.get("description")

        editor = get_editor(body)
        if editor is None:
            return ("table edit requires an editor!", 400, default_headers)

        table = mTable.get(id)
        # print(f"Variable name updates requested: {varname_updates}")
        # print(f"Description updates requested: {description_updates}")

        # We MUST have at least a code or a display component to be a valid
        # PATCH
        if varname_updates is None and description_updates is None:
            return (
                "Must provide variable names and/or descriptions to be PATCHed.",
                400,
                default_headers,
            )

        if varname_updates is None:
            varname_updates = {}
        if description_updates is None:
            description_updates = {}

        var_list = sorted(
            list(set(list(varname_updates.keys()) + list(description_updates.keys())))
        )

        for var in var_list:
            original_code = var
            new_code = varname_updates.get(original_code)

            if new_code is None:
                new_code = original_code

            if not table.rename_var(
                original_varname=original_code,
                new_varname=new_code,
                new_description=description_updates.get(original_code),
                editor=editor,
            ):
                return (
                    f"{original_code} was not found in the terminology.",
                    404,
                    default_headers,
                )

        return table.dump(), 201, default_headers


class TableEdit(Resource):
    def put(self, id, code):
        """Add a new variable to an existing table"""

        table = mTable.get(id)
        body = request.get_json()

        editor = get_editor(body)
        if editor is None:
            return ("table PUT requires an editor!", 400, default_headers)

        vardef = deepcopy(body)
        vardef["name"] = code

        table.add_variable(vardef, editor=editor)

        if "api_preference" in body:
            table.update_api_preference(body["api_preference"])

        table.save()
        return table.dump(), 201, default_headers

    def delete(self, id, code):
        """Add a new variable to an existing table"""

        table = mTable.get(id)
        body = request.get_json()

        editor = get_editor(body)
        if editor is None:
            return ("table edit requires an editor!", 400, default_headers)

        try:
            table.remove_variable(code, editor=editor)
            table.save()
        except KeyError as e:
            return str(e), 404, default_headers

        return table.dump(), 200, default_headers


class Tables(Resource):
    def get(self):
        """
        TODO: Paginate these ResourceType/get calls
        Technically, this will probably not get so big as to be a problem
        but it's technically not wise to pull these into a single response.
        We should plan on paginating this at some point."""
        return (
            [x.to_dict() for x in persistence().collection("Table").stream()],
            200,
            default_headers,
        )

    def post(self):
        tbl = request.get_json()

        editor = get_editor(tbl)

        if editor is None:
            return ("table edit requires an editor!", 400, default_headers)
        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return t.dump(), 201, default_headers


class Table(Resource):
    def get(self, id):
        # pdb.set_trace()
        return mTable.get(id, return_instance=False)

    def put(self, id):
        tbl = request.get_json()

        if "editor" not in tbl:
            return ("table PUT requires an editor!", 400, default_headers)

        if "id" not in tbl:
            tbl["id"] = id

        if "resource_type" in tbl:
            del tbl["resource_type"]

        t = mTable(**tbl)
        t.save()
        return t.dump(), 200, default_headers

    def delete(self, id):
        body = request.get_json()
        editor = get_editor(body)
        if editor not in body:
            return ("table DELETE  requires an editor!", 400, default_headers)

        # This is a bit "out of band"
        t = mTable.get(id)
        t.terminology().dereference().add_provenance(
            change_type=Terminology.ChangeType.RemoveTable,
            target="self",
            old_value=f"Table Name: {t.name}",
            editor=editor,
        )

        dref = persistence().collection("Table").document(id)

        # Delete any references to the table from any data-dictionaries:
        DataDictionaries().delete_table_references(id)

        t = dref.get().to_dict()
        time_of_delete = dref.delete()
        # if t is not None:
        #    persistence().save()

        return t, 200, default_headers


class HarmonyCSV(Resource):
    def get(self, id):
        t = mTable.get(id)

        try:
            harmony = t.as_harmony()
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return harmony, 200, default_headers

class TableOntologyAPISearchPreferences(Resource):
    def get(self, id, code=None):
        """Retrieve the `api_preference` for a specific Terminology or Code."""
        t = mTable.get(id)
        
        if t is None:
            return {"message": f"Terminology with ID {id} not found."}, 404, default_headers

        if code:
            # Logic for getting preference to a specific code
            api_preference_code = None
            for t_var in t.variables:
                if t_var.code == code:
                    api_preference_code = t_var.api_preference
                    break

            if api_preference_code is None:
                return {"message": "No API preference set for this code in the table."}, 404, default_headers

            return api_preference_code, 200, default_headers
        else:
            # Logic for getting preference to a specific table
            api_preference = t.api_preference
            
            if api_preference is None:
                return {"message": "No API preference set for this table."}, 404, default_headers

            return api_preference, 200, default_headers
        
    def post(self, id, code=None):
        """Create or add an `api_preference` for a specific Table or Variable."""
        body = request.get_json()

        if "api_preference" not in body:
            return {"message": "api_preference is required"}, 400

        api_preference = body["api_preference"]

        t = mTable.get(id)

        if t is None:
            return {"message": "Table not found"}, 404

        if code:
            # Logic for adding preference to a specific variable
            code_found = False

            for t_var in t.variables:
                if t_var.code == code:
                    t_var.api_preference = api_preference
                    code_found = True
                    break

            if not code_found:
                return {"message": f"Code {code} not found in the Table."}, 404

        else:
            # Logic for adding preference to the entire table
            t.api_preference = api_preference

        t.save()

        return t.dump(), 200, default_headers

    def put(self, id, code=None):
        """Add or update an `api_preference` for a specific Table or Code."""
        body = request.get_json()
        api_preference = body.get("api_preference")
        editor = get_editor(body)

        t = mTable.get(id)
        if t is None:
            return {"message": "Table not found"}, 404

        if code:
            # Logic for updating preference for a specific code
            code_found = False

            for t_var in t.variables:
                if t_var.code == code:
                    if not t_var.api_preference:
                        return {"message": f"No existing API preference found for code {code}. Use POST to add."}, 404
                    t_var.api_preference = api_preference
                    code_found = True
                    break

            if not code_found:
                return {"message": f"Code {code} not found in the Table."}, 404
            
            t.add_or_update_pref(api_preference=api_preference, editor=editor, code=code)

            return {"api_preference": t_var.api_preference}, 201, default_headers

        else:
            # Logic for updating preference for the entire table
            t.add_or_update_pref(api_preference=api_preference, editor=editor)

            return t.dump(), 201, default_headers

    def delete(self, id, code=None):
        """Remove an `api_preference` from a specific Table or Code."""
        body = request.get_json()
        pref = body.get("api_preference")
        editor = get_editor(body)

        t = mTable.get(id)
        if t is None:
            return {"message": "Table not found."}, 404

        if code:
            # Logic for removing preference from a specific code
            code_found = False

            for t_var in t.variables:
                if t_var.code == code:
                    code_found = True

                    for pref_key in pref.keys():
                        if pref_key in t_var.api_preference:
                            t.remove_pref(api_preference=pref_key, editor=editor, code=code)
                        else:
                            return {"message": f"Preference key '{pref_key}' not found in the code {code}."}, 404
                    break

            if not code_found:
                return {"message": f"Code {code} not found in the Table."}, 404

        else:
            # Logic for removing preference from the entire table
            not_found_keys = []

            for pref_key in pref.keys():
                try:
                    t.remove_pref(pref_key, editor=editor)
                except KeyError:
                    not_found_keys.append(pref_key)

            if not_found_keys:
                return f"Preferences not found: {', '.join(not_found_keys)}", 404, default_headers

        t.save()

        return t.dump(), 200, default_headers