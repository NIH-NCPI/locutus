"""
API token self-service (Auth Requirements spec, M9), plus the admin side
of token incident response. Creation is interactive-only so a compromised
token can't mint another token to extend its own access; listing and
revocation work from either credential path.

Revoking never deletes a token -- it's marked revoked (see ApiToken) and
recorded as an AuditEvent, so an admin can still see when it was last used.
"""

from datetime import datetime

from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import require_admin, require_auth
from locutus.model.api_token import ApiToken
from locutus.model.user import User


def _isoformat(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _summarize(token: ApiToken) -> dict:
    return {
        "tokenId": token.id,
        "name": token.name,
        "createdAt": _isoformat(token.created_at),
        "lastUsedAt": _isoformat(token.last_used_at),
        "expiresAt": _isoformat(token.expires_at),
    }


def _admin_summarize(token: ApiToken) -> dict:
    """_summarize plus ownership and revocation details -- still never the
    hash or the raw token."""
    return {
        **_summarize(token),
        "userId": token.user_id,
        "revokedAt": _isoformat(token.revoked_at),
        "revokedBy": token.revoked_by,
        "revokeReason": token.revoke_reason,
    }


def _reason() -> str | None:
    body = request.get_json(silent=True) or {}
    return body.get("reason") or None


class ApiTokens(Resource):
    @require_auth(interactive_only=True)
    def post(self):
        """Creates a new token for the current user.

        Body: { "name": str, "expiresAt"?: ISO 8601 timestamp }
        Returns: { "tokenId": str, "token": "lct_..." } -- the only time
        the plaintext token is ever available.
        """
        body = request.get_json(silent=True) or {}
        name = body.get("name")
        if not name:
            return (
                {"message": "This action requires the parameter: 'name'"},
                400,
                default_headers,
            )

        expires_at = None
        raw_expires_at = body.get("expiresAt")
        if raw_expires_at:
            try:
                expires_at = datetime.fromisoformat(raw_expires_at)
            except ValueError:
                return (
                    {"message": "expiresAt must be an ISO 8601 timestamp"},
                    400,
                    default_headers,
                )

        token, raw = ApiToken.create(
            user_id=g.current_user["user_id"], name=name, expires_at=expires_at
        )
        return {"tokenId": token.id, "token": raw}, 200, default_headers

    @require_auth
    def get(self):
        """Lists the current user's own tokens -- names and metadata only,
        never the hash or the raw token."""
        tokens = ApiToken.list_for_user(g.current_user["user_id"])
        return [_summarize(t) for t in tokens], 200, default_headers


class ApiTokenItem(Resource):
    @require_auth
    def delete(self, id):
        """Owner revokes their own token."""
        if not ApiToken.revoke(id, g.current_user["user_id"]):
            return {"message": "Token not found"}, 404, default_headers
        return {"message": "Token revoked"}, 200, default_headers


class AdminApiTokenItem(Resource):
    @require_admin
    def delete(self, id):
        """Admin revokes any user's token, e.g. for offboarding.

        Body (optional): { "reason": str }
        """
        if not ApiToken.admin_revoke(id, g.current_user["user_id"], _reason()):
            return {"message": "Token not found"}, 404, default_headers
        return {"message": "Token revoked"}, 200, default_headers


class AdminUserApiTokens(Resource):
    @require_admin
    def get(self, id: str):
        """Lists every token a user has, revoked ones included, so an admin
        can find the one to revoke and see when it was last used."""
        if User.get(id) is None:
            return {"message": f"User not found: {id}"}, 404, default_headers
        tokens = ApiToken.list_for_user(id, include_revoked=True)
        return [_admin_summarize(t) for t in tokens], 200, default_headers

    @require_admin
    def delete(self, id: str):
        """Revokes all of a user's active tokens -- lighter than disabling
        the account, which also ends their sessions and blocks login.

        Body (optional): { "reason": str }
        Returns: { "revoked": int, "tokenIds": [str] }
        """
        if User.get(id) is None:
            return {"message": f"User not found: {id}"}, 404, default_headers
        revoked = ApiToken.admin_revoke_all(id, g.current_user["user_id"], _reason())
        return {"revoked": len(revoked), "tokenIds": revoked}, 200, default_headers


class ApiTokenRevokeByValue(Resource):
    @require_auth
    def post(self):
        """Revokes a token by its raw value, whoever owns it -- for any
        signed-in user who finds a token somewhere it shouldn't be (a log,
        a commit, a chat). Holding the value is already enough to use or
        revoke it, so no further check is needed.

        Body: { "token": "lct_...", "reason"?: str }
        Always the same 200 whether or not anything was revoked, so this
        can't be used to test whether a string is a live token.
        """
        body = request.get_json(silent=True) or {}
        raw = body.get("token")
        if not isinstance(raw, str) or not raw:
            return (
                {"message": "This action requires the parameter: 'token'"},
                400,
                default_headers,
            )
        ApiToken.revoke_by_value(raw, g.current_user["user_id"], _reason())
        return (
            {"message": "If that token was active, it has been revoked"},
            200,
            default_headers,
        )
