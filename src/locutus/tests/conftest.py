import logging
import os

import pytest
from rich.console import Console

from locutus.storage.mongo import filter_uri


def pytest_sessionstart(session):
    uri = os.environ.get("MONGO_URI", "")

    # Logic to check if we are in the safe 'test' database
    if "test" not in uri.split("/")[-1].split("?"):
        console = Console()

        # 1. Print the styled message directly to the terminal
        console.print(
            f"\n[bold red]CRITICAL CONFIG ERROR:[/bold red] "
            f"MONGO_URI points to [yellow]{filter_uri(uri)}[/yellow].\n"
            f"Aborting suite to protect non-test data."
        )

        # 2. Hard exit with a plain string for the internal logs
        pytest.exit(reason="Database safety check failed.", returncode=1)
