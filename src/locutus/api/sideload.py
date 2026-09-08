from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers, get_editor
from locutus.auth import forbidden_write_ids, require_auth
from locutus.model.exceptions import APIError, LackingRequiredParameter
from locutus.utility.sideload import SetMappings


class SideLoad(Resource):
    @require_auth
    def post(self):
        mapping_data = request.get_json()
        get_editor(body=mapping_data, editor=None)

        csv_contents = mapping_data["csvContents"]

        # M12: a CSV can reference many tables at once -- reject the whole
        # request before writing anything if current_user lacks write
        # access to any of them, rather than applying some rows and not
        # others. A table_id that doesn't exist at all is left to
        # SetMappings' own check below, unchanged.
        table_ids = sorted({row["table_id"] for row in csv_contents})
        forbidden = forbidden_write_ids("Table", table_ids, g.current_user)
        if forbidden:
            return (
                {"message": "Forbidden", "table_ids": forbidden},
                403,
                default_headers,
            )

        try:
            return SetMappings(csv_contents)
        except LackingRequiredParameter as e:
            return e.to_dict(), 400
        except APIError as e:
            return e.to_dict(), 400
