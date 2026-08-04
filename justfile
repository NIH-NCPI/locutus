mongo_container := "locmongo"
mongo_port := env_var_or_default("MONGODB_PORT", "27017")
dbname := "test"
mongo_uri := "mongodb://localhost:" + mongo_port + "/"+ dbname

mapdragon_dir := "../map-dragon"
mapdragon_repo := "https://github.com/NIH-NCPI/map-dragon.git"
backend_port := "5000"

# Start (or resume) a local MongoDB container for development
mongo:
    docker start {{mongo_container}} 2>/dev/null || docker run -d \
        --name {{mongo_container}} \
        -p {{mongo_port}}:27017 \
        mongo:7.0

# Run the unit tests against the local MongoDB container
test: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} uv run pytest

# Run the unit tests with coverage and write a markdown report to docs/coverage.md (gitignored)
test-coverage: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} uv run pytest --cov=src/locutus  -q
    { \
        echo "# Test Coverage Report"; \
        echo; \
        echo "Generated: $(date -u +'%Y-%m-%d %H:%M UTC')"; \
        echo; \
        uv run coverage report --format=markdown --sort=cover; \
    } > docs/coverage.md
    echo "Coverage report written to docs/coverage.md"

# Run the Flask app against the local MongoDB container
run: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} FLASK_APP=src/locutus/app.py uv run flask run --debug

# Start the backend in the background and the map-dragon front-end's Vite dev server in the foreground (Ctrl-C stops both)
mapdragon: mongo
    #!/usr/bin/env bash
    set -e
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} FLASK_APP=src/locutus/app.py uv run flask run --debug --port {{backend_port}} &
    backend_pid=$!
    trap 'kill "$backend_pid" 2>/dev/null || true' EXIT

    # Clone map-dragon as a sibling directory the first time this runs.
    # Leave an existing checkout alone rather than pulling it -- it isn't ours to mutate.
    if [ ! -d "{{mapdragon_dir}}" ]; then
        echo "Cloning map-dragon into {{mapdragon_dir}}..."
        git clone {{mapdragon_repo}} "{{mapdragon_dir}}"
    fi

    # Base the local env on map-dragon's own committed .env.unified (so
    # search/OAuth config stays in sync with upstream) but point the vocab
    # endpoint at the backend we just started instead of a same-origin /api.
    grep -v '^VITE_VOCAB_ENDPOINT' "{{mapdragon_dir}}/.env.unified" > "{{mapdragon_dir}}/.env.local"
    echo "VITE_VOCAB_ENDPOINT=http://localhost:{{backend_port}}/api" >> "{{mapdragon_dir}}/.env.local"

    if [ ! -d "{{mapdragon_dir}}/node_modules" ]; then
        (cd "{{mapdragon_dir}}" && npm install)
    fi

    (cd "{{mapdragon_dir}}" && npm run dev)

# Stop the local MongoDB container
mongo-stop:
    docker stop {{mongo_container}}

# Wipe the local MongoDB container's data and start fresh
mongo-reset:
    docker rm -f {{mongo_container}} 2>/dev/null || true
    just mongo

provision:
  uv run --with git+https://github.com/carrollaboratory/locutus-utils locutils -db "{{mongo_uri}}" -s all

# Install dependencies for local development
install:
    uv sync --extra dev

#Upgrade dependencies to latest versions
upgrade:
    uv sync --upgrade

# Lint the code
lint:
    ruff check .

# Format the code
format:
    ruff format .
