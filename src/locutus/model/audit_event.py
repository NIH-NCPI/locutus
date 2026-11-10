"""
The AuditEvent model records who did what to an account or its
credentials: admin user changes (disable/enable/promote/demote) and every
API token revocation. Append-only -- nothing here updates or deletes an
event once written. Like User/ApiToken, it deliberately doesn't derive from
Serializable.
"""

from collections.abc import Iterator
from datetime import UTC, datetime
from enum import StrEnum
from itertools import islice
from typing import Any, cast

import locutus


class AuditEvent:
    class Action(StrEnum):
        UserDisable = "user.disable"
        UserEnable = "user.enable"
        UserPromote = "user.promote"
        UserDemote = "user.demote"
        # One token, by id -- the owner's own revoke or an admin's.
        TokenRevoke = "token.revoke"
        # Every active token a user has, in one admin request.
        TokenRevokeAll = "token.revoke_all"
        # A raw token value someone submitted, e.g. one found in a log.
        TokenRevokeByValue = "token.revoke_by_value"

    def __init__(
        self,
        action: Action,
        actor_id: str,
        target_user_id: str,
        id: str | None = None,
        at: datetime | None = None,
        target_token_ids: list[str] | None = None,
        reason: str | None = None,
    ):
        self.id = id
        self.at = at if at is not None else datetime.now(UTC)
        self.action = action
        self.actor_id = actor_id
        self.target_user_id = target_user_id
        self.target_token_ids = target_token_ids if target_token_ids else []
        self.reason = reason

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "at": self.at,
            "action": self.action,
            "actorId": self.actor_id,
            "targetUserId": self.target_user_id,
            "targetTokenIds": self.target_token_ids,
            "reason": self.reason,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AuditEvent":
        return cls(
            id=data.get("id"),
            at=data.get("at"),
            action=data["action"],
            actor_id=data["actorId"],
            target_user_id=data["targetUserId"],
            target_token_ids=data.get("targetTokenIds"),
            reason=data.get("reason"),
        )

    @classmethod
    def record(
        cls,
        action: Action,
        actor_id: str,
        target_user_id: str,
        target_token_ids: list[str] | None = None,
        reason: str | None = None,
    ) -> "AuditEvent":
        event = cls(
            action=action,
            actor_id=actor_id,
            target_user_id=target_user_id,
            target_token_ids=target_token_ids,
            reason=reason,
        )
        doc = event.to_dict()
        del doc["id"]  # let storage assign it
        event.id = str(
            locutus.persistence().collection("AuditEvent").document().set(doc)
        )
        return event

    @classmethod
    def find(
        cls,
        user_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> "list[AuditEvent]":
        """Newest first. user_id matches events where that user is either
        the actor or the target."""
        query: dict[str, Any] = {}
        if user_id is not None:
            query["$or"] = [{"actorId": user_id}, {"targetUserId": user_id}]
        if action is not None:
            query["action"] = action
        # return_instance=False makes find() yield plain dicts, but its
        # signature doesn't say so -- same cast as list_api_tokens.
        docs = cast(
            "Iterator[dict[str, Any]]",
            locutus.persistence()
            .collection("AuditEvent")
            .find(query, sorting=[("at", -1)], return_instance=False),
        )
        return [cls.from_dict(doc) for doc in islice(docs, limit)]
