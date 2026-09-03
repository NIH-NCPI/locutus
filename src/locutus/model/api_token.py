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


class ApiToken:
    def __init__(
        self,
        id: str | None = None,
        user_id: str | None = None,
        name: str | None = None,
        created_at: datetime | None = None,
        last_used_at: datetime | None = None,
        expires_at: datetime | None = None,
    ):
        self.id = id
        self.user_id = user_id
        self.name = name
        self.created_at = created_at
        self.last_used_at = last_used_at
        self.expires_at = expires_at

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
        }
        token_doc["id"] = str(locutus.persistence().create_api_token(token_doc))
        return cls.from_dict(token_doc), raw

    @classmethod
    def get(cls, token_id: str) -> "ApiToken | None":
        doc = locutus.persistence().collection("ApiToken").document(token_id).get()
        return cls.from_dict(doc.to_dict()) if doc.exists else None

    @classmethod
    def list_for_user(cls, user_id: str) -> list["ApiToken"]:
        return [
            cls.from_dict(doc) for doc in locutus.persistence().list_api_tokens(user_id)
        ]

    @classmethod
    def delete(cls, token_id: str, user_id: str) -> bool:
        """Deletes a token if it belongs to user_id. Returns False if it
        doesn't exist or belongs to someone else."""
        return locutus.persistence().delete_api_token(token_id, user_id)

    @classmethod
    def admin_delete(cls, token_id: str) -> bool:
        """Deletes any token regardless of owner, e.g. for admin
        offboarding. Resolves the real owner first and reuses the same
        ownership-checked storage call rather than adding a second,
        unchecked delete path to the storage layer."""
        token = cls.get(token_id)
        if token is None or token.user_id is None:
            return False
        return locutus.persistence().delete_api_token(token_id, token.user_id)
