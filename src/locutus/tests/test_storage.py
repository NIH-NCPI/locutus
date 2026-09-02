import locutus


def _clear(collection_name):
    for doc in locutus.persistence().collection(collection_name).stream():
        locutus.persistence().collection(collection_name).document(doc.id).delete()


def test_get_user_found_and_not_found():
    _clear("User")
    doc_id = str(
        locutus.persistence()
        .collection("User")
        .document()
        .set({"email": "a@example.com", "institutionIds": ["vumc"], "role": "user"})
    )

    try:
        user = locutus.persistence().get_user(doc_id)
        assert user is not None
        assert user["email"] == "a@example.com"
        assert user["institutionIds"] == ["vumc"]

        assert locutus.persistence().get_user("does-not-exist") is None
    finally:
        _clear("User")


def test_get_resource_found_and_not_found():
    _clear("Study")
    doc_id = str(
        locutus.persistence()
        .collection("Study")
        .document()
        .set({"name": "storage-test-study", "ownerId": "u1", "visibility": "public"})
    )

    try:
        resource = locutus.persistence().get_resource("Study", doc_id)
        assert resource is not None
        assert resource["ownerId"] == "u1"

        assert locutus.persistence().get_resource("Study", "does-not-exist") is None
    finally:
        _clear("Study")


def test_api_token_lifecycle():
    _clear("ApiToken")

    try:
        token_id = str(
            locutus.persistence().create_api_token(
                {
                    "userId": "u1",
                    "tokenHash": "hash-of-secret",
                    "name": "laptop",
                    "createdAt": "2026-09-01",
                    "lastUsedAt": None,
                    "expiresAt": None,
                }
            )
        )

        fetched = locutus.persistence().get_api_token("hash-of-secret")
        assert fetched is not None
        assert fetched["userId"] == "u1"

        assert locutus.persistence().get_api_token("no-such-hash") is None

        listed = locutus.persistence().list_api_tokens("u1")
        assert len(listed) == 1
        assert listed[0]["name"] == "laptop"
        assert "tokenHash" not in listed[0]

        assert locutus.persistence().list_api_tokens("someone-else") == []

        # Wrong owner can't delete.
        assert locutus.persistence().delete_api_token(token_id, "someone-else") is False
        assert len(locutus.persistence().list_api_tokens("u1")) == 1

        # Missing token id is a clean False, not an error.
        assert locutus.persistence().delete_api_token("not-a-real-id", "u1") is False

        # Owner can delete.
        assert locutus.persistence().delete_api_token(token_id, "u1") is True
        assert locutus.persistence().list_api_tokens("u1") == []
    finally:
        _clear("ApiToken")


def test_update_token_last_used_actually_persists():
    """Regression coverage for the DocumentReference.update() bug this
    method depends on -- it queried _id as a bare string instead of an
    ObjectId, so the update silently matched nothing."""
    _clear("ApiToken")

    try:
        token_id = str(
            locutus.persistence().create_api_token(
                {
                    "userId": "u1",
                    "tokenHash": "hash-of-secret",
                    "name": "laptop",
                    "createdAt": "2026-09-01",
                    "lastUsedAt": None,
                    "expiresAt": None,
                }
            )
        )

        locutus.persistence().update_token_last_used(token_id)

        fetched = locutus.persistence().get_api_token("hash-of-secret")
        assert fetched is not None
        assert fetched["lastUsedAt"] is not None
    finally:
        _clear("ApiToken")
