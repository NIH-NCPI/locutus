# Locutus

[![Tests](https://github.com/NIH-NCPI/locutus/actions/workflows/test.yml/badge.svg)](https://github.com/NIH-NCPI/locutus/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-blue.svg)](pyproject.toml)

Locutus is the backend for a web-based terminology mapping tool. It gives researchers a collaborative environment to harmonize dataset terms — the column values in a data dictionary — against public ontologies such as MeSH and HPO, so that datasets from different studies can be compared and combined using shared vocabulary.

It's a REST API (Flask + MongoDB) that manages terminologies, tables/data dictionaries, code mappings, provenance history, and per-user voting/discussion on proposed mappings. It's the API layer for the companion frontend, [Map Dragon](https://github.com/NIH-NCPI/map-dragon).

## Architecture

- **Flask** app exposing a resource-oriented REST API (`flask-restful`)
- **MongoDB** for storage
- Session-based auth for interactive editing, with editor/service-account fallback for scripted access
- Provenance tracking on every change to a terminology, table, or mapping
- Deployed as a container (see `Dockerfile` / `cloudbuild.yaml`) to Google Cloud Run

## Getting started

### With Docker Compose

```bash
docker compose up --build
```

This builds the image and serves the API on `http://localhost:5000`.

### Local install

Requires Python 3.13+ and a running MongoDB instance.

```bash
pip install ".[dev]"
```

For a cloud deployment, install with the `cloud` extra instead (adds structured JSON logging):

```bash
pip install ".[cloud]"
```

By default the log level is `WARNING`; set `LOCUTUS_LOGLEVEL` to any standard Python log level (`INFO`, `DEBUG`, etc.) to change it.

## Running tests

Unit tests use PyTest and expect a reachable MongoDB instance.

```bash
LOCUTUS_DB_TYPE=mongodb LOCUTUS_LOGLEVEL=DEBUG pytest
```

Run a single test file:

```bash
pytest src/locutus/tests/test_terminology.py
```

Stop on the first failure:

```bash
pytest -x src/locutus/tests/test_terminology.py
```

## Writing tests

All tests share one MongoDB database, and pytest runs the files in alphabetical
order, so a test that leaves documents behind can break a later test in another
file. A few conventions keep the suite independent of that order.

**Where tests go.** Tests that call the HTTP API live in `api_<area>_test.py`
and use the `client` fixture. Tests of a model or helper on its own live in
`test_<module>.py` and don't log in. For example, tests of
`/api/admin/institutions` go in `api_admin_test.py`, not `test_institution.py`.

**Logging in leaves a session behind.** Sessions are stored in the `sessions`
collection (see `sessions.py`). Every `_Owner(client)` or
`client.session_transaction()` writes a session document there, and
`_Owner.cleanup()` deletes the user and its tokens but not the session.
`test_sessions.py` asserts an exact number of session documents, so a session
left over from an earlier file makes it fail with `assert 2 == 1`. Today the
`api_*` files are safe only because the `client` fixture in `test_auth.py`
clears the collection before `test_sessions.py` runs. A test that logs in and
sorts after `test_auth.py` must clear sessions itself:

```python
def test_something_that_logs_in(client):
    owner = _Owner(client)
    try:
        ...
    finally:
        owner.cleanup()
        db = locutus.persistence()
        db.client[db.db_name]["sessions"].delete_many({})
```

**Clean up in `finally`.** Delete everything a test creates (users, tokens,
institutions, studies and so on) in a `finally` block or a fixture's teardown,
so a failed assertion doesn't leave data for later tests.

**Changing who can call an endpoint.** When you loosen or tighten an endpoint's
access decorator, update the existing tests for it rather than only adding new
ones:

- Remove or rewrite the test that expected the old status code. For example,
  `..._get_requires_admin` expecting `403` no longer applies once the endpoint
  uses `@require_auth`.
- Test both sides of the rule, each in its own test named for what it checks.
  For an endpoint any logged-in user may read, a `..._requires_auth` test
  checks that a caller who isn't logged in gets `401`. A
  `..._allows_any_user` test checks that a logged-in non-admin gets `200` and
  the expected data.
- Keep the tests showing that the endpoint's write methods (`POST`, `PUT`,
  `DELETE`) still return `403` for a non-admin.

For example, opening `GET /api/admin/institutions` to every logged-in user
(in `api_admin_test.py`, which already has `_clear_institutions()`):

```python
def test_admin_institutions_get_requires_auth(client):
    response = client.get("/api/admin/institutions")
    assert response.status_code == 401


def test_admin_institutions_get_allows_any_user(client):
    _clear_institutions()
    user = _Owner(client)  # role defaults to User, not Admin
    try:
        Institution(name="VUMC").save()
        Institution(name="CHOP").save()
        response = client.get("/api/admin/institutions")
        assert response.status_code == 200
        names = sorted(inst["name"] for inst in response.get_json())
        assert names == ["CHOP", "VUMC"]
    finally:
        user.cleanup()
        _clear_institutions()
```

`test_admin_institutions_post_requires_admin` already shows that a non-admin
still can't create an institution.

Before pushing, run the whole suite, not just the files you changed. Problems
with leftover data only show up in a full run.

## Linting & formatting

The project lints and formats with [Ruff](https://docs.astral.sh/ruff/) and type-checks with [basedpyright](https://docs.basedpyright.com/), both left at their stock/default settings — no project-specific rule overrides.

```bash
pip install ".[dev]"
ruff check .
ruff format .
basedpyright
```

**Zed** users get this for free: Zed's built-in Python support already runs Ruff and basedpyright with their default settings, so no extra editor config is needed.

**VS Code** users: this repo ships `.vscode/settings.json` and `.vscode/extensions.json`, so opening the folder will prompt you to install the [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) and [basedpyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright) extensions, with format-on-save and Ruff's fixAll/organize-imports code actions already wired up. Pylance is disabled in favor of basedpyright to avoid two language servers fighting over the same diagnostics.

## API Reference

The full REST API reference — every resource, request/response payloads, and error behavior — lives in the [docs site](https://nih-ncpi.github.io/locutus/#/).

## License

[MIT](LICENSE)
