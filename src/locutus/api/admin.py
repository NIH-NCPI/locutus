"""
Admin-only institution management (Auth Requirements spec, M3, S3).
Institutions aren't part of the M4 owner/access resource model -- every
endpoint here is gated by @require_admin (the system-level role), not
require_read_access/require_write_access.
"""

import json

from bson import json_util
from flask import request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import require_admin
from locutus.model.institution import Institution


class AdminInstitutions(Resource):
    @require_admin
    def get(self):
        institutions = [i.to_dict() for i in Institution.all()]
        return json.loads(json_util.dumps(institutions)), 200, default_headers

    @require_admin
    def post(self):
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        if not name:
            return {"message": "name is required"}, 400, default_headers

        institution_id = body.get("id")
        if institution_id and Institution.get(institution_id) is not None:
            return (
                {"message": f"Institution already exists: {institution_id}"},
                409,
                default_headers,
            )

        institution = Institution(
            id=institution_id,
            name=name,
            allowed_emails=body.get("allowedEmails", []),
        )
        institution.save()
        return (
            json.loads(json_util.dumps(institution.to_dict())),
            201,
            default_headers,
        )


class AdminInstitution(Resource):
    @require_admin
    def get(self, id: str):
        institution = Institution.get(id)
        if institution is None:
            return {"message": f"Institution not found: {id}"}, 404, default_headers
        return (
            json.loads(json_util.dumps(institution.to_dict())),
            200,
            default_headers,
        )


class AdminInstitutionAllowlist(Resource):
    """S3: pre-registering emails that are allowed to create an account
    under a given institution on first Google login (see api/auth.py's
    GoogleLogin)."""

    @require_admin
    def get(self, id: str):
        institution = Institution.get(id)
        if institution is None:
            return {"message": f"Institution not found: {id}"}, 404, default_headers
        return (
            json.loads(json_util.dumps(institution.allowed_emails)),
            200,
            default_headers,
        )

    @require_admin
    def post(self, id: str):
        institution = Institution.get(id)
        if institution is None:
            return {"message": f"Institution not found: {id}"}, 404, default_headers

        body = request.get_json(silent=True) or {}
        emails = body.get("emails")
        if not emails and body.get("email"):
            emails = [body["email"]]
        if not emails:
            return (
                {"message": "This action requires the parameter: 'emails'"},
                400,
                default_headers,
            )

        for email in emails:
            if email not in institution.allowed_emails:
                institution.allowed_emails.append(email)
        institution.save()

        return (
            json.loads(json_util.dumps(institution.allowed_emails)),
            200,
            default_headers,
        )


class AdminInstitutionAllowlistItem(Resource):
    @require_admin
    def delete(self, id: str, email: str):
        institution = Institution.get(id)
        if institution is None:
            return {"message": f"Institution not found: {id}"}, 404, default_headers

        if email not in institution.allowed_emails:
            return (
                {"message": f"{email} is not on {id}'s allowlist"},
                404,
                default_headers,
            )

        institution.allowed_emails.remove(email)
        institution.save()

        return (
            json.loads(json_util.dumps(institution.allowed_emails)),
            200,
            default_headers,
        )
