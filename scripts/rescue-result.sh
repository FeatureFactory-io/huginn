#!/usr/bin/env bash
# rescue-result.sh — auto-fill an empty # Result block from git state.
#
# Usage: scripts/rescue-result.sh <task-id>
#
# Called automatically by the factory.sh worker loop when a worker exits without
# writing a # Result block (common cause: worker's --workspace is a git worktree,
# so it writes to the worktree copy of the claimed file, not the repo-root copy).
#
# Resolution order:
#   1. Read branch: from the claimed task's frontmatter.
#   2. Resolve commit_sha from git ls-remote origin <branch>.
#   3. Resolve mr from glab mr list --source-branch <branch>.
#   4. Append a # Result block to the claimed file.
#   5. Commit: "factory: rescue T-NNN (auto-filled empty Result block)".
#
# Exit 0 on success; exit 1 if the branch cannot be resolved (nothing to fill in).
#
# Requires: git, glab, rg, jq

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

TASK_ID="${1:?usage: $0 <task-id>}"
CLAIMED="factory/tasks/claimed/${TASK_ID}.md"
BLOCKED="factory/tasks/blocked/${TASK_ID}.md"

# Prefer claimed/, fall back to blocked/ (LE may call this after done.sh --blocked)
if [[ -f "$CLAIMED" ]]; then
  TARGET="$CLAIMED"
elif [[ -f "$BLOCKED" ]]; then
  TARGET="$BLOCKED"
else
  echo "rescue-result: task not in claimed/ or blocked/: ${TASK_ID}" >&2
  exit 1
fi

# Already has a Result block with all fields filled — nothing to do
if rg -q '^# Result' "$TARGET" 2>/dev/null; then
  result_section="$(awk '/^# Result/{found=1; next} found{print}' "$TARGET")"
  _status="$(printf '%s\n' "$result_section" | rg -m1 '^status:[[:space:]]*' 2>/dev/null | sed 's/^status:[[:space:]]*//' | tr -d '"' || true)"
  _branch="$(printf '%s\n' "$result_section" | rg -m1 '^branch:[[:space:]]*' 2>/dev/null | sed 's/^branch:[[:space:]]*//' | tr -d '"' || true)"
  _mr="$(printf '%s\n' "$result_section" | rg -m1 '^mr:[[:space:]]*' 2>/dev/null | sed 's/^mr:[[:space:]]*//' | tr -d '"' || true)"
  _sha="$(printf '%s\n' "$result_section" | rg -m1 '^commit_sha:[[:space:]]*' 2>/dev/null | sed 's/^commit_sha:[[:space:]]*//' | tr -d '"' || true)"
  if [[ -n "$_status" && -n "$_branch" && -n "$_mr" && -n "$_sha" ]]; then
    echo "rescue-result: ${TASK_ID} already has complete # Result block — skipping"
    exit 0
  fi
  echo "rescue-result: ${TASK_ID} has # Result block but fields are empty — stripping and re-filling"
  # Strip the existing (empty) Result block before appending a filled one
  tmpfile="$(mktemp)"
  awk '/^# Result/{exit} {print}' "$TARGET" > "$tmpfile"
  mv "$tmpfile" "$TARGET"
fi

# ── Resolve branch from frontmatter ──────────────────────────────────────────
BRANCH="$(rg -m1 '^branch:[[:space:]]*' "$TARGET" 2>/dev/null \
          | sed 's/^branch:[[:space:]]*//' | tr -d '"' | tr -d "'")"

if [[ -z "$BRANCH" ]]; then
  echo "rescue-result: no branch: field in ${TARGET} — cannot auto-fill" >&2
  exit 1
fi

# ── Resolve commit_sha from origin ───────────────────────────────────────────
COMMIT_SHA="$(git ls-remote origin "$BRANCH" 2>/dev/null | awk '{print $1}' | cut -c1-8 || true)"

# ── Resolve MR number from glab ──────────────────────────────────────────────
MR="0"
if command -v glab >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
  MR="$(glab mr list --source-branch "$BRANCH" -F json 2>/dev/null \
        | jq -r '.[0].iid // 0' 2>/dev/null || echo 0)"
fi

STATUS="rescued"
[[ -n "$COMMIT_SHA" ]] || COMMIT_SHA="unknown"

# ── Append # Result block ─────────────────────────────────────────────────────
printf '\n# Result\n\nstatus: %s\nbranch: %s\nmr: %s\ncommit_sha: %s\n\nAuto-filled by rescue-result.sh — worker exited without writing Result block.\n' \
  "$STATUS" "$BRANCH" "$MR" "$COMMIT_SHA" >> "$TARGET"

echo "rescue-result: ${TASK_ID} → branch=${BRANCH} mr=!${MR} sha=${COMMIT_SHA}"

# ── Commit the rescue ─────────────────────────────────────────────────────────
git add "$TARGET" 2>/dev/null || true
git commit -m "factory: rescue ${TASK_ID} (auto-filled empty Result block)" 2>/dev/null || true
