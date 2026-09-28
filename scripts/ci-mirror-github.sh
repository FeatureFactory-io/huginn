#!/usr/bin/env bash
# Push the current GitLab checkout to the GitHub read mirror (FeatureFactory-io/huginn).
# Used by: GitLab CI job mirror_github (main pushes + semver tag pipelines).
#
# Requires GitLab CI variable GITHUB_MIRROR_TOKEN (fine-grained or classic PAT with
# contents:write on FeatureFactory-io/huginn). Never log the token.
set -euo pipefail

: "${GITHUB_MIRROR_TOKEN:?GITHUB_MIRROR_TOKEN is required (GitLab CI variable)}"
GITHUB_MIRROR_REPO="${GITHUB_MIRROR_REPO:-FeatureFactory-io/huginn}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required on PATH" >&2
  exit 1
fi

REMOTE_URL="https://x-access-token:${GITHUB_MIRROR_TOKEN}@github.com/${GITHUB_MIRROR_REPO}.git"

git remote remove github 2>/dev/null || true
git remote add github "${REMOTE_URL}"

MAIN_REF="${CI_COMMIT_SHA:?CI_COMMIT_SHA is required}"
echo "Mirroring ${MAIN_REF} to github:refs/heads/main (repo=${GITHUB_MIRROR_REPO})"
git push github "${MAIN_REF}:refs/heads/main" --force-with-lease

if [[ -n "${CI_COMMIT_TAG:-}" ]]; then
  echo "Mirroring tag ${CI_COMMIT_TAG}"
  git push github "refs/tags/${CI_COMMIT_TAG}"
fi

git remote remove github
echo "GitHub mirror push complete."
