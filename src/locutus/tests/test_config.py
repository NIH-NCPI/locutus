import pytest
import os

@pytest.mark.first
def test_os_env():
    assert os.environ.get('MONGO_URI').split("/")[-1].split("?")[0] == "test"
