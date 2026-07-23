mongo_container := "locutus-mongo"
mongo_port := "27017"
mongo_uri := "mongodb://localhost:" + mongo_port

# Start (or resume) a local MongoDB container for development
mongo:
    docker start {{mongo_container}} 2>/dev/null || docker run -d \
        --name {{mongo_container}} \
        -p {{mongo_port}}:27017 \
        mongo:7.0

# Run the unit tests against the local MongoDB container
test: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}}/test pytest

# Run the Flask app against the local MongoDB container
run: mongo
    LOCUTUS_DB_TYPE=mongodb MONGO_URI={{mongo_uri}}/locutus FLASK_APP=src/locutus/app.py flask run --debug

# Stop the local MongoDB container
mongo-stop:
    docker stop {{mongo_container}}

# Wipe the local MongoDB container's data and start fresh
mongo-reset:
    docker rm -f {{mongo_container}} 2>/dev/null || true
    just mongo

# Install dependencies for local development
install:
    pip install ".[dev]"

# Lint the code
lint:
    ruff check .

# Format the code
format:
    ruff format .
