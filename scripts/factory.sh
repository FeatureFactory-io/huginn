#!/usr/bin/env bash
# factory.sh — spawn the sprint factory for a given milestone.
#
# Usage:  scripts/factory.sh <milestone-name>
#
# Run from repo root (or any cwd — script cds to repo root).
#
# Creates a tmux session named `huginn-<milestone>` with:
#   - one window per worker role, each running an fswatch loop that claims
#     tasks matching its role from pending/ and invokes cursor-agent
#   - one window for the LE
#   - one window tailing the blackboard
#   - one window running status on a 2s interval (watch if available)
#
# Attach at the end. Detach with prefix-d, reattach with `tmux a -t huginn-<m>`.

set -euo pipefail

MILESTONE="${1:?usage: $0 <milestone-name>}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SESSION="huginn-${MILESTONE}"

# Find a suitable Cursor CLI binary. The exact name varies across versions;
# adjust this if your install is different (see factory/README.md).
if command -v cursor-agent >/dev/null 2>&1; then
  CURSOR_BIN="cursor-agent"
elif command -v cursor >/dev/null 2>&1; then
  CURSOR_BIN="cursor"
else
  echo "error: cursor-agent (or cursor) not found on PATH" >&2
  exit 1
fi

# Tmux session already exists? Refuse to clobber.
if tmux has-session -t "$SESSION" 2>/dev/null; then
  echo "session $SESSION already exists — attach with: tmux a -t $SESSION" >&2
  exit 1
fi

mkdir -p factory/{blueprints,tasks/{pending,claimed,blocked,done,rejected},logs}

ROLES=(step-def-writer feature-builder release-engineer manual-tester)

worker_loop() {
  local role="$1"
  cat <<EOF
cd "$REPO_ROOT" || exit 1
while :; do
  fswatch -1 factory/tasks/pending >/dev/null 2>&1 || true
  for f in factory/tasks/pending/*.md; do
    [[ -f "\$f" ]] || continue
    id="\$(basename "\$f" .md)"
    declared_role="\$(rg -m1 '^role:[[:space:]]*' "\$f" 2>/dev/null | sed 's/^role:[[:space:]]*//')"
    [[ "\$declared_role" == "$role" ]] || continue
    if claimed_path="\$($REPO_ROOT/scripts/claim.sh "\$id" "$role" 2>/dev/null)"; then
      echo "[\$(date +%H:%M:%S)] $role claimed \$id"
      $CURSOR_BIN \\
        --system "\$(cat $REPO_ROOT/prompts/${role}.md)" \\
        --input "\$claimed_path" \\
        2>&1 | tee -a factory/logs/${role}.log
    fi
  done
done
EOF
}

tmux new-session -d -s "$SESSION" -n "le" \
  "cd \"$REPO_ROOT\" && $CURSOR_BIN --system \"\$(cat $REPO_ROOT/prompts/lead-engineer.md)\" \
    --input factory/blackboard.md \
    2>&1 | tee -a factory/logs/le.log; bash"

for role in "${ROLES[@]}"; do
  tmux new-window -t "$SESSION" -n "$role" \
    "$(worker_loop "$role"); bash"
done

tmux new-window -t "$SESSION" -n "blackboard" \
  "cd \"$REPO_ROOT\" && tail -F factory/blackboard.md; bash"

if command -v watch >/dev/null 2>&1; then
  STATUS_LOOP="watch -n 2 \"$REPO_ROOT/scripts/status.sh\""
else
  STATUS_LOOP="while sleep 2; do clear; \"$REPO_ROOT/scripts/status.sh\"; done"
fi

tmux new-window -t "$SESSION" -n "status" \
  "cd \"$REPO_ROOT\" && $STATUS_LOOP; bash"

tmux select-window -t "$SESSION:le"

echo "factory spawned. Attach with:"
echo "  tmux a -t $SESSION"
echo
echo "Or detach with prefix-d and reattach later."
