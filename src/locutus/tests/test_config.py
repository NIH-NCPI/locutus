import os

import pytest


@pytest.mark.run(order=1)
def test_os_env():
    uri = os.environ.get("MONGO_URI", "")
    # Extract DB name: gets "test" from "mongodb://localhost:27017/test?authSource=admin"
    db_name = uri.split("/")[-1].split("?")[0]

    if db_name != "test":
        pytest.exit(
            f"AssertionError: CRITICAL: Wrong database! MONGO_URI is pointing to: {uri}",
            returncode=1,
        )
