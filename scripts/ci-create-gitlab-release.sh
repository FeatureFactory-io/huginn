#!/usr/bin/env sh
# Create or update the GitLab Release for the semver tag (triggered by the tag push).
# Used by: make gitlab-release (GitLab release stage; requires release-cli on PATH).
# NOTE: runs inside registry.gitlab.com/gitlab-org/release-cli which has no bash.
#
# When the operator ships with `glab release create` (SAO §9), the release already
# exists before this job runs — update the description instead of failing with 409.
set -eu
: "${CI_COMMIT_TAG:?CI_COMMIT_TAG is required — pipeline must be triggered by a semver tag}"

RELEASE_NAME="Huginn ${CI_COMMIT_TAG}"
RELEASE_DESC="Staging deployed for review. After acceptance, run the manual **promote_production** job to swap EB prod CNAMEs."

if release-cli create \
  --name "$RELEASE_NAME" \
  --tag-name "${CI_COMMIT_TAG}" \
  --description "$RELEASE_DESC"; then
  exit 0
fi

exec release-cli update \
  --tag-name "${CI_COMMIT_TAG}" \
  --name "$RELEASE_NAME" \
  --description "$RELEASE_DESC"
