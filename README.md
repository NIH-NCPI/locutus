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
