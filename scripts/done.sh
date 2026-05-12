#!/usr/bin/env bash
# done.sh — move a claimed task to done (optional Result stub).
#
# Usage: scripts/done.sh <task-id>
# Requires factory/tasks/claimed/<task-id>.md to exist.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id>}"

CLAIMED="factory/tasks/claimed/${TASK_ID}.md"
DONE="factory/tasks/done/${TASK_ID}.md"

[[ -f "$CLAIMED" ]] || {
  echo "error: task not in claimed/: ${TASK_ID}" >&2
  exit 1
}

if ! rg -q '^# Result' "$CLAIMED" 2>/dev/null; then
  cat >> "$CLAIMED" <<'BLOCK'

# Result

status: passed
branch: ""
mr: ""
commit_sha: ""

_(worker: fill branch, merge request IID, commit SHA; set status to failed or blocked if applicable)_
BLOCK
fi

mv "$CLAIMED" "$DONE"
echo "$(pwd)/${DONE}"
