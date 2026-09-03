import pytest

from locutus.model.coding import Coding
from locutus.model.terminology import Terminology
from locutus.model.user_input import MappingConversation, MappingVote

from . import _Owner, client
from .test_table import basic_table
from .test_terminology import sample_terminology


def _cleanup_vote(terminology_id, code, mapped_code):
    # Not strictly required since issues/013 was fixed (Terminology.delete()
    # now handles a single leftover MappingVote/MappingConversation cleanly),
    # but keeping fixture teardown starting from zero leftover votes/
    # conversations avoids depending on that cleanup path in unrelated tests.
    vote = MappingVote.get(
        terminology_id=terminology_id,
        source_code=code,
        mapped_code=mapped_code,
        return_instance=True,
    )
    if vote is not None:
        vote.delete(hard_delete=True)


def _cleanup_conversation(terminology_id, code, mapped_code):
    conversation = MappingConversation.get(
        terminology_id=terminology_id,
        source_code=code,
        mapped_code=mapped_code,
        return_instance=True,
    )
    if conversation is not None:
        conversation.delete(hard_delete=True)


def test_terminology_user_input_requires_auth(client, sample_terminology):
    response = client.get(
        f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes"
    )
    assert response.status_code == 401


def test_terminology_user_input_get_no_data(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        response = client.get(
            f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes"
        )
        assert response.status_code == 200
        assert response.json["message"] == "No user input for this mapping."
    finally:
        test_owner.cleanup()


def test_terminology_user_input_put_vote_and_get(client, sample_terminology):
    # Uses token_headers() (Path B) rather than the default session -- with
    # an active session, SessionManager.create_user_id() always prefers
    # session["user_id"] over the body's explicit "editor" value, which
    # would key the vote by the owner's user id instead of "unit-test".
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "up"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json["mapping_votes"]["unit-test"]["vote"] == "up"

        response = client.get(
            f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes",
            headers=headers,
        )
        assert response.json["mapping_votes"]["unit-test"]["vote"] == "up"

        _cleanup_vote(sample_terminology.id, "C1", "M1")
    finally:
        test_owner.cleanup()


def test_terminology_user_input_put_conversation_and_get(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.put(
            f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_conversations",
            json={"editor": "unit-test", "note": "a comment"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 200
        assert response.json["mapping_conversations"][0]["note"] == "a comment"

        _cleanup_conversation(sample_terminology.id, "C1", "M1")
    finally:
        test_owner.cleanup()


def test_terminology_user_input_requires_write_access(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        response = client.put(
            f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "up"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_terminology_delete_with_single_vote_and_conversation(client):
    """Pins the issues/013 fix: Terminology.delete() used to crash with
    TypeError whenever a terminology had exactly one MappingVote or
    MappingConversation, since UserInput.get() unwraps a single-item result
    to a bare instance instead of a one-item list."""
    test_owner = _Owner(client)
    try:
        terminology = Terminology(
            id="delete-with-single-vote-test",
            name="Delete With Single Vote Test",
            url="http://ftd.unit.tests/delete_with_single_vote",
            description="Terminology for issues/013 regression coverage",
            codes=[
                Coding(
                    terminology_id="delete-with-single-vote-test",
                    code="C1",
                    display="Code One",
                    system="http://example.com/ont1",
                    description="Description for C1",
                )
            ],
        )
        test_owner.own(terminology)

        vote_response = client.put(
            f"/api/Terminology/{terminology.id}/user_input/C1/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "up"},
            headers={"Content-Type": "application/json"},
        )
        assert vote_response.status_code == 200

        conversation_response = client.put(
            f"/api/Terminology/{terminology.id}/user_input/C1/mapping/M1/mapping_conversations",
            json={"editor": "unit-test", "note": "a comment"},
            headers={"Content-Type": "application/json"},
        )
        assert conversation_response.status_code == 200

        assert (
            type(
                MappingVote.get(
                    terminology_id=terminology.id,
                    source_code="C1",
                    mapped_code="M1",
                    return_instance=True,
                )
            )
            is MappingVote
        )
        assert (
            type(
                MappingConversation.get(
                    terminology_id=terminology.id,
                    source_code="C1",
                    mapped_code="M1",
                    return_instance=True,
                )
            )
            is MappingConversation
        )

        # This used to raise TypeError: 'MappingVote' object is not iterable.
        terminology.delete(hard_delete=True)

        assert Terminology.get(terminology.id) is None
        assert (
            MappingVote.get(
                terminology_id=terminology.id,
                source_code="C1",
                mapped_code="M1",
                return_instance=True,
            )
            == []
        )
        assert (
            MappingConversation.get(
                terminology_id=terminology.id,
                source_code="C1",
                mapped_code="M1",
                return_instance=True,
            )
            == []
        )
    finally:
        test_owner.cleanup()


def test_terminology_user_input_put_missing_editor_raises(client, sample_terminology):
    # Documents current behavior: TerminologyUserInput.put raises
    # LackingUserID before the try/except block that would otherwise turn it
    # into a clean 400, so it propagates as an unhandled exception instead.
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        with pytest.raises(Exception, match="requires an editor or session"):
            client.put(
                f"/api/Terminology/{sample_terminology.id}/user_input/C1/mapping/M1/mapping_votes",
                json={"vote": "up"},
                headers=headers,
            )
    finally:
        test_owner.cleanup()


def test_terminology_user_input_put_code_not_present(client, sample_terminology):
    test_owner = _Owner(client)
    try:
        test_owner.own(sample_terminology)
        response = client.put(
            f"/api/Terminology/{sample_terminology.id}/user_input/does-not-exist/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "up"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_terminology_user_input_get_missing_terminology_returns_404(client):
    # require_read_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get(
            "/api/Terminology/not-there/user_input/C1/mapping/M1/mapping_votes"
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_user_input_requires_auth(client, sample_terminology, basic_table):
    response = client.get(
        f"/api/Table/{basic_table.id}/user_input/string_var/mapping/M1/mapping_votes"
    )
    assert response.status_code == 401


def test_table_user_input_get_no_data(client, sample_terminology, basic_table):
    test_owner = _Owner(client)
    try:
        response = client.get(
            f"/api/Table/{basic_table.id}/user_input/string_var/mapping/M1/mapping_votes"
        )
        assert response.status_code == 200
        assert response.json["message"] == "No user input for this mapping."
    finally:
        test_owner.cleanup()


def test_table_user_input_put_vote_and_get(client, sample_terminology, basic_table):
    # Uses token_headers() (Path B) -- see the comment in
    # test_terminology_user_input_put_vote_and_get above.
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        response = client.put(
            f"/api/Table/{basic_table.id}/user_input/string_var/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "down"},
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json["mapping_votes"]["unit-test"]["vote"] == "down"

        table = basic_table
        terminology_id = table.terminology.reference_id()
        _cleanup_vote(terminology_id, "string_var", "M1")
    finally:
        test_owner.cleanup()


def test_table_user_input_requires_write_access(
    client, sample_terminology, basic_table
):
    test_owner = _Owner(client)
    try:
        response = client.put(
            f"/api/Table/{basic_table.id}/user_input/string_var/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "down"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 403
    finally:
        test_owner.cleanup()


def test_table_user_input_put_missing_editor_raises(
    client, sample_terminology, basic_table
):
    # Same shape as the Terminology-level bug: the LackingUserID raise sits
    # before any try/except, so it isn't turned into a clean 400.
    test_owner = _Owner(client)
    try:
        test_owner.own(basic_table)
        headers = test_owner.token_headers()
        headers["Content-Type"] = "application/json"
        with pytest.raises(Exception, match="requires an editor or session"):
            client.put(
                f"/api/Table/{basic_table.id}/user_input/string_var/mapping/M1/mapping_votes",
                json={"vote": "down"},
                headers=headers,
            )
    finally:
        test_owner.cleanup()


def test_table_user_input_get_missing_table_returns_404(client):
    # require_read_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.get(
            "/api/Table/not-there/user_input/C1/mapping/M1/mapping_votes"
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()


def test_table_user_input_put_missing_table_returns_404(client):
    # require_write_access now 404s before the handler (which never itself
    # checked for None) can even run.
    test_owner = _Owner(client)
    try:
        response = client.put(
            "/api/Table/not-there/user_input/C1/mapping/M1/mapping_votes",
            json={"editor": "unit-test", "vote": "up"},
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code == 404
    finally:
        test_owner.cleanup()
