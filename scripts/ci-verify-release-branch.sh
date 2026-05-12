#!/usr/bin/env bash
# Verify release/x.y.z branch: remote tag x.y.z exists and matches HEAD.
# Used by: make verify-release (GitLab validate stage).
set -euo pipefail
: "${CI_COMMIT_BRANCH:?CI_COMMIT_BRANCH is required}"

RELEASE_TAG="${CI_COMMIT_BRANCH#release/}"
echo "Verifying branch=${CI_COMMIT_BRANCH} tag=${RELEASE_TAG}"

if ! echo "$CI_COMMIT_BRANCH" | grep -Eq '^release/[0-9]+\.[0-9]+\.[0-9]+$'; then
  echo "ERROR: branch must be release/x.y.z (semver digits only, no v prefix in branch name)."
  exit 1
fi

git fetch --tags --force origin
if ! git show-ref --verify --quiet "refs/tags/$RELEASE_TAG"; then
  echo "ERROR: Git tag '${RELEASE_TAG}' must exist on origin (create on main, push tag, then push this branch)."
  exit 1
fi

TAG_SHA=$(git rev-parse "refs/tags/$RELEASE_TAG^{}")
HEAD_SHA=$(git rev-parse HEAD)
if [ "$TAG_SHA" != "$HEAD_SHA" ]; then
  echo "ERROR: release branch tip must equal tag ${RELEASE_TAG} commit (tag=${TAG_SHA} head=${HEAD_SHA})."
  exit 1
fi

echo "OK: tag ${RELEASE_TAG} points at this commit."
