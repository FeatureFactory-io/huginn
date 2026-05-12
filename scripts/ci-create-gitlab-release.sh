#!/usr/bin/env bash
# Create a GitLab Release for the semver tag (tag must already exist on the commit).
# Used by: make gitlab-release (GitLab release stage; requires release-cli on PATH).
set -euo pipefail
: "${CI_COMMIT_BRANCH:?}"

RELEASE_TAG="${CI_COMMIT_BRANCH#release/}"

exec release-cli create \
  --name "Huginn ${RELEASE_TAG}" \
  --tag-name "${RELEASE_TAG}" \
  --description "Staging deployed for review. After acceptance, run the manual **promote_production** job to swap EB prod CNAMEs."
