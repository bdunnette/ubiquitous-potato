# Multi-platform support for linux/amd64 and linux/arm64
FROM ghcr.io/astral-sh/uv:latest AS uv-bin
FROM python:3.13-slim

# Install system packages required for compiling Python packages and AWS tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    gcc \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy uv binary directly from official Astral image
COPY --from=uv-bin /uv /uvx /bin/

WORKDIR /app

# Copy dependency definitions and lockfile for reproducible, locked builds
COPY pyproject.toml uv.lock .python-version ./

# Create virtualenv and install dependencies using uv
RUN uv venv /app/.venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

RUN uv sync --frozen

# Copy the rest of the application
COPY . .

# Default entrypoint allows running any zappa or manage command
ENTRYPOINT ["zappa"]
CMD ["update", "dev"]
