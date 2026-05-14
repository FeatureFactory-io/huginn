# Sprint result — AI → SitRep (milestone 7419357)

**Release tag:** `0.2.0`
**Release branch:** `release/0.2.0`
**Staging pipeline:** https://gitlab.com/dp2580/huginn/-/pipelines/2526025464
**Staging URL** (once `deploy_staging` completes): https://huginn-staging.us-east-1.elasticbeanstalk.com
**Production:** **NOT promoted.** `make swap` is a manual human decision per SAO §9–§10.

## What shipped

This release wires Gjallarhorn end-to-end to produce SitReps from the doctrine layer
and ingested data, plus the two read-side UI screens that consume them. Nine tasks,
five backend + four UI, all integrated to `main` and tagged `0.2.0`.

**Backend (gjallarhorn):**
- **T-LLM (!23)** — LLM ABC + `ClaudeLLM` with `retry_on_rate_limit`. Ephemeral cache
  per plan; no real Claude API calls in tests (ScriptedLLM fixture).
- **T-TOOLS (!24)** — `ToolExecutor` with project-scoped read tools
  (`get_commits`, `get_jira_tickets`, `get_chat_messages`, `get_playbook`,
  `get_recent_sitreps`). Fail-closed `WRITE_TOOLS` allowlist.
- **T-AGENT (!28)** — `GjallarhornAgent.create_plan()` + `execute_single_step()`.
  Lazy import of `execute_plan` to break the agent↔tasks cycle. 4 ephemeral-cached
  system blocks per SAO §17.6.
- **T-EXEC (!29)** — `execute_plan` Celery task with full SAO §17.5 resilience matrix:
  `RateLimitError` / `TimeoutError` / `OSError` → `mark_paused_for_retry` + capped
  exponential backoff (≤ 120 s). Idempotent re-entry on `mark_started`.
- **T-SITREP-GEN (!30)** — Narrative-phase generation pipeline with `transaction.atomic`
  plan+steps writes, signal-based persistence, automatic-trigger idempotency on
  `(project, to_dt)`, and TODO stubs at the SSE/Redis publish points (chat milestone).

**UI (sitrep):**
- **T-SITREP-LIST-STEPS (!31)** — 19 RED scenario tests (1:1 with feature file
  `docs/features/act-5-sitrep/sitrep-list.feature`).
- **T-SITREP-LIST-IMPL (!32)** — `SitRepListView` + `sitrep_generate_view` POST
  endpoint, ports `ui/templates/ui/mockups/sitrep/list.html` to production.
  Filters: `trigger`, `pb_version` (accepts `v1` or `1`), date range.
- **T-SITREP-VIEW-STEPS (!33)** — 31 RED scenario tests (1:1 with
  `docs/features/act-5-sitrep/sitrep-view.feature`).
- **T-SITREP-VIEW-IMPL (!34)** — `SitRepDetailView` (read-only), ports
  `ui/templates/ui/mockups/sitrep/view.html`. URL pattern
  `projects/<int:project_pk>/sitreps/<int:pk>/` placed above `projects-detail`
  to avoid shadowing — completes the click-through from the list screen.

## How to look at it (once staging is up)

1. Visit https://huginn-staging.us-east-1.elasticbeanstalk.com and log in.
2. Pick a project (e.g. atlas-backend) → its detail page now has an
   **"Open SitReps"** affordance (test-id `project-open-sitreps`).
3. From the SitRep list screen: filter by trigger / playbook version / date,
   or click **Generate SitRep** (preset = since last; custom = pick from/to)
   to enqueue a manual generation.
4. Click any row to view the narrative SitRep (situation assessment, variables
   placeholder, decisions placeholder, fragos applied, notable activity).
5. The "Open Chat" button on the detail screen is a placeholder (`href="#"`)
   until the Chat milestone wires `chat-fullscreen`.

## Sprint metrics

- **Total tasks:** 9 (5 feature-builder backend, 2 step-def-writer, 2 feature-builder UI)
- **Tasks integrated on first attempt:** 6 (T-LLM, T-TOOLS, T-SITREP-LIST-STEPS,
  T-SITREP-LIST-IMPL, T-SITREP-VIEW-STEPS, T-SITREP-VIEW-IMPL)
