"""
The Institution model backs Locutus authorization (see the Auth Requirements
spec, M3). Like User, it deliberately does not derive from Serializable --
it isn't part of the owned-resource tree and has no ownerId/access fields
of its own.
"""

import locutus


class Institution:
    def __init__(
        self, id=None, name: str | None = None, member_ids=None, allowed_emails=None
    ):
        self.id = id
        self.name = name
        self.member_ids = member_ids if member_ids is not None else []
        self.allowed_emails = allowed_emails if allowed_emails is not None else []

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "memberIds": self.member_ids,
            "allowedEmails": self.allowed_emails,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            name=data.get("name"),
            member_ids=data.get("memberIds", []),
            allowed_emails=data.get("allowedEmails", []),
        )

    def save(self):
        self.id = str(
            locutus.persistence()
            .collection("Institution")
            .document(self.id)
            .set(self.to_dict())
        )
        return self

    def delete(self):
        locutus.persistence().collection("Institution").document(self.id).delete()

    @classmethod
    def get(cls, institution_id):
        data = locutus.persistence().get_resource("Institution", institution_id)
        return cls.from_dict(data) if data is not None else None

    @classmethod
    def all(cls):
        return [
            cls.from_dict(doc.to_dict())
            for doc in locutus.persistence().collection("Institution").stream()
        ]

    def allows_email(self, email):
        return email in self.allowed_emails

    def add_member(self, user_id):
        if user_id not in self.member_ids:
            self.member_ids.append(user_id)

    def remove_member(self, user_id):
        if user_id in self.member_ids:
            self.member_ids.remove(user_id)
