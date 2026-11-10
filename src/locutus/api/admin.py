"""
Admin-only institution and user management (Auth Requirements spec, M3,
S3, S4), and the audit log those user changes are recorded in. Neither institutions nor users are part of the M4 owner/access
resource model -- every endpoint here is gated by @require_admin (the
system-level role), not require_read_access/require_write_access.
"""

import json
import re
from datetime import UTC, datetime

from bson import json_util
from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import require_admin
from locutus.model.audit_event import AuditEvent
from locutus.model.institution import Institution
from locutus.model.user import User

# Pragmatic "looks like an email" check, not full RFC 5322 -- just enough
# to catch plainly-wrong input like a bare "1" rather than validate every
# edge case a real address can take.
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _invalid_emails(emails: list[str]) -> list[str]:
    return [e for e in emails if not _EMAIL_RE.match(e)]


def _reason() -> str | None:
    body = request.get_json(silent=True) or {}
    return body.get("reason") or None


def _record(action: AuditEvent.Action, user: User) -> None:
    assert user.id is not None
    AuditEvent.record(
        action,
        actor_id=g.current_user["user_id"],
        target_user_id=user.id,
        reason=_reason(),
    )


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

        allowed_emails = body.get("allowedEmails", [])
        invalid = _invalid_emails(allowed_emails)
        if invalid:
            return (
                {"message": f"Not a valid email address: {', '.join(invalid)}"},
                400,
                default_headers,
            )

        institution = Institution(
            id=institution_id,
            name=name,
            allowed_emails=allowed_emails,
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

        invalid = _invalid_emails(emails)
        if invalid:
            return (
                {"message": f"Not a valid email address: {', '.join(invalid)}"},
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


class AdminUsers(Resource):
    """S4: admin-facing user directory -- memberIds/allowedEmails alone
    (the institution endpoints above) give no way to see everyone in the
    system at once, independent of institution."""

    @require_admin
    def get(self):
        users = [u.to_dict() for u in User.all()]
        return json.loads(json_util.dumps(users)), 200, default_headers


class AdminUser(Resource):
    @require_admin
    def get(self, id: str):
        user = User.get(id)
        if user is None:
            return {"message": f"User not found: {id}"}, 404, default_headers
        return json.loads(json_util.dumps(user.to_dict())), 200, default_headers


class AdminUserDisable(Resource):
    """S4: off-boarding without deletion -- see the disabled_at checks in
    locutus/auth.py and api/auth.py's GoogleLogin for the enforcement side.
    This endpoint only ever sets/clears the flag; it doesn't touch owned
    resources, provenance, or institution membership."""

    @require_admin
    def post(self, id: str):
        if id == g.current_user["user_id"]:
            return (
                {"message": "You cannot disable your own account"},
                403,
                default_headers,
            )

        user = User.get(id)
        if user is None:
            return {"message": f"User not found: {id}"}, 404, default_headers

        user.disabled_at = datetime.now(UTC)
        user.disabled_by = g.current_user["user_id"]
        user.save()
        _record(AuditEvent.Action.UserDisable, user)
        return json.loads(json_util.dumps(user.to_dict())), 200, default_headers


class AdminUserEnable(Resource):
    @require_admin
    def post(self, id: str):
        user = User.get(id)
        if user is None:
            return {"message": f"User not found: {id}"}, 404, default_headers

        user.disabled_at = None
        user.disabled_by = None
        user.save()
        _record(AuditEvent.Action.UserEnable, user)
        return json.loads(json_util.dumps(user.to_dict())), 200, default_headers


class AdminUserPromote(Resource):
    """Grants the system-level admin role. Takes effect on the user's very
    next request -- require_admin reads the role from the stored User each
    time (via both the session and API-token paths), not from the session."""

    @require_admin
    def post(self, id: str):
        user = User.get(id)
        if user is None:
            return {"message": f"User not found: {id}"}, 404, default_headers

        user.role = User.Role.Admin
        user.save()
        _record(AuditEvent.Action.UserPromote, user)
        return json.loads(json_util.dumps(user.to_dict())), 200, default_headers


class AdminUserDemote(Resource):
    """Returns an admin to the normal user role. Like disable, an admin can't
    target their own account -- with that rule, the caller always remains an
    admin, so the system can never be left with none."""

    @require_admin
    def post(self, id: str):
        if id == g.current_user["user_id"]:
            return (
                {"message": "You cannot remove your own admin role"},
                403,
                default_headers,
            )

        user = User.get(id)
        if user is None:
            return {"message": f"User not found: {id}"}, 404, default_headers

        user.role = User.Role.User
        user.save()
        _record(AuditEvent.Action.UserDemote, user)
        return json.loads(json_util.dumps(user.to_dict())), 200, default_headers


class AdminAuditEvents(Resource):
    """Who disabled, enabled, promoted, or demoted an account, and who
    revoked which API tokens. Newest first.

    Query params (all optional): userId (as either actor or target),
    action (e.g. "token.revoke"), limit (default 100, max 1000).
    """

    @require_admin
    def get(self):
        try:
            limit = int(request.args.get("limit", 100))
        except ValueError:
            return {"message": "limit must be an integer"}, 400, default_headers
        if not 1 <= limit <= 1000:
            return {"message": "limit must be 1-1000"}, 400, default_headers

        action = request.args.get("action")
        if action is not None and action not in AuditEvent.Action:
            return {"message": f"Unknown action: {action}"}, 400, default_headers

        events = AuditEvent.find(
            user_id=request.args.get("userId"), action=action, limit=limit
        )
        return (
            [{**e.to_dict(), "at": e.at.isoformat() if e.at else None} for e in events],
            200,
            default_headers,
        )
