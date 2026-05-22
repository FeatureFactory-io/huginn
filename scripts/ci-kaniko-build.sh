#!/bin/sh
# Build and push app image to ECR (Kaniko). Invoked from GitLab build job only.
# Same logic as: make ci-build
# POSIX sh: Kaniko debug executor has busybox only (no bash, no Alpine apk).
set -eu
: "${CI_PROJECT_DIR:?}"
: "${CI_COMMIT_TAG:?}"
: "${CI_COMMIT_SHORT_SHA:?}"
: "${ECR_REGISTRY:?}"
: "${KANIKO_EXECUTOR:=/kaniko/executor}"

exec "$KANIKO_EXECUTOR" \
  --context "${CI_PROJECT_DIR}" \
  --dockerfile "${CI_PROJECT_DIR}/Dockerfile" \
  --build-arg "GIT_REVISION=${CI_COMMIT_SHORT_SHA}" \
  --destination "${ECR_REGISTRY}/huginn:${CI_COMMIT_SHORT_SHA}" \
  --destination "${ECR_REGISTRY}/huginn:${CI_COMMIT_TAG}" \
  --destination "${ECR_REGISTRY}/huginn:latest"
