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
from locutus.model.user import User


def _institution_dict_with_members(institution: Institution) -> dict:
    """Institution.to_dict() plus a resolved `members` array -- memberIds
    alone is a list of opaque user ids, which gives an admin UI no way to
    show who that actually is or when they last logged in. Additive only:
    memberIds itself is left exactly as it was, so anything already reading
    that field is unaffected. A memberIds entry with no matching User (a
    stale/deleted account) is silently skipped rather than raising.
    """
    data = institution.to_dict()
    members = []
    for user_id in institution.member_ids:
        user = User.get(user_id)
        if user is None:
            continue
        members.append(
            {
                "id": user.id,
                "email": user.email,
                "displayName": user.display_name,
                "role": user.role,
                "lastLoginAt": user.last_login_at,
            }
        )
    data["members"] = members
    return data


class AdminInstitutions(Resource):
    @require_admin
    def get(self):
        institutions = [_institution_dict_with_members(i) for i in Institution.all()]
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
            json.loads(json_util.dumps(_institution_dict_with_members(institution))),
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

        # Doubles as "revoke this institution's access" for anyone already
        # provisioned under this email -- removing only memberIds here
        # would be cosmetic, since get_permission() never consults it, only
        # the user's own institutionIds. Both have to drop this institution
        # or the allowlist edit wouldn't actually revoke anything for
        # someone who already has an account.
        user = User.find_by_email(email)
        if user is not None:
            assert user.id is not None
            if id in user.institution_ids:
                user.institution_ids.remove(id)
                user.save()
            institution.remove_member(user.id)

        institution.save()

        return (
            json.loads(json_util.dumps(institution.allowed_emails)),
            200,
            default_headers,
        )
