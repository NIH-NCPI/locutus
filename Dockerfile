
FROM python:3.11-alpine

# Set working directory
WORKDIR /app

# Environment variables
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Install base dependencies and conditionally install ARM-specific dependencies
RUN apk update && apk add --no-cache git

# Install additional build dependencies for ARM64 (Apple Silicon)
RUN if [ "$(uname -m)" = "aarch64" ] || [ "$(uname -m)" = "arm64" ]; then \
    apk add --no-cache \
    gcc \
    g++ \
    musl-dev \
    libffi-dev \
    openssl-dev \
    make \
    libc6-compat \
    python3-dev \
    libstdc++ \
    linux-headers; \
    export GRPC_PYTHON_BUILD_SYSTEM_OPENSSL=1; \
    export GRPC_PYTHON_BUILD_SYSTEM_ZLIB=1; \
    pip install grpcio; \
    fi

# Copy the source code and project metadata
COPY . /app
WORKDIR /app
COPY pyproject.toml .
COPY README.md .

# Install Python dependencies from pyproject.toml
RUN pip install .

# Install github packages that do not conform to the toml file 
COPY requirements.txt .

# Install requirements and clean up git
RUN pip install --no-cache-dir -r requirements.txt && \
    apk del git

# Expose port 80 (for consistency with docker-compose)
EXPOSE 80
CMD ["flask", "run"] 
