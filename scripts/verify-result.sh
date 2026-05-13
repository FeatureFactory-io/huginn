#!/usr/bin/env bash
# verify-result.sh — verify a claimed task's # Result block before moving to done/.
#
# Usage: scripts/verify-result.sh <task-id>
#
# Reads factory/tasks/claimed/<id>.md and checks:
#   1. A "# Result" block exists with non-empty status:, branch:, mr:, commit_sha:
#   2. The branch exists on origin (git ls-remote)
#   3. The MR is in state "opened" or "merged" (glab mr view)
#
# Exit 0 on success.
# Exit 2 on failure; reason written to stderr as "reason:<field>: <detail>".
#
# Requires: rg (ripgrep), git, glab, jq

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id>}"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"

[[ -f "$CLAIMED" ]] || {
  echo "error: task not in claimed/: ${TASK_ID}" >&2
  exit 1
}

# ── 1. Check # Result block exists ────────────────────────────────────────────
if ! rg -q '^# Result' "$CLAIMED" 2>/dev/null; then
  echo "reason:result_block: no '# Result' section in ${CLAIMED}" >&2
  exit 2
fi

# Extract fields from the Result block (everything after "# Result" line)
result_section="$(awk '/^# Result/{found=1; next} found{print}' "$CLAIMED")"

_field() {
  printf '%s\n' "$result_section" \
    | rg -m1 "^${1}:[[:space:]]*" \
    | sed "s/^${1}:[[:space:]]*//" \
    | tr -d '"' \
    | tr -d "'"
}

STATUS="$(_field status)"
BRANCH="$(_field branch)"
MR="$(_field mr)"
COMMIT_SHA="$(_field commit_sha)"

# ── 2. Validate fields are non-empty ─────────────────────────────────────────
[[ -n "$STATUS" ]] || { echo "reason:status: field 'status' is empty" >&2; exit 2; }
[[ -n "$BRANCH" ]] || { echo "reason:branch: field 'branch' is empty" >&2; exit 2; }
[[ -n "$MR" ]]     || { echo "reason:mr: field 'mr' is empty" >&2; exit 2; }
[[ -n "$COMMIT_SHA" ]] || { echo "reason:commit_sha: field 'commit_sha' is empty" >&2; exit 2; }

# ── 3. Branch must exist on origin ───────────────────────────────────────────
if ! git ls-remote --exit-code origin "$BRANCH" >/dev/null 2>&1; then
  echo "reason:branch: branch '${BRANCH}' not found on origin" >&2
  exit 2
fi

# ── 4. MR must be in state opened or merged ──────────────────────────────────
if ! command -v jq >/dev/null 2>&1; then
  echo "reason:mr: jq not found — install via: brew install jq" >&2
  exit 2
fi

mr_state="$(glab mr view "$MR" --output json 2>/dev/null | jq -r '.state // empty')"
if [[ -z "$mr_state" ]]; then
  echo "reason:mr: could not fetch MR !${MR} state (glab mr view failed)" >&2
  exit 2
fi
if [[ "$mr_state" != "opened" && "$mr_state" != "merged" ]]; then
  echo "reason:mr: MR !${MR} state is '${mr_state}', expected opened or merged" >&2
  exit 2
fi

echo "verify-result: ${TASK_ID} OK (branch=${BRANCH} mr=!${MR} status=${STATUS})"
exit 0
