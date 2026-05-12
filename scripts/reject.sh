#!/usr/bin/env bash
# reject.sh — minimal v1: archive task + reason; LE re-queues pending manually.
#
# Usage: scripts/reject.sh <task-id> "<reason>"
# Looks for factory/tasks/done/<id>.md or factory/tasks/claimed/<id>.md

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id> \"reason\"}"
REASON="${2:?usage: $0 <task-id> \"reason\"}"

mkdir -p "factory/tasks/rejected/${TASK_ID}"
TS="$(date +%Y%m%d-%H%M%S)"
LOG="factory/tasks/rejected/${TASK_ID}/${TS}.txt"

for src in "factory/tasks/done/${TASK_ID}.md" "factory/tasks/claimed/${TASK_ID}.md"; do
  if [[ -f "$src" ]]; then
    {
      echo "reason: ${REASON}"
      echo "---"
      cat "$src"
    } >"$LOG"
    rm -f "$src"
    echo "Archived to ${LOG}"
    echo "Next: copy or recreate factory/tasks/pending/${TASK_ID}.md from the archive," >&2
    echo "      bump attempt: in frontmatter, then git commit per factory convention." >&2
    exit 0
  fi
done

echo "error: task not in done/ or claimed/: ${TASK_ID}" >&2
exit 1
