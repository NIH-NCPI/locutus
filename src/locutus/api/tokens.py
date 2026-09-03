"""
API token self-service (Auth Requirements spec, M9). Creation is
interactive-only so a compromised token can't mint another token to
extend its own access; listing and self-revocation work from either
credential path.
"""

from datetime import datetime

from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import require_admin, require_auth
from locutus.model.api_token import ApiToken


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
        if not ApiToken.delete(id, g.current_user["user_id"]):
            return {"message": "Token not found"}, 404, default_headers
        return {"message": "Token revoked"}, 200, default_headers


class AdminApiTokenItem(Resource):
    @require_admin
    def delete(self, id):
        """Admin revokes any user's token, e.g. for offboarding."""
        if not ApiToken.admin_delete(id):
            return {"message": "Token not found"}, 404, default_headers
        return {"message": "Token revoked"}, 200, default_headers
