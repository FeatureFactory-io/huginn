#!/usr/bin/env sh
# Create a GitLab Release for the semver tag (triggered by the tag push).
# Used by: make gitlab-release (GitLab release stage; requires release-cli on PATH).
# NOTE: runs inside registry.gitlab.com/gitlab-org/release-cli which has no bash.
set -eu
: "${CI_COMMIT_TAG:?CI_COMMIT_TAG is required — pipeline must be triggered by a semver tag}"

exec release-cli create \
  --name "Huginn ${CI_COMMIT_TAG}" \
  --tag-name "${CI_COMMIT_TAG}" \
  --description "Staging deployed for review. After acceptance, run the manual **promote_production** job to swap EB prod CNAMEs."
