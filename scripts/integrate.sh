#!/usr/bin/env bash
# integrate.sh — LE tool for reviewing and merging worker task branches.
#
# Usage:
#   scripts/integrate.sh <id>          # diff review (read-only): print worktree + git log/diff
#   scripts/integrate.sh merge <id>    # merge the MR via glab, mark task as integrated
#
# Requires: git, glab, jq, rg

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

# ── Argument parsing ──────────────────────────────────────────────────────────
MODE="review"
if [[ "${1:-}" == "merge" ]]; then
  MODE="merge"
  TASK_ID="${2:?usage: $0 merge <task-id>}"
else
  TASK_ID="${1:?usage: $0 <task-id> | $0 merge <task-id>}"
fi

DONE_FILE="factory/tasks/done/${TASK_ID}.md"

[[ -f "$DONE_FILE" ]] || {
  echo "error: task not in done/: ${TASK_ID}" >&2
  exit 1
}

# ── Extract Result fields ─────────────────────────────────────────────────────
result_section="$(awk '/^# Result/{found=1; next} found{print}' "$DONE_FILE")"

_field() {
  printf '%s\n' "$result_section" \
    | rg -m1 "^${1}:[[:space:]]*" \
    | sed "s/^${1}:[[:space:]]*//" \
    | tr -d '"' \
    | tr -d "'"
}

BRANCH="$(_field branch)"
MR="$(_field mr)"
ROLE="$(rg -m1 '^role:[[:space:]]*' "$DONE_FILE" 2>/dev/null | sed 's/^role:[[:space:]]*//' || echo '')"

[[ -n "$BRANCH" ]] || { echo "error: 'branch' field missing in ${DONE_FILE}" >&2; exit 1; }
[[ -n "$MR" ]]     || { echo "error: 'mr' field missing in ${DONE_FILE}" >&2; exit 1; }

WORKTREE="$REPO_ROOT/.worktrees/${ROLE}"

# ── Review mode (read-only) ───────────────────────────────────────────────────
if [[ "$MODE" == "review" ]]; then
  echo "=== integrate: ${TASK_ID} (review) ==="
  echo "Worktree : ${WORKTREE}"
  echo "Branch   : ${BRANCH}"
  echo "MR       : !${MR}"
  echo ""

  if [[ -d "$WORKTREE" ]]; then
    echo "--- git log (${BRANCH} vs main) ---"
    git -C "$WORKTREE" log --oneline "main..${BRANCH}" 2>/dev/null || \
      echo "(worktree not on branch ${BRANCH} — run: cd ${WORKTREE} && git checkout ${BRANCH})"
    echo ""
    echo "--- git diff --stat (main...${BRANCH}) ---"
    git -C "$WORKTREE" diff --stat "main...${BRANCH}" 2>/dev/null || true
  else
    echo "(worktree ${WORKTREE} not present — factory.sh creates worktrees at startup)"
    echo "To inspect manually:"
    echo "  git log --oneline main..${BRANCH}"
    echo "  git diff --stat main...${BRANCH}"
  fi
  exit 0
fi

# ── Merge mode ────────────────────────────────────────────────────────────────
if ! command -v jq >/dev/null 2>&1; then
  echo "error: jq required for merge mode — install via: brew install jq" >&2
  exit 1
fi

echo "=== integrate merge: ${TASK_ID} ==="
echo "MR !${MR}  branch ${BRANCH}"

# Assert MR can be merged
mr_json="$(glab mr view "$MR" --output json 2>/dev/null)"
merge_status="$(printf '%s\n' "$mr_json" | jq -r '.merge_status // empty')"
mr_state="$(printf '%s\n' "$mr_json" | jq -r '.state // empty')"

if [[ "$mr_state" == "merged" ]]; then
  echo "MR !${MR} is already merged — updating task status only."
else
  if [[ "$merge_status" != "can_be_merged" ]]; then
    echo "error: MR !${MR} merge_status is '${merge_status}' (expected 'can_be_merged')" >&2
    echo "       Rebase the branch onto the target and push, then retry." >&2
    exit 1
  fi
  echo "Merging MR !${MR} (squash, remove source branch) …"
  glab mr merge "$MR" --squash --remove-source-branch --yes
  echo "Merged."
fi

# Mark task as integrated in done/ file
if rg -q '^status:' "$DONE_FILE" 2>/dev/null; then
  # Replace the status line inside the Result block
  TMP="$(mktemp)"
  awk '
    /^# Result/{in_result=1}
    in_result && /^status:/ && !done { print "status: integrated"; done=1; next }
    { print }
  ' "$DONE_FILE" > "$TMP"
  mv "$TMP" "$DONE_FILE"
else
  # Append status: integrated if no status field found
  printf '\nstatus: integrated\n' >> "$DONE_FILE"
fi

"$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🔀 (LE) merged **%s** via !%s → integrated' \
  "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$TASK_ID" "$MR")"

echo "Task ${TASK_ID} marked status: integrated."
