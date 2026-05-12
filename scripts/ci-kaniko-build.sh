#!/bin/sh
# Build and push app image to ECR (Kaniko). Invoked from GitLab build job only.
# Same logic as: make ci-build
# POSIX sh: Kaniko debug executor has busybox only (no bash, no Alpine apk).
set -eu
: "${CI_PROJECT_DIR:?}"
: "${CI_COMMIT_BRANCH:?}"
: "${CI_COMMIT_SHORT_SHA:?}"
: "${ECR_REGISTRY:?}"
: "${KANIKO_EXECUTOR:=/kaniko/executor}"

RELEASE_SEMVER="${CI_COMMIT_BRANCH#release/}"

exec "$KANIKO_EXECUTOR" \
  --context "${CI_PROJECT_DIR}" \
  --dockerfile "${CI_PROJECT_DIR}/Dockerfile" \
  --build-arg "GIT_REVISION=${CI_COMMIT_SHORT_SHA}" \
  --destination "${ECR_REGISTRY}/huginn:${CI_COMMIT_SHORT_SHA}" \
  --destination "${ECR_REGISTRY}/huginn:${RELEASE_SEMVER}" \
  --destination "${ECR_REGISTRY}/huginn:latest"
