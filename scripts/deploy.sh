#!/usr/bin/env bash
# Deploy or update the Django application to AWS Lambda using Zappa and uv.
set -euo pipefail

STAGE="${1:-dev}"
INITIAL="${2:-}"

echo "==> Syncing dependencies with uv..."
uv sync

echo "==> Collecting static assets for WhiteNoise..."
USE_S3_SQLITE=false uv run python manage.py collectstatic --noinput

if [ "$INITIAL" = "--initial" ] || [ "$INITIAL" = "-i" ]; then
    echo "==> Performing initial deployment (zappa deploy $STAGE)..."
    uv run zappa deploy "$STAGE"
else
    echo "==> Updating existing deployment (zappa update $STAGE)..."
    uv run zappa update "$STAGE"
fi

echo "==> Executing remote database migrations on Lambda..."
uv run zappa manage "$STAGE" migrate

echo "==> Deployment finished successfully!"
