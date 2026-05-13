#!/usr/bin/env bash
# release.sh — cut a semver release from main after all tasks are integrated.
#
# Usage: scripts/release.sh <semver> [--dry-run]
#
# Guards (all must pass):
#   1. <semver> matches x.y.z (no v prefix)
#   2. factory/tasks/pending/ and factory/tasks/claimed/ are empty
#   3. Every factory/tasks/done/*.md has "status: integrated"
#   4. The git tag <semver> does not already exist
#
# On success (non-dry-run, on main):
#   - git tag <semver>
#   - git push origin <semver>
#   - git push origin main:refs/heads/release/<semver>
#   - bb-append.sh "- (LE) cut release <semver>"
#
# GitLab CI for release/<semver> then runs:
#   ci-verify-release-branch → make staging → (manual) make swap

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_ROOT"

SEMVER="${1:?usage: $0 <semver> [--dry-run]}"
DRY_RUN=0
[[ "${2:-}" == "--dry-run" ]] && DRY_RUN=1

# ── 1. Validate semver format ──────────────────────────────────────────────────
if ! [[ "$SEMVER" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "error: semver '${SEMVER}' must match x.y.z (no 'v' prefix)" >&2
  exit 1
fi

# ── 2. pending/ and claimed/ must be empty ────────────────────────────────────
pending_count="$(find factory/tasks/pending -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"
claimed_count="$(find factory/tasks/claimed -name '*.md' 2>/dev/null | wc -l | tr -d ' ')"

if (( pending_count > 0 )); then
  echo "error: factory/tasks/pending/ is not empty (${pending_count} task(s) remain):" >&2
  ls factory/tasks/pending/ >&2
  exit 1
fi
if (( claimed_count > 0 )); then
  echo "error: factory/tasks/claimed/ is not empty (${claimed_count} task(s) in flight):" >&2
  ls factory/tasks/claimed/ >&2
  exit 1
fi

# ── 3. Every done/*.md must have status: integrated ───────────────────────────
not_integrated=()
for f in factory/tasks/done/*.md; do
  [[ -f "$f" ]] || continue
  status_val="$(rg -m1 '^status:[[:space:]]*' "$f" 2>/dev/null | sed 's/^status:[[:space:]]*//' | tr -d '"' || echo '')"
  if [[ "$status_val" != "integrated" ]]; then
    not_integrated+=("$(basename "$f") (status: ${status_val:-missing})")
  fi
done

if (( ${#not_integrated[@]} > 0 )); then
  echo "error: the following done/ tasks are not yet integrated:" >&2
  printf '  %s\n' "${not_integrated[@]}" >&2
  echo "       Run 'scripts/integrate.sh merge <id>' for each one first." >&2
  exit 1
fi

# ── 4. Tag must not already exist ─────────────────────────────────────────────
if git rev-parse "$SEMVER" >/dev/null 2>&1; then
  echo "error: git tag '${SEMVER}' already exists" >&2
  exit 1
fi

# ── 5. Must be on main ────────────────────────────────────────────────────────
current_branch="$(git symbolic-ref --short HEAD 2>/dev/null || echo 'DETACHED')"
if [[ "$current_branch" != "main" ]]; then
  echo "error: must be on 'main' to cut a release (currently on '${current_branch}')" >&2
  exit 1
fi

echo "release.sh: all guards passed for ${SEMVER}"
echo "  pending: ${pending_count}  claimed: ${claimed_count}  not-integrated: ${#not_integrated[@]}"

if [[ $DRY_RUN -eq 1 ]]; then
  echo "DRY RUN — would execute:"
  echo "  git tag ${SEMVER}"
  echo "  git push origin ${SEMVER}"
  echo "  git push origin main:refs/heads/release/${SEMVER}"
  exit 0
fi

echo "Tagging and pushing …"
git tag "$SEMVER"
git push origin "$SEMVER"
git push origin "main:refs/heads/release/${SEMVER}"

"$REPO_ROOT/scripts/bb-append.sh" "$(printf -- '- **%s %s** 🚀 (LE) cut release **%s** — CI pipeline starting on release/%s' \
  "$(date +%Y-%m-%d)" "$(date +%H:%M:%S)" "$SEMVER" "$SEMVER")"

echo ""
echo "Release ${SEMVER} cut. GitLab CI will:"
echo "  1. Run ci-verify-release-branch (validate stage)"
echo "  2. Build Docker image + make staging (deploy to inactive EB)"
echo "  3. Await manual 'make swap' to promote to production"
