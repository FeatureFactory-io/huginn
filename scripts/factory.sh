#!/usr/bin/env bash
# factory.sh — spawn the sprint factory for a given milestone.
#
# Usage:  scripts/factory.sh <milestone-name> [mgmt-branch]
#
# mgmt-branch defaults to the current branch (should be features/<milestone>).
# Run from repo root (or any cwd — script cds to repo root).
#
# Worktree model:
#   - Repo root stays on the MGMT branch (features/<milestone>) — LE home.
#     Factory state (tasks/, blackboard.md) is committed here only.
#   - Each worker role gets a git worktree under .worktrees/<role>/
#     so workers never need to checkout the mgmt branch or stash.
#   - .worktrees/ is in .gitignore; worktrees are pruned on teardown.
#
# Creates a tmux session named `huginn-<milestone>` with:
#   - one window per worker role, cwd = .worktrees/<role>/
#   - one window for the LE (cwd = repo root, mgmt branch)
#   - one window tailing the blackboard
#   - one window running status on a 2s interval (watch if available)
#
# Attach at the end. Detach with prefix-d, reattach with `tmux a -t huginn-<m>`.

set -euo pipefail

MILESTONE="${1:?usage: $0 <milestone-name>}"
MGMT_BRANCH="${2:-$(git symbolic-ref --short HEAD 2>/dev/null || echo 'features/gjallarhorn')}"
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
mkdir -p .worktrees

# Ensure .worktrees is gitignored
if ! grep -qxF '.worktrees/' .gitignore 2>/dev/null; then
  echo '.worktrees/' >> .gitignore
fi

ROLES=(step-def-writer feature-builder release-engineer manual-tester)

# Create a worktree for each role on an orphan scratch branch.
# Workers check out their task branch inside the worktree when they claim a task.
for role in "${ROLES[@]}"; do
  wt="$REPO_ROOT/.worktrees/$role"
  if [[ ! -d "$wt" ]]; then
    # Start on the mgmt branch so the worktree has the full history
    git worktree add "$wt" "$MGMT_BRANCH" --detach 2>/dev/null || true
  fi
done

worker_loop() {
  local role="$1"
  local wt="$REPO_ROOT/.worktrees/$role"
  cat <<EOF
cd "$wt" || exit 1
while :; do
  fswatch -1 "$REPO_ROOT/factory/tasks/pending" >/dev/null 2>&1 || true
  for f in "$REPO_ROOT"/factory/tasks/pending/*.md; do
    [[ -f "\$f" ]] || continue
    id="\$(basename "\$f" .md)"
    declared_role="\$(rg -m1 '^role:[[:space:]]*' "\$f" 2>/dev/null | sed 's/^role:[[:space:]]*//')"
    [[ "\$declared_role" == "$role" ]] || continue
    # claim.sh runs in the REPO ROOT (mgmt branch) so factory state commits land there
    if claimed_path="\$($REPO_ROOT/scripts/claim.sh "\$id" "$role" 2>/dev/null)"; then
      echo "[\$(date +%H:%M:%S)] $role claimed \$id"
      # Switch this worktree to the task's feature branch
      task_branch="\$(rg -m1 '^branch:[[:space:]]*' "\$claimed_path" 2>/dev/null | sed 's/^branch:[[:space:]]*//')"
      if [[ -n "\$task_branch" ]]; then
        git checkout "\$task_branch" 2>/dev/null || git checkout -b "\$task_branch" 2>/dev/null || true
      fi
      COMBINED_PROMPT="\$(printf '%s\n\n---\n\n%s' "\$(cat $REPO_ROOT/prompts/${role}.md)" "\$(cat "\$claimed_path")")"
      $CURSOR_BIN \\
        --print \\
        --yolo \\
        --output-format stream-json \\
        --stream-partial-output \\
        --workspace "\$wt" \\
        "\$COMBINED_PROMPT" \\
        2>&1 | tee -a "$REPO_ROOT/factory/logs/${role}.log"
      "$REPO_ROOT/scripts/done.sh" "\$id" 2>/dev/null || true
      (cd "$REPO_ROOT" && git add factory/tasks/ && git commit -m "factory: done \$id" && git push) 2>&1 | tee -a "$REPO_ROOT/factory/logs/${role}.log" || true
    fi
  done
done
EOF
}

# LE window — autonomous agent loop on mgmt branch, reviews done/ tasks
LE_LOOP=$(cat <<'LEEOF'
cd "REPO_ROOT_PLACEHOLDER" && git checkout MGMT_PLACEHOLDER 2>/dev/null || true
while :; do
  changed="$(fswatch -1 "REPO_ROOT_PLACEHOLDER/factory/tasks/done" 2>/dev/null)"
  [[ -f "$changed" ]] || continue
  task_id="$(basename "$changed" .md)"
  PROMPT="$(cat REPO_ROOT_PLACEHOLDER/prompts/lead-engineer.md)

---

FACTORY STATE:
$(cat REPO_ROOT_PLACEHOLDER/factory/blackboard.md)

TASK JUST COMPLETED — review per checks 1-6 in your prompt, then act:
$(cat "$changed")

PENDING:
$(ls REPO_ROOT_PLACEHOLDER/factory/tasks/pending/ 2>/dev/null)

CLAIMED:
$(ls REPO_ROOT_PLACEHOLDER/factory/tasks/claimed/ 2>/dev/null)"
  CURSOR_BIN_PLACEHOLDER \
    --print \
    --yolo \
    --output-format stream-json \
    --stream-partial-output \
    --workspace "REPO_ROOT_PLACEHOLDER" \
    "$PROMPT" \
    2>&1 | tee -a "REPO_ROOT_PLACEHOLDER/factory/logs/le.log"
  (cd "REPO_ROOT_PLACEHOLDER" && git add factory/ && git commit -m "factory: LE reviewed $task_id" && git push) 2>/dev/null || true
done
LEEOF
)
LE_LOOP="${LE_LOOP//REPO_ROOT_PLACEHOLDER/$REPO_ROOT}"
LE_LOOP="${LE_LOOP//MGMT_PLACEHOLDER/$MGMT_BRANCH}"
LE_LOOP="${LE_LOOP//CURSOR_BIN_PLACEHOLDER/$CURSOR_BIN}"
tmux new-session -d -s "$SESSION" -n "le" "bash -c $(printf '%q' "$LE_LOOP"); bash"

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
echo
echo "Worktrees: $(git worktree list --porcelain | grep -c 'worktree') active"
echo "To clean up worktrees after the sprint: git worktree prune"
