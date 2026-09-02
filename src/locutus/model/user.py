"""
The User model backs Locutus authorization (see the Auth Requirements spec,
M2). It deliberately does not derive from Serializable -- identity isn't
part of the resource tree that Serializable's factory/registration machinery
exists for, and giving it its own small structure keeps that machinery from
having to account for a type with no owner/access fields of its own.
"""

from enum import StrEnum
from typing import Any

import locutus


class User:
    class Role(StrEnum):
        """System-level role -- distinct from the resource-level editor/
        viewer roles on individual work products (see Visibility)."""

        User = "user"
        Admin = "admin"

    def __init__(
        self,
        id: str | None = None,
        email: str | None = None,
        display_name: str | None = None,
        institution_ids: list[str] | None = None,
        role: Role = Role.User,
    ):
        self.id = id
        self.email = email
        self.display_name = display_name
        self.institution_ids = institution_ids if institution_ids is not None else []
        self.role = role

    def is_admin(self) -> bool:
        return self.role == User.Role.Admin

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "email": self.email,
            "displayName": self.display_name,
            "institutionIds": self.institution_ids,
            "role": self.role,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "User":
        return cls(
            id=data.get("id"),
            email=data.get("email"),
            display_name=data.get("displayName"),
            institution_ids=data.get("institutionIds", []),
            role=data.get("role", User.Role.User),
        )

    def save(self) -> "User":
        self.id = str(
            locutus.persistence()
            .collection("User")
            .document(self.id)
            .set(self.to_dict())
        )
        return self

    def delete(self) -> None:
        locutus.persistence().collection("User").document(self.id).delete()

    @classmethod
    def get(cls, user_id: str) -> "User | None":
        data = locutus.persistence().get_user(user_id)
        return cls.from_dict(data) if data is not None else None

    @classmethod
    def find_by_email(cls, email: str) -> "User | None":
        match = locutus.persistence().collection("User").find_one({"email": email})
        return cls.from_dict(match) if match is not None else None
