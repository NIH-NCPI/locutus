import pytest

from locutus.app import create_app
from locutus.model.api_token import ApiToken
from locutus.model.user import User


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context(), app.test_client() as client:
        yield client


class _Owner:
    """Creates a real User and logs the shared `client` fixture in as
    them, for the duration of one test. Shared across API test files that
    need a real authenticated caller (table/study/terminology/... tests)."""

    def __init__(self, client, email="test-owner@example.com"):
        self.client = client
        self.user = User(email=email).save()
        assert self.user.id is not None
        self._token_ids: list[str] = []
        with client.session_transaction() as sess:
            sess["user_id"] = self.user.id

    def own(self, resource):
        """Makes the logged-in user the owner of an existing fixture
        resource (basic_table, sample_terminology, ...) and re-saves it."""
        resource.owner_id = self.user.id
        resource.save()
        return resource

    def token_headers(self):
        """Path B (API token) rather than a session -- deliberately drops
        the session cookie __init__ set, so the *old* editor concept (a
        separate, pre-auth audit-trail field, see get_editor()) can't fall
        back to it. Used for the "missing editor" tests below: under
        Path A, a real login session now always doubles as a valid editor
        fallback, which would make "missing editor" unreachable and defeat
        the point of those tests. The test client's cookie jar persists
        across requests like a real browser's, so the session cookie would
        otherwise still ride along even with an Authorization header set."""
        assert self.user.id is not None
        token, raw = ApiToken.create(user_id=self.user.id, name="test-token")
        assert token.id is not None
        self._token_ids.append(token.id)
        self.client.delete_cookie("session")
        return {"Authorization": f"Bearer {raw}"}

    def cleanup(self):
        assert self.user.id is not None
        for token_id in self._token_ids:
            ApiToken.delete(token_id, self.user.id)
        self.user.delete()
