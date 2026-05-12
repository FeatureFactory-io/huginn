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
brew install git glab fswatch tmux ripgrep
```

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
```

**Preflight flags:** `--allow-dirty` — skip “clean git working tree” check.

## Cursor CLI in `factory.sh`

Worker panes invoke `$CURSOR_BIN` with `--system` and `--input`. Flag names vary by Cursor version; adjust [`scripts/factory.sh`](../scripts/factory.sh) if your CLI differs.

## Maintainer verification

Syntax-check scripts:

```bash
bash -n scripts/factory.sh scripts/preflight.sh scripts/claim.sh scripts/done.sh scripts/reject.sh scripts/status.sh
```

Functional **preflight** requires **`glab auth`** and a real milestone title.

## Future hardening

- Parse Gherkin in preflight (e.g. official parser or pytest dry-run) — not in v1 scaffold.