- **Tasks integrated on attempt 2:** 3 (T-AGENT, T-EXEC, T-SITREP-GEN — all rejected
  for base-poisoning, then clean on second pass)
- **LE rebase-fixup invocations (Phase-4 carve-out):** 4 (T-EXEC factory-state,
  T-SITREP-GEN base swap, T-SITREP-LIST-IMPL 3-LoC fix, T-SITREP-VIEW-IMPL
  factory-state) — total 3 LoC of LE code edits, all on test contracts not
  business logic.
- **Empty-Result-block rescues:** 4 (T-LLM, T-TOOLS, T-SITREP-LIST-IMPL,
  T-SITREP-VIEW-IMPL — recurring failure mode, post-sprint fix recommended).
- **Pre-release gates green on `main`:** `make lint` ✅, `make test` ✅
  (512 passed / 1 skipped).
- **CI pipeline status:** `verify_release_branch` ✅, `lint` ✅, `test` running,
  `build` / `deploy_staging` queued, `promote_production` **awaits manual click**.

## Known factory bugs (post-sprint backlog)

Captured in detail in `factory/blackboard.md` "Known factory bugs / post-sprint fixes":

1. LE pre-gating to `blocked/` (#78) — fixed in protocol; documented.
2. `integrate.sh merge` awk-race on `status: integrated` flip (one observation,
   T-TOOLS); proposed fix: in-place `sed -i.bak` + post-flip assertion.
3. **Empty `# Result` block routes real work to `blocked/`** (4 observations):
   `rescue-result.sh`'s early-exit only checks `^# Result` presence, not whether
   the status field is filled. Proposed fix: require both `^# Result` AND
   non-empty `^status:[[:space:]]*\S` to skip rescue.
4. Worker `fswatch -1` on `pending/` is edge-triggered and misses
   dep-satisfaction events (one observation, T-SITREP-LIST-STEPS). Mitigation
   used: LE `touch pending/<id>.md`. Proposed fix: add `done/` to fswatch path
   list, or replace with poll loop.
5. **Ruff version drift** between venv (0.15.x) and pre-commit (0.6.0).
   **Resolved this sprint** as part of Phase 4.5: bumped
   `.pre-commit-config.yaml` to `v0.15.12` to match venv + reformatted two test
   files. CI lint passed. (Side-effect of the `chore/style` reformat is
   captured in commit `1c5c337`.)

Plus two new bugs surfaced this sprint:

6. **Worker base-poisoning** — workers `git checkout -b` from a dirty worktree
   tip instead of `git fetch && reset --hard origin/main`. Three workers in a
   row (T-AGENT att 1, T-EXEC att 1, T-SITREP-GEN att 1) shipped contaminated
   diffs. Boilerplate exists in task spec; workers ignore it. Proposed fix:
   hoist into the system blueprint AND have `claim.sh` enforce
   `worktree HEAD == origin/main` before handing off.

7. **Factory-state file conflict on merge** — when `done.sh` writes the
   bookkeeping commit on the worker's branch and main has the equivalent
   commit, `factory/tasks/done/<id>.md` conflicts. Observed on T-EXEC and
   T-SITREP-VIEW-IMPL; resolved both by `git reset --hard origin/main` +
   `git cherry-pick <impl>`. Workaround patched mid-sprint by the human
   (`scripts/factory.sh` now auto-resolves with `git checkout --theirs --` for
   conflicted files before commit, see commit `e5b06f7` / issue #81).

## What the human reviews

- The staging URL above (once `deploy_staging` completes — currently building).
- This file + `factory/blackboard.md` (full event log).
- Then, when satisfied: **`make swap`** to promote staging → production.
  `make swap` promotes the revision currently on the inactive EB env (i.e. the
  one this pipeline just deployed); do not pass `BRANCH=` or arbitrary HEAD.
- File bugs against the post-sprint factory bug list if you want any of those
  fixed before the next milestone.
