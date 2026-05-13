#!/usr/bin/env bash
set -euo pipefail

SESSION="huginn-logs"
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

tmux kill-session -t "$SESSION" 2>/dev/null || true

files=("$DIR"/*.jsonl)
if [[ ${#files[@]} -eq 0 ]]; then
  echo "No .jsonl files found in $DIR" >&2
  exit 1
fi

tmux new-session -d -s "$SESSION" -x "$(tput cols)" -y "$(tput lines)"

# First pane: open directly in the initial window
tmux send-keys -t "$SESSION:0.0" "tail -f '${files[0]}' | jq" Enter
tmux select-pane -t "$SESSION:0.0" -T "$(basename "${files[0]}" .jsonl)"

# Remaining files: split vertically each time
for i in "${!files[@]}"; do
  [[ $i -eq 0 ]] && continue
  file="${files[$i]}"
  name="$(basename "$file" .jsonl)"
  tmux split-window -h -t "$SESSION:0"
  tmux send-keys -t "$SESSION:0.$i" "tail -f '$file' | jq" Enter
  tmux select-pane -t "$SESSION:0.$i" -T "$name"
done

# Even out pane widths
tmux select-layout -t "$SESSION:0" even-horizontal

# Show pane titles in the status bar
tmux set-option -t "$SESSION" pane-border-status top
tmux set-option -t "$SESSION" pane-border-format " #{pane_title} "

tmux attach-session -t "$SESSION"
