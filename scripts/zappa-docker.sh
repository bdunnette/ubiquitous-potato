#!/usr/bin/env bash
# Execute any Zappa command inside a Linux Docker container using uv.
set -euo pipefail

PLATFORM="${DOCKER_DEFAULT_PLATFORM:-linux/arm64}"
if [ -n "${TARGET_ARCH:-}" ]; then
    if [[ "${TARGET_ARCH}" != linux/* ]]; then
        PLATFORM="linux/${TARGET_ARCH}"
    else
        PLATFORM="${TARGET_ARCH}"
    fi
fi
TAG_SUFFIX="${PLATFORM//\//-}"
IMAGE_TAG="django-zappa-deployer:${TAG_SUFFIX}"

echo "==> Building Linux deployment container with uv for platform ${PLATFORM}..."
docker build --platform "${PLATFORM}" -t "${IMAGE_TAG}" .

AWS_DIR="${HOME}/.aws"
CURRENT_DIR="$(pwd)"

echo "==> Executing: zappa $* inside Linux (${PLATFORM}) container..."
docker run --platform "${PLATFORM}" --rm \
    -v "${AWS_DIR}:/root/.aws:ro" \
    -v "${CURRENT_DIR}:/app" \
    -e AWS_PROFILE="${AWS_PROFILE:-default}" \
    -e AWS_DEFAULT_REGION="${AWS_DEFAULT_REGION:-us-east-2}" \
    "${IMAGE_TAG}" "$@"
