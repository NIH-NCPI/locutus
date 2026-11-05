"""
The ApiToken model backs CLI/scripted access to Locutus (Auth Requirements
spec, M8/M9) -- Path B of the two credential paths locutus.auth's
require_auth resolves. Like User/Institution, it deliberately doesn't
derive from Serializable.
"""

import secrets
from datetime import UTC, datetime
from typing import Any

import locutus
from locutus.auth import TOKEN_PREFIX, hash_token
from locutus.model.audit_event import AuditEvent


class ApiToken:
    def __init__(
        self,
        id: str | None = None,
        user_id: str | None = None,
        name: str | None = None,
        created_at: datetime | None = None,
        last_used_at: datetime | None = None,
        expires_at: datetime | None = None,
        revoked_at: datetime | None = None,
        revoked_by: str | None = None,
        revoke_reason: str | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.created_at = created_at
        self.last_used_at = last_used_at
        self.expires_at = expires_at
        # Revocation keeps the document rather than deleting it, so an
        # admin can still see when a suspect token was last used. None
        # means active; see _resolve_via_token in locutus/auth.py.
        self.revoked_at = revoked_at
        self.revoked_by = revoked_by
        self.revoke_reason = revoke_reason

    def to_dict(self) -> dict[str, Any]:
        # Deliberately never includes the hash -- from_dict() below never
        # reads it back out of a stored doc either, so there's no path for
        # it to leak back through this class once it's written at create().
        return {
            "id": self.id,
            "userId": self.user_id,
            "name": self.name,
            "createdAt": self.created_at,
            "lastUsedAt": self.last_used_at,
            "expiresAt": self.expires_at,
            "revokedAt": self.revoked_at,
            "revokedBy": self.revoked_by,
            "revokeReason": self.revoke_reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ApiToken":
        return cls(
            id=data.get("id"),
            user_id=data.get("userId"),
            name=data.get("name"),
            created_at=data.get("createdAt"),
            last_used_at=data.get("lastUsedAt"),
            expires_at=data.get("expiresAt"),
            revoked_at=data.get("revokedAt"),
            revoked_by=data.get("revokedBy"),
            revoke_reason=data.get("revokeReason"),
        )

    @classmethod
    def create(
        cls, user_id: str, name: str, expires_at: datetime | None = None
    ) -> tuple["ApiToken", str]:
        """Generates a new token, stores only its hash, and returns
        (model, plaintext). The plaintext is never persisted -- this return
        value is the only time it's ever available, matching GitHub PATs."""
        raw = TOKEN_PREFIX + secrets.token_hex(16)
        token_doc = {
            "userId": user_id,
            "tokenHash": hash_token(raw),
            "name": name,
            "createdAt": datetime.now(UTC),
            "lastUsedAt": None,
            "expiresAt": expires_at,
            "revokedAt": None,
            "revokedBy": None,
            "revokeReason": None,
        }
        token_doc["id"] = str(locutus.persistence().create_api_token(token_doc))
        return cls.from_dict(token_doc), raw

    @classmethod
    def get(cls, token_id: str) -> "ApiToken | None":
        doc = locutus.persistence().collection("ApiToken").document(token_id).get()
        return cls.from_dict(doc.to_dict()) if doc.exists else None

    @classmethod
    def list_for_user(
        cls, user_id: str, include_revoked: bool = False
    ) -> list["ApiToken"]:
        return [
            cls.from_dict(doc)
            for doc in locutus.persistence().list_api_tokens(user_id, include_revoked)
        ]

    @classmethod
    def revoke(cls, token_id: str, user_id: str) -> bool:
        """Owner revokes their own token. Returns False if it doesn't
        exist, belongs to someone else, or is already revoked."""
        if not locutus.persistence().revoke_api_token(token_id, user_id, user_id):
            return False
        AuditEvent.record(
            AuditEvent.Action.TokenRevoke,
            actor_id=user_id,
            target_user_id=user_id,
            target_token_ids=[token_id],
        )
        return True

    @classmethod
    def admin_revoke(
        cls, token_id: str, actor_id: str, reason: str | None = None
    ) -> bool:
        """Revokes any token regardless of owner, e.g. for admin
        offboarding. Resolves the real owner first and reuses the same
        ownership-checked storage call rather than adding a second,
        unchecked revoke path to the storage layer."""
        token = cls.get(token_id)
        if token is None or token.user_id is None:
            return False
        if not locutus.persistence().revoke_api_token(
            token_id, token.user_id, actor_id, reason
        ):
            return False
        AuditEvent.record(
            AuditEvent.Action.TokenRevoke,
            actor_id=actor_id,
            target_user_id=token.user_id,
            target_token_ids=[token_id],
            reason=reason,
        )
        return True

    @classmethod
    def admin_revoke_all(
        cls, user_id: str, actor_id: str, reason: str | None = None
    ) -> list[str]:
        """Revokes every active token user_id has, leaving the account and
        its sessions alone. Returns the ids actually revoked."""
        revoked = [
            token.id
            for token in cls.list_for_user(user_id)
            if token.id is not None
            and locutus.persistence().revoke_api_token(
                token.id, user_id, actor_id, reason
            )
        ]
        AuditEvent.record(
            AuditEvent.Action.TokenRevokeAll,
            actor_id=actor_id,
            target_user_id=user_id,
            target_token_ids=revoked,
            reason=reason,
        )
        return revoked

    @classmethod
    def revoke_by_value(
        cls, raw: str, actor_id: str, reason: str | None = None
    ) -> bool:
        """Revokes the token whose plaintext is raw, whoever owns it -- for
        a token found somewhere it shouldn't be. Returns whether an active
        token was revoked; callers shouldn't pass that back to the caller,
        or this would double as a way to test whether a string is a live
        token."""
        doc = locutus.persistence().get_api_token(hash_token(raw))
        if doc is None:
            return False
        token_id, user_id = doc["id"], doc["userId"]
        if not locutus.persistence().revoke_api_token(
            token_id, user_id, actor_id, reason
        ):
            return False
        AuditEvent.record(
            AuditEvent.Action.TokenRevokeByValue,
            actor_id=actor_id,
            target_user_id=user_id,
            target_token_ids=[token_id],
            reason=reason,
        )
        return True
