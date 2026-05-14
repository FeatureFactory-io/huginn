# Dark factory (`factory/`)

Mechanical scaffold for the **dark-factory** Cursor skill: milestone-driven LE + specialist workers via filesystem queue (`tasks/pending` → `claimed` → `done`), tmux + `fswatch`, and Cursor CLI.

## Canonical docs

| Topic | Location |
|--------|-----------|
| Phases 0–6 contract | Dark-factory skill `SKILL.md` — typically `~/.cursor/skills/dark-factory/SKILL.md` (attach skill in Cursor) |
| Cursor conventions | [`docs/workflows/cursor_agent_protocol.md`](../docs/workflows/cursor_agent_protocol.md) |
| CI/CD, staging vs prod | [`docs/architecture/SAO.md`](../docs/architecture/SAO.md) §9–§10 |
| LE watch loop detail | [`references/worker-protocol.md`](../references/worker-protocol.md) + skill `references/loop.md` |

## Prerequisites

```bash
brew install git glab fswatch tmux ripgrep util-linux
```

> **`util-linux`** provides `flock(1)`, used by `scripts/bb-append.sh` to serialize concurrent blackboard writes. On Linux it is pre-installed.
> On macOS, Homebrew installs `util-linux` as a keg-only formula. `bb-append.sh` resolves the path automatically via `brew --prefix util-linux`. Optionally add it to `PATH` for shell use:
> ```bash
> export PATH="$(brew --prefix util-linux)/bin:$PATH"
> ```

Plus **`cursor-agent`** or **`cursor`** on `PATH`. **`python3`** is required for **`preflight.sh`** (JSON issue validation). Optional: **`jq`**, **`watch`** (GNU watch without `-c` works on macOS Homebrew `watch`; if missing, `scripts/factory.sh` falls back to a `sleep` loop).

Mockups for ingestion live under **`ui/templates/ui/mockups/`** (not a repo-root `mockups/` folder).

## Commands

Run from the **repository root**.

```bash
# Phase 0 — validate milestone, issues, tooling (see script for flags)
./scripts/preflight.sh 'Your Milestone Title'

# Phase 3 — tmux factory (after LE has filled pending tasks)
./scripts/factory.sh 'Your-Milestone-Slug'
# Attach: tmux a -t huginn-Your-Milestone-Slug

# Post-sprint — archive completed sprint and reset factory/ for the next run
./scripts/archive.sh 'your-sprint-slug'
# Moves blackboard, blueprints, done/rejected/blocked tasks, and logs to
# factory/archive/<slug>/; recreates a clean skeleton; removes stale worktrees.
# Refuses to run if pending/ or claimed/ are non-empty.
```

**Preflight flags:** `--allow-dirty` — skip “clean git working tree” check. `--allow-missing-featurefile-ref` — warn but pass when some milestone issues omit `docs/features/.../*.feature` (default remains strict).

## Cursor CLI in `factory.sh`

Worker panes invoke `$CURSOR_BIN` in headless mode. `scripts/factory.sh` now supports per-role model defaults via env vars:

- `FACTORY_LE_MODEL` — defaults to `claude-opus-4-7-thinking-xhigh`
- `FACTORY_MODEL_FEATURE_BUILDER` — defaults to `claude-4.6-sonnet-medium-thinking`
- `FACTORY_MODEL_STEP_DEF_WRITER`
- `FACTORY_MODEL_RELEASE_ENGINEER`
- `FACTORY_MODEL_MANUAL_TESTER`

Flag names vary by Cursor version; adjust [`scripts/factory.sh`](../scripts/factory.sh) if your CLI differs.

## Maintainer verification

Syntax-check scripts:

```bash
bash -n scripts/factory.sh scripts/preflight.sh scripts/claim.sh scripts/done.sh \
         scripts/reject.sh scripts/status.sh scripts/bb-append.sh \
         scripts/verify-result.sh scripts/integrate.sh scripts/release.sh \
         scripts/archive.sh
```

Functional **preflight** requires **`glab auth`** and a real milestone title.

## Task queue lanes

| Directory | Meaning |
|-----------|---------|
| `tasks/pending/` | Waiting to be claimed by a worker |
| `tasks/claimed/` | Currently being worked on (atomic `mv` from pending) |
| `tasks/done/` | Worker completed; awaiting LE review and `integrate.sh merge` |
| `tasks/rejected/<id>/` | Archived rejection snapshots (timestamped `.txt` files) |
| `tasks/blocked/` | Tasks routed here by two paths: (1) `reject.sh` when `attempt+1 > FACTORY_MAX_ATTEMPTS`; (2) `done.sh --blocked` when `verify-result.sh` fails after a worker finishes (missing/blank `# Result`, branch not pushed, or MR not open/merged). LE decides next action in both cases. |

`scripts/reject.sh <id> "<reason>"` auto-requeues to `pending/` with `attempt: N+1`.
When `attempt+1 > FACTORY_MAX_ATTEMPTS`, it writes to `blocked/<id>.md` instead.
Override the limit: `FACTORY_MAX_ATTEMPTS=5 scripts/reject.sh …`

## Future hardening

- Parse Gherkin in preflight (e.g. official parser or pytest dry-run) — not in v1 scaffold.
