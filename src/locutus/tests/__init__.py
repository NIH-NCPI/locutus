import pytest

from locutus.app import create_app


@pytest.fixture
def client():
    app = create_app()
    app.config["TESTING"] = True

    with app.app_context(), app.test_client() as client:
        yield client
