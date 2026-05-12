#!/usr/bin/env bash
# preflight.sh — Phase 0 dry gate for dark-factory (tools, git clean, milestone, issues).
#
# Usage: scripts/preflight.sh [--allow-dirty] <milestone-title>
#
# Milestone must match GitLab's milestone filter for `glab issue list --milestone`.
# Each issue title/description must mention at least one path like docs/features/.../*.feature

set -euo pipefail

ALLOW_DIRTY=false
ARGS=()
for arg in "$@"; do
  case "$arg" in
    --allow-dirty) ALLOW_DIRTY=true ;;
    *) ARGS+=("$arg") ;;
  esac
done

MILESTONE="${ARGS[0]:?usage: $0 [--allow-dirty] <milestone-title>}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "error: missing command: $1" >&2
    exit 1
  }
}

for c in git glab fswatch tmux rg python3; do require_cmd "$c"; done

if ! command -v cursor-agent >/dev/null 2>&1 && ! command -v cursor >/dev/null 2>&1; then
  echo "error: need cursor-agent or cursor on PATH" >&2
  exit 1
fi

command -v jq >/dev/null 2>&1 || echo "warn: jq not on PATH (optional)" >&2
command -v watch >/dev/null 2>&1 || echo "warn: watch not on PATH (factory.sh falls back to sleep loop)" >&2

if [[ "$ALLOW_DIRTY" != true ]] && [[ -n "$(git status --porcelain 2>/dev/null)" ]]; then
  echo "error: git working tree not clean (commit/stash or pass --allow-dirty)" >&2
  exit 1
fi

parse_gitlab_repo() {
  local url="$1"
  url="${url%.git}"
  if [[ "$url" =~ ^git@[^:]+:(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  if [[ "$url" =~ https?://[^/]+/(.+)$ ]]; then
    echo "${BASH_REMATCH[1]}"
    return 0
  fi
  echo "error: cannot parse owner/repo from git remote URL: $url" >&2
  return 1
}

GLAB_REPO="$(parse_gitlab_repo "$(git remote get-url origin)")"

MOCKS_FOUND=false
if [[ -d ui/templates/ui/mockups ]]; then
  html_count="$(find ui/templates/ui/mockups -name '*.html' 2>/dev/null | wc -l | tr -d ' ')"
  [[ "${html_count}" != "0" ]] && MOCKS_FOUND=true
fi
if [[ "$MOCKS_FOUND" != true ]] && [[ -d mockups ]] && [[ -n "$(ls -A mockups 2>/dev/null)" ]]; then
  MOCKS_FOUND=true
fi
if [[ "$MOCKS_FOUND" != true ]]; then
  echo "warn: no mockups under ui/templates/ui/mockups/ or repo-root mockups/"
fi

ISSUES_JSON="$(glab issue list -R "$GLAB_REPO" --milestone "$MILESTONE" -F json)" || {
  echo "error: glab issue list failed — check milestone title, remote -R ${GLAB_REPO}, and auth (glab auth login)" >&2
  exit 1
}

echo "$ISSUES_JSON" | python3 <<'PY'
import json, re, sys

try:
    issues = json.load(sys.stdin)
except json.JSONDecodeError as e:
    print("error: glab did not return valid JSON — upgrade glab?", e, file=sys.stderr)
    sys.exit(1)
if not isinstance(issues, list) or len(issues) == 0:
    print("error: no issues in milestone (title mismatch or empty milestone)", file=sys.stderr)
    sys.exit(1)
pat = re.compile(r"docs/features/[^\s\)]+\.feature")
missing = []
for i in issues:
    title = i.get("title") or ""
    desc = i.get("description") or ""
    body = title + "\n" + desc
    if not pat.search(body):
        missing.append(str(i.get("iid", "?")))
if missing:
    print(
        "error: issues missing docs/features/.../*.feature in title or description:",
        ", ".join(missing),
        file=sys.stderr,
    )
    sys.exit(1)
print("preflight ok:", len(issues), "issue(s); feature paths referenced")
PY
