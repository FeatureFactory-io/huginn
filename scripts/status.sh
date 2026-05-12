#!/usr/bin/env bash
# status.sh — factory queue counts + sample IDs.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

count_md() {
  local dir="$1"
  local n=0
  local f
  shopt -s nullglob
  for f in "${dir}"/*.md; do
    [[ -f "$f" ]] || continue
    ((n++)) || true
  done
  shopt -u nullglob
  echo "$n"
}

sample_ids() {
  local dir="$1"
  local max="${2:-8}"
  local f n=0
  shopt -s nullglob
  for f in "${dir}"/*.md; do
    [[ -f "$f" ]] || continue
    printf '%s ' "$(basename "$f" .md)"
    ((++n >= max)) && break
  done
  shopt -u nullglob
  echo
}

echo "pending:  $(count_md factory/tasks/pending)  $(sample_ids factory/tasks/pending)"
echo "claimed:  $(count_md factory/tasks/claimed)  $(sample_ids factory/tasks/claimed)"
echo "blocked:  $(count_md factory/tasks/blocked)  $(sample_ids factory/tasks/blocked)"
echo "done:     $(count_md factory/tasks/done)     $(sample_ids factory/tasks/done)"

rej="$(find factory/tasks/rejected -mindepth 2 -type f 2>/dev/null | wc -l | tr -d ' ')"
echo "rejected archive files: ${rej} (under factory/tasks/rejected/<id>/)"
