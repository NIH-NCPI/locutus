mongo_container := "locmongo"
mongo_port := env_var_or_default("MONGODB_PORT", "27017")
dbname := "test"
mongo_uri := "mongodb://localhost:" + mongo_port + "/"+ dbname

# Start (or resume) a local MongoDB container for development
mongo:
    docker start {{mongo_container}} 2>/dev/null || docker run -d \
        --name {{mongo_container}} \
        -p {{mongo_port}}:27017 \
        mongo:7.0

# Run the unit tests against the local MongoDB container
test: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} uv run pytest

# Run the Flask app against the local MongoDB container
run: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}} FLASK_APP=src/locutus/app.py uv run flask run --debug

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
    uv pip install ".[dev]"

# Lint the code
lint:
    ruff check .

# Format the code
format:
    ruff format .
