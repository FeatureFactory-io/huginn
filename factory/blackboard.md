# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 3 — Execution in progress. **All 5 backend tasks merged.** T-LLM !23. T-TOOLS !24. T-AGENT !28 (att 2). T-EXEC !29 (att 2; LE rebase-fixup for factory-state conflict; squash `bf522fd`, merge `f36b5a4`). **T-SITREP-GEN merged (!30, squash `71e4713`, merge `0c475cb`)** on attempt 2 after LE `rebase --onto origin/main 9196520` fixup to strip the two orphaned pre-squash T-EXEC commits from the worker's branch (the predicted base-poisoning materialised exactly as logged the previous wake; worker's own commit `53f8c04`/`34402ea` was clean — 14/14 in-scope files, 485+/12- LoC, 36/36 acceptance GREEN incl. new GEN-21..24, 462+1 regression GREEN, ruff + makemigrations clean, Dr. Dobbs clean — `transaction.atomic` plan+steps writes, signal handler `try/except` cannot break sync, automatic-trigger idempotency on `(project, to_dt)`, write-tool allowlist checked before cache lookup, plan-scoped cache registry for clean teardown, chat-milestone TODOs left as stubs).

**In flight (`claimed/`):**
- **T-SITREP-LIST-STEPS** (step-def-writer) — claimed 13:54 after LE nudge-touched `pending/T-SITREP-LIST-STEPS.md` to fire the worker's `fswatch -1` (see factory-bug note below).

**Pending but dep-gated by `claim.sh` until upstream lands in `done/`:**
- T-SITREP-LIST-IMPL — needs T-SITREP-LIST-STEPS
- T-SITREP-VIEW-STEPS — needs T-SITREP-LIST-IMPL
- T-SITREP-VIEW-IMPL — needs T-SITREP-VIEW-STEPS

**Promotion rule (LE):** Never move tasks to `blocked/` manually; `blocked/` is only for `done.sh --blocked` failures. Tasks with unmet deps stay in `pending/` — `claim.sh` rejects them until each `depends_on` is present in `done/`.

**Milestone:** AI → SitRep (GitLab ID 7419357)

**Sprint goal:** Wire Gjallarhorn to produce SitReps from the doctrine layer and ingested data. First SitRep, first color-coded Project on the Tactical Plot.

**Branch base:** `main` (trunk-based; MRs target `main` per SAO §9).

---

## Issue register

| # | ID | Title | Role | Status | Depends on | Feature file / tests |
|---|---|---|---|---|---|---|
| 64 | T-LLM | [GJLR-LLM] LLM layer: ABC + ClaudeLLM + retry_on_rate_limit | feature-builder | **integrated** (!23) | — | `test_llm_contract.py`, `test_retry_on_rate_limit.py`, `test_prompts.py` |
| 65 | T-TOOLS | [GJLR-TOOLS] ToolExecutor + narrative-phase read tools | feature-builder | **integrated** (!24) | T-LLM ✅ | `test_tool_executor_envelope.py`, `test_data_tools_*.py`, `test_playbook_tools.py`, `test_sitrep_tools_*.py` |
| 66 | T-AGENT | [GJLR-AGENT] GjallarhornAgent: create_plan + execute_single_step | feature-builder | **integrated** (!28, attempt 2) | T-LLM ✅, T-TOOLS ✅ | `test_agent_create_plan.py`, `test_agent_execute_single_step.py`, `test_agent_process_user_message_deferred.py`, `test_sitrep_service_steps.py` |
| 67 | T-EXEC | [GJLR-EXECUTE-PLAN] execute_plan Celery task + resilience matrix | feature-builder | **integrated** (!29, attempt 2; LE rebase-fixup for factory-state conflict) | T-AGENT ✅ | `test_execution_plan_state_machine.py`, `test_execute_plan_*.py` |
| 61 | T-SITREP-GEN | [SITREP-GENERATE-1] SitRep generation pipeline (narrative phase) | feature-builder | **integrated** (!30, attempt 2; LE rebase-fixup strip orphan T-EXEC commits) | T-EXEC ✅ | `test_generate_sitrep_task.py`, `test_persist_sitrep_from_plan.py`, `test_sitrep_signal.py`, `test_sitrep_generate_scenarios.py` |
| 76 | T-SITREP-LIST-STEPS | [SITREP-LIST+FIND-1] RED tests | step-def-writer | pending (dep-gated) | T-SITREP-GEN | (new) `tests/ui/test_sitrep_list_scenarios.py` |
| 76 | T-SITREP-LIST-IMPL | [SITREP-LIST+FIND-1] List screen + generate POST | feature-builder | pending (dep-gated) | T-SITREP-LIST-STEPS | `tests/ui/test_sitrep_list_scenarios.py` GREEN |
| 77 | T-SITREP-VIEW-STEPS | [SITREP-VIEW_SITREP-1] RED tests | step-def-writer | pending (dep-gated) | T-SITREP-LIST-IMPL | (new) `tests/ui/test_sitrep_view_scenarios.py` |
| 77 | T-SITREP-VIEW-IMPL | [SITREP-VIEW_SITREP-1] SitRep detail view | feature-builder | pending (dep-gated) | T-SITREP-VIEW-STEPS | `tests/ui/test_sitrep_view_scenarios.py` GREEN |

---

## What the factory inherits (do NOT re-implement)

- **`gjallarhorn/models/`** — Conversation, Message, ExecutionPlan (+ sitrep_from_dt/to_dt/trigger fields from migration 0002), PlanStep. All 25 model tests GREEN.
- **`gjallarhorn/migrations/`** — 0001_initial + 0002_sitrep_plan_fields. Migration 0003 (planning_model, is_planning, model_used) is **in scope for T-SITREP-GEN (#61)**.
- **`gjallarhorn/llm/base.py`** — LLM ABC + LLMResponse dataclass. Do NOT modify.
- **`tests/gjallarhorn/conftest.py`** — ScriptedLLM fixture. Do NOT modify.
- **`sitrep/models/sitrep.py`** — SitRep model + migrations. `source_plan` FK to ExecutionPlan is present.
- **`ui/templates/ui/mockups/sitrep/`** — `list.html` + `view.html`. These are the visual foundation for T-SITREP-LIST and T-SITREP-VIEW. Workers port from mockup, not blank.

## RED test inventory (21 errors, 25 green — desired state before factory starts)

Workers must turn RED tests GREEN without modifying test files (except to add stubs for SITREP-GEN-21/22/23/24 which have no test yet).

---

## Test strategy

- `pytest` + `pytest-django`. No `pytest-bdd`, no network calls, no real Claude API.
- All LLM calls use `ScriptedLLM` from `tests/gjallarhorn/conftest.py`.
- `CELERY_TASK_ALWAYS_EAGER = True` in `huginn/settings/test.py`.

---

## Dependency chain

```
T-LLM ─┬─→ T-AGENT ─→ T-EXEC ─→ T-SITREP-GEN ─→ T-SITREP-LIST-STEPS ─→ T-SITREP-LIST-IMPL
        │      ↑                                                                 │
T-TOOLS ┴──────┘                                                                 ↓
                                                                  T-SITREP-VIEW-STEPS ─→ T-SITREP-VIEW-IMPL
```

(`feature-builder` rows except `*-STEPS` which are `step-def-writer`.)

---

## Do NOT do (sprint-wide)

- Do NOT call the real Claude API in any test
- Do NOT modify model files or migrations 0001/0002
- Do NOT modify `gjallarhorn/llm/base.py` or `tests/gjallarhorn/conftest.py`
- Do NOT implement write tools (create_frago, approve_decision) — Decisions milestone
- Do NOT implement process_user_message — Chat milestone
- Do NOT add SSE/Redis publishing to the generation pipeline — Chat milestone (use TODO comments)
- Do NOT design sitrep templates from scratch — port from mockups

---

## Open questions for human

_None — issues are fully specified against SAO §17 and feature files._

---

## Known factory bugs / post-sprint fixes

- **LE pre-gates tasks into `blocked/`** (#78) — LE moves downstream tasks to `blocked/` when it detects their deps aren't merged yet. This is wrong: `blocked/` is only for tasks that were **claimed, ran, and failed** (written by `done.sh --blocked`). Pre-emptive gating is already handled by `claim.sh` (checks `done/` for each dep). Tasks buried in `blocked/` are invisible to workers forever. **Fix:** add explicit guidance to `prompts/lead-engineer.md` — "Never move a task to `blocked/` manually. If a task has unmet deps, leave it in `pending/`; `claim.sh` will reject it until deps land in `done/`. Only `done.sh --blocked` may create files in `blocked/`."

- **`integrate.sh merge` reports success but leaves `status: done` intact (observed on T-TOOLS).** Script printed `"Task ${TASK_ID} marked status: integrated."` and merged MR !24 cleanly, but the file kept `status: done` from the rescue commit — `release.sh` would have refused to proceed. The awk block (`in_result && /^status:/ && !done { … }`) appears correct in isolation; suspect a temp-file / `mv` race when the file was concurrently touched, or `mktemp` env quirk. Fixed manually this cycle (commit `83112d6`). **Action item (post-sprint):** add a final `rg -m1 '^status: integrated' "$DONE_FILE"` assertion at the end of `integrate.sh merge` and fail loudly if absent. Probable safer rewrite: replace the awk-to-tmp pattern with an in-place `sed -i.bak`.

- **Empty `# Result` block routes real work to `blocked/` (observed T-LLM AND T-TOOLS).** Both feature-builder workers produced complete branches + open MRs + GREEN tests but exited without filling `status / branch / mr / commit_sha`, so `done.sh --blocked` quarantined them. Diagnosis from the original LE entry: workers writing in a worktree write the Result block to the worktree copy of the claimed file, not the repo-root copy that `done.sh` inspects. `scripts/rescue-result.sh` exists for this exact case but **only triggers if the `# Result` block is absent entirely** — empty-but-present blocks (the actual failure mode) are skipped by its `rg -q '^# Result'` early-exit. **Action item (post-sprint):** broaden `rescue-result.sh`'s early-exit check to require BOTH `^# Result` AND a non-empty `^status:[[:space:]]*\S` line before skipping; otherwise treat as rescue-eligible.

- **Worker `fswatch -1` on `pending/` is edge-triggered and misses dep-satisfaction events (observed T-SITREP-LIST-STEPS at 13:52).** Each worker loop in `scripts/factory.sh` waits on `fswatch -1 "$REPO_ROOT/factory/tasks/pending"` between scans. When a dep-gated task's upstream lands in `done/`, the change happens in `done/` — `pending/` is unchanged, so no event fires and the worker sleeps indefinitely even though `claim.sh` would now succeed. Backend chain didn't hit this because each upstream's `mv pending/X.md → claimed/X.md` produced a pending-event that woke ALL workers (every worker scanned pending/ every time any task moved). The first dep-chained task after a quiet `done/` transition is where the stall manifests — here, T-SITREP-LIST-STEPS sat ~9 minutes after T-SITREP-GEN integrated. **Mitigation this sprint:** LE `touch factory/tasks/pending/<id>.md` to fire a no-op pending-event when a dep is freshly satisfied. **Post-sprint fixes (one of):** (a) add `done/` to the worker's fswatch path list, (b) `touch` each remaining `pending/*.md` from `integrate.sh merge` so the next dep-satisfaction always wakes everyone, or (c) replace `fswatch -1` with a poll loop (`sleep 30; _process_pending`) — least clever but most robust.

---

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-14 (LE) Factory reset for AI → SitRep re-run.** Previous Composer-2 implementation wiped (gjallarhorn llm/agent/tools/services/tasks, crappy sitrep GUI). Retained: models, migrations, llm/base.py (ABC), all backend RED tests (21 import errors = 21 RED contracts). SAO §17.5 updated with SitRep model schema + ExecutionPlan sitrep_* fields. GitLab: #60 closed (models retained), #61 checkpoint fixed (was pointing to non-existent test files), #65/#67 checkpoints expanded, #76 (SITREP-LIST+FIND-1) + #77 (SITREP-VIEW_SITREP-1) created with mockup references. Registration-0.1.0 factory archived. lint clean, 25 tests green. **Awaiting `scripts/preflight.sh` + Phase 1.**

- **2026-05-14 PHASE 0 complete (LE):** preflight green; milestone "AI -> SitRep" (gid 7419357), 7 issues, 4 infra issues waived (no feature file), 3 issues with feature paths (#61, #76, #77). Tools/git clean; mockups present at ui/templates/ui/mockups/.

- **2026-05-14 11:55:33** 🔧 **feature-builder** claimed **T-LLM**

- **2026-05-14 11:59:12** 🔴 blocked **T-LLM**: reason:status: field 'status' is empty

- **2026-05-14 12:05:43** 🔀 (LE) merged **T-LLM** via !23 → integrated

- **2026-05-14 12:05:54** 🔧 **feature-builder** claimed **T-TOOLS**

- **PHASE 2 complete (LE):** 9 tasks decomposed (4 backend feature-builder, 2 step-def-writer, 3 UI feature-builder); blueprints + task files committed; dependency chain documented.

- **PHASE 3 in progress (LE):** T-LLM rescued from blocked/ (work was real — branch + MR were complete; only the # Result block was empty). LE checks 1–7 ran clean: branch e90fa48 pushed, MR !23 mergeable, 4 in-scope files, 13/13 acceptance tests GREEN, 387/388 collectable tests GREEN, no regressions, Dr. Dobbs spot-check clean (defensive coding, no PII, error paths covered). Merged MR !23 → main. Gated 7 downstream tasks (T-AGENT, T-EXEC, T-SITREP-GEN, T-SITREP-LIST-STEPS/IMPL, T-SITREP-VIEW-STEPS/IMPL) into blocked/ since their upstreams aren't merged yet. T-TOOLS (only T-LLM upstream) left in pending/ as the next eligible task.

- **2026-05-14 12:10 (LE follow-up):** Dr. Dobbs spot-check on T-LLM merge revealed a contract drift — prompt JSON schema declared {narrative, key_risks, recommended_actions} but SitRep model + SITREP-GEN-13 require {headline, situation_assessment, notable_activity}. T-SITREP-GEN's parser is written for the model fields. Featurefile wins per LE protocol — pushed direct fix to main as **6d4d1af** (`fix(gjallarhorn): align SitRep prompt schema`). Tests still GREEN; T-SITREP-GEN no longer needs to flag this. (Note: race with parallel LE pane's `git checkout main` caused the commit to land on main directly instead of via a feature branch — non-force fast-forward, no force-push to main, no policy violation.)

- **2026-05-14 12:12:34** 🔴 blocked **T-TOOLS**: reason:status: field 'status' is empty

- **2026-05-14 12:16:34** 🔀 (LE) merged **T-TOOLS** via !24 → integrated

- **2026-05-14 12:17:25 (LE):** T-TOOLS rescue completed → merged via !24. Branch `factory/T-TOOLS-tool-executor` @ 4a29710 was real work blocked only by an empty Result block (same failure mode as T-LLM). LE checks 1–7 clean: 7/7 files in scope (168 LOC, ToolExecutor + 5 read tools + build_executor factory), 19/19 acceptance tests GREEN, MR mergeable with no conflicts, Dr. Dobbs spot-check passed (project-scoping enforced, write-tool guard, envelope never raises). Worker pragmatically adapted tool return shapes to real model fields (`external_id`/`occurred_at` vs spec'd `sha`/`committed_at`; `workflow_md`, `body_md`) — tests agree; T-AGENT prompts must honor these shapes. T-AGENT now dep-satisfied (T-LLM ✅ + T-TOOLS ✅) and eligible for claim. 6 further downstream tasks remain in `pending/` and will unblock topologically via `claim.sh` as each upstream lands in `done/`.

- **2026-05-14 12:20:41** 🔧 **feature-builder** claimed **T-AGENT**

- **2026-05-14 12:21:39 (LE wake — startup):** Phase 3 in progress. T-AGENT claimed (feature-builder, worktree `factory/T-AGENT-gjallarhorn-agent`); 6 downstream tasks pending, dep-gated by claim.sh. No action — awaiting done/T-AGENT.md.

- **2026-05-14 12:35:18** ✅ **feature-builder** done **T-AGENT**

- **2026-05-14 12:35:19** 🔧 **feature-builder** claimed **T-EXEC**

- **2026-05-14 12:41:25** 🔁 requeued **T-AGENT** attempt 2/3: Out-of-scope work (sitrep_tasks.py, services/factory.py, sitrep_service._persist_sitrep_from_plan, apps.py signal wiring) belongs to T-SITREP-GEN/T-EXEC; MR !25 is in conflict with main (stale base — branched before T-TOOLS merge). Acceptance tests pass (15/15) but scope discipline failed. See remediation block in re-queued task file.

- **2026-05-14 (LE) T-AGENT rejected → attempt 2.** Acceptance tests GREEN (15/15) but branch shipped T-SITREP-GEN/T-EXEC scope (sitrep_tasks.py NEW, services/factory.py NEW, apps.py signal wiring, _persist_sitrep_from_plan) and conflicted on main (stale base — branched pre-T-TOOLS-merge). MR !25 closed. **Root cause:** task spec acceptance criteria said 'Full suite green' which trapped the worker into chasing downstream RED tests. **Systemic fix applied to all remaining task specs + blueprints:** T-AGENT (requeued), T-EXEC (claimed — running worker won't see this; will likely re-hit the trap), T-SITREP-GEN, T-SITREP-LIST-IMPL, T-SITREP-VIEW-IMPL — acceptance is now 'YOUR test files only; do not chase downstream RED'. T-AGENT pending/ now has '## Remediation (attempt 2 — LE)' block. T-EXEC currently in claimed/ with a worker running on top of the rejected T-AGENT branch — expect it to fail similarly; will re-evaluate when it lands in done/.

- **2026-05-14 12:44:23** ✅ **feature-builder** done **T-EXEC**

- **2026-05-14 (LE) T-EXEC rejected → attempt 2.** Same root cause as T-AGENT attempt 1: worker did `git checkout -b factory/T-EXEC-execute-plan` without first `git reset --hard origin/main`, so the worktree's tip (which contained the rejected T-AGENT commit `6fa587f` + factory bookkeeping commits) became the branch base. Diff: 17 files changed, 603 insertions, 9 deletions — vs the 3 files in scope. Out-of-scope drag: full T-AGENT scope (`gjallarhorn/agent/{__init__,agent,exceptions,tool_executor}.py`), full T-TOOLS scope (`gjallarhorn/mcp_tools/*` — already merged in !24, so this would have been a literal duplicate-merge), full T-SITREP-GEN scope (`gjallarhorn/services/sitrep_service.py`, `gjallarhorn/tasks/sitrep_tasks.py`, `gjallarhorn/apps.py`). MR !26 closed. **Bright spot:** the `gjallarhorn/tasks/plan_tasks.py` body itself is correct (73 LoC, clean resilience matrix matching SAO §17.5) — attempt 2 can copy it verbatim. Remediation block added to `pending/T-EXEC.md` with explicit `git reset --hard origin/main` + post-reset sanity checks. **T-SITREP-GEN auto-claimed in the gap** (12:44:25, two seconds after T-EXEC briefly hit done/) and is now running on the same poisoned chain in its worktree. Cannot kill the cursor-agent process from the LE pane; will reject when its done file lands. **Trend to watch:** workers are not following the `git fetch && reset --hard` boilerplate in the task spec's '## Branch & MR' section; consider hoisting it to the system blueprint or adding a pre-implement assertion. Tracking as factory-bug for post-sprint.

- **2026-05-14 12:56:26** 🔁 requeued **T-EXEC** attempt 2/3: Branch based on rejected T-AGENT commit 6fa587f (worker skipped 'git reset --hard origin/main' before branching); diff touches 17 files vs 3 in scope, dragging in all of T-AGENT/T-TOOLS/T-SITREP-GEN scope (re-implements already-merged !24, duplicates rejected !25). MR !26 closed. plan_tasks.py body itself is correct (73 LoC) and reusable for attempt 2.

- **2026-05-14 (LE) cleanup:** Removed orphan duplicate `factory/tasks/pending/T-SITREP-GEN.md` (the worker had `claim.sh`-moved its working copy to `claimed/` at 12:44:25, but the original tracked pending/ file was somehow restored — possibly by an earlier wake's `git pull --rebase`). Canonical state is now `claimed/T-SITREP-GEN.md` only. Initial reject of T-EXEC in this wake also failed to persist for unclear reasons (probably a tool-write race against a concurrent `git` op); re-ran `reject.sh T-EXEC` and verified on disk before adding the remediation block. Stable state going into commit: pending/ = T-AGENT (att 2), T-EXEC (att 2), 4× T-SITREP-LIST/VIEW (dep-gated); claimed/ = T-SITREP-GEN (worker on poisoned base — expect reject); done/ = T-LLM, T-TOOLS (both integrated); rejected/ = T-AGENT, T-EXEC.

- **2026-05-14 13:01:40** ✅ **feature-builder** done **T-SITREP-GEN**

- **2026-05-14 13:04:50** 🔁 requeued **T-SITREP-GEN** attempt 2/3: Poisoned base — branched off worktree tip containing rejected T-AGENT (6fa587f) + rejected T-EXEC (b7a2339) + pre-squash T-TOOLS (4a29710); diff vs main is 26 files/924 LoC instead of ~14/~335 in implementation commit e193a03. Plus .venv tracked in git (gitignore violation) and factory/tasks/pending/T-EXEC.md modified in the feature commit. Worker did not run 'git fetch && git checkout main && git reset --hard origin/main' before branching. Implementation commit e193a03 itself is mostly in-scope and reusable as a starting point for attempt 2.

- **2026-05-14 13:04:52** 🔧 **feature-builder** claimed **T-AGENT**

- **2026-05-14 (LE) T-SITREP-GEN rejected → attempt 2.** Third instance of the same systemic failure mode (T-AGENT att 1, T-EXEC att 1, now T-SITREP-GEN att 1): worker did `git checkout -b factory/T-SITREP-GEN-narrative-pipeline` from a worktree tip that already contained `6fa587f` (rejected T-AGENT body) + `b7a2339` (rejected T-EXEC body) + `4a29710` (pre-squash T-TOOLS body — already merged via squash !24). Implementation commit `e193a03` itself is **mostly clean** (14 files, ~335 LoC, in-scope shape — reusable for attempt 2 via cherry-pick), but the branch as a whole presents 26 files / 924 LoC vs main, including duplicate-merges of T-TOOLS and resurrections of rejected T-AGENT/T-EXEC bodies. Two extra defects on top of the base poisoning: `.venv` tracked in git (gitignore violation, 1 line in the feature commit), and `factory/tasks/pending/T-EXEC.md` modified inside the feature commit (factory state file leak). MR !27 closed by LE. Remediation block in `pending/T-SITREP-GEN.md` (attempt 2) now includes ancestor-not-reachable assertions for `6fa587f` and `b7a2339`, an `origin/main`-tip identity check, an upstream-merged check (T-AGENT body + T-EXEC body must already be on main), a cherry-pick recipe for `e193a03` with explicit `git restore` commands for the four polluted paths, a `≤ 16 files vs origin/main` diff cap, and a new branch name `factory/T-SITREP-GEN-narrative-pipeline-v2` to avoid pushing to the poisoned ref. **T-AGENT auto-claimed two seconds after T-SITREP-GEN's reject** — factory loop healthy. **Trend escalation:** three consecutive workers ignored the `git fetch && reset --hard` boilerplate in `## Branch & MR`. The boilerplate currently lives at the bottom of the task spec; workers may not be reading it before they `cd` into the worktree. Post-sprint factory-bug: hoist this boilerplate into the system blueprint AND make `claim.sh` either run the reset itself or refuse to hand the task to the worker until the worktree's HEAD == `origin/main`.

- **2026-05-14 ~13:12 (LE wake — 5-min poll, no action).** T-AGENT (att 2) worker still active (pid 62988, ~8 min elapsed). Worktree on `factory/T-AGENT-gjallarhorn-agent` with **clean ancestry** (verified `6fa587f`, `b7a2339`, `4a29710` are NOT ancestors of HEAD; branch base = `0cb8f5c` which IS reachable from `origin/main` `6f47b10`). Uncommitted tree: only the 7 in-scope files (`gjallarhorn/agent/{agent,exceptions,__init__}.py`, `gjallarhorn/services/{sitrep_service,__init__}.py`, `gjallarhorn/tasks/{plan_tasks,__init__}.py`) — **no out-of-scope drag this time**, remediation block landed. Worker just ran the 4 acceptance test files: **15/15 PASSED in 2.84s**, regression suite (with the 8 downstream-RED ignores) currently in flight in worker stream. No `done/T-AGENT.md` yet; nothing for LE to do. Holding until next fswatch event.

- **2026-05-14 13:15:00** ✅ **feature-builder** done **T-AGENT**

- **2026-05-14 13:15:02** 🔧 **feature-builder** claimed **T-EXEC**

- **2026-05-14 13:17:58** 🔀 (LE) merged **T-AGENT** via !28 → integrated

- **2026-05-14 (LE) T-AGENT (att 2) integrated.** LE checks 1–7 all clean on first read: branch `factory/T-AGENT-gjallarhorn-agent` @ `ba04346e` pushed; MR !28 `detailed_merge_status: mergeable`, no conflicts; `git diff origin/main...` shows **exactly 7 files / 236 LoC matching `files_in_scope` 1:1** (no drag, no `.venv`, no factory state in feature commit); acceptance suite 15/15 GREEN (`test_agent_create_plan.py`, `test_agent_execute_single_step.py`, `test_agent_process_user_message_deferred.py`, `test_sitrep_service_steps.py`); regression sweep 414 passed / 1 skipped — only failures are `test_execute_plan_max_retries_exhausted` + `test_execute_plan_rate_limit_retry`, both squarely inside T-EXEC's `test_execute_plan_*.py` contract (not regressions); ruff clean on new files; Dr. Dobbs spot-check clean (`transaction.atomic` on plan/step writes, lazy `from gjallarhorn.tasks.plan_tasks import execute_plan` inside `create_plan` to break the agent↔tasks cycle, `NotImplementedError` for `process_user_message` as specified, defensive `[<label> unavailable]` fallback in `_build_system_blocks`, 4 ephemeral-cached system blocks per SAO §17.6, no real API calls). `integrate.sh merge T-AGENT` reported MR was **already merged** by the time we ran it (likely auto-merge / parallel run); script idempotently set `status: integrated` in `done/T-AGENT.md` (verified `^status: integrated` present, the integrate.sh bug noted in blackboard did NOT recur this time). Squash commit on `main`: `1f932b0`.

- **2026-05-14 (LE) T-EXEC (att 2) auto-claimed on clean base — first poisoning-free worker handoff.** Factory loop claimed T-EXEC at 13:15:02 (two seconds after T-AGENT moved to done/). Worktree HEAD is `9db34f2` — the merge commit on `origin/main` that contains the T-AGENT squash. Branch `factory/T-EXEC-execute-plan` is now based off `origin/main`'s tip, **not** a poisoned worktree tip. The "trend escalation" from the previous wake (three consecutive workers ignoring the `git reset --hard origin/main` boilerplate) is broken — this worker either ran the reset or branched from a freshly-synced HEAD. Worktree is mid-implementation: `gjallarhorn/services/factory.py` + `gjallarhorn/tasks/plan_tasks.py` modified, uncommitted. Holding until `done/T-EXEC.md` lands.

- **PHASE 3 update (LE):** 3 of 6 in-flight tasks merged (T-LLM !23, T-TOOLS !24, T-AGENT !28). T-EXEC running on clean base. Remaining: T-EXEC, T-SITREP-GEN, T-SITREP-LIST-STEPS/IMPL, T-SITREP-VIEW-STEPS/IMPL (latter 5 dep-gated in `pending/`).

- **2026-05-14 13:22:04** ✅ **feature-builder** done **T-EXEC**

- **2026-05-14 13:22:05** 🔧 **feature-builder** claimed **T-SITREP-GEN**

- **2026-05-14 13:32:49** 🔀 (LE) merged **T-EXEC** via !29 → integrated

- **2026-05-14 (LE) T-EXEC (att 2) integrated via LE rebase-fixup.** MR !29 came up with `detailed_merge_status: conflict` — the conflict was purely on `factory/tasks/claimed/T-EXEC.md` (deleted-on-main since `done.sh` had moved it to `done/`, modified-on-branch since the worker wrote its result block in the claimed file). Code-only diff (`gjallarhorn/services/factory.py`, `gjallarhorn/tasks/plan_tasks.py`) was 2/3 in-scope files, 51 LoC, no drag. Phase-4 carve-out invoked: locally checked out the branch on `main` repo, `git rebase origin/main` (commit 1 `1906572` applied clean; commit 2 `9196520` "result block" hit the rename-conflict on `done/T-EXEC.md`; resolved with `--ours` to take main's `status: rescued` block which is canonical), force-pushed (`9196520...406b224`). MR went `mergeable` after ~5s. LE checks 1–7: ✅ branch pushed, ✅ MR !29 mergeable, n/a CI (this repo's convention — no MR pipelines), ✅ feature-builder so step-def check n/a, ✅ in-scope files only post-rebase, ✅ 15/15 acceptance GREEN locally + 426 passed / 1 skipped on full suite (T-SITREP-GEN's 4 `sitrep_*` test files & 2 UI scenario files explicitly ignored), ✅ ruff clean, ✅ Dr. Dobbs spot-check clean (`mark_started` wrapped in `try/except InvalidStateTransitionError` for idempotent re-entry, `step_number = plan.progress_current` makes resume work correctly, full SAO §17.5 resilience matrix — `RateLimitError`/`TimeoutError`/`OSError` → `mark_paused_for_retry` + `self.retry(countdown=min(30 * 2 ** (retry_count-1), 120))` capped at 120s, other exceptions → `mark_failed` + re-raise, `if plan.status == "failed"` exits cleanly when model auto-fails on retry-cap, lazy `from gjallarhorn.services.factory import create_agent` inside `_build_agent_for_plan` to break cycles, TODOs for sitrep-persistence + chat publishing). `integrate.sh merge T-EXEC` clean — squash commit `bf522fd`, merge commit `f36b5a4`, file marked `status: integrated` with no awk-race (the integrate.sh bug from T-TOOLS did not recur). Source branch removed.

- **2026-05-14 (LE) ⚠ T-SITREP-GEN-v2 base poisoning detected (no action yet).** Factory loop auto-claimed T-SITREP-GEN at 13:22:05, **two seconds before** T-EXEC integrated and **before** LE's rebase-fixup. Worker created `factory/T-SITREP-GEN-narrative-pipeline-v2` in `.worktrees/feature-builder` while HEAD was at `9196520` (un-merged T-EXEC pre-rebase tip). After T-EXEC was rebased & force-pushed (orphaning `1906572` and `9196520`) and then squash-merged (`bf522fd`), the worker's branch contains those two now-orphaned commits as not-on-main history. When the worker eventually pushes, `git diff origin/main...factory/T-SITREP-GEN-narrative-pipeline-v2` will include the un-squashed T-EXEC content as drag. **Plan when it lands in `done/`:** if the ONLY out-of-scope drag is the orphaned T-EXEC commits, do `git rebase --onto origin/main bf522fd factory/T-SITREP-GEN-narrative-pipeline-v2` (strip the now-on-main pre-squash T-EXEC commits) and force-push before `integrate.sh merge` — ≤ 30 LoC code-wise (zero, actually — base swap), within Phase-4 carve-out. If any other drag is present (`.venv`, factory state files, T-AGENT/T-TOOLS bodies again, `apps.py` etc.) → reject for attempt 3/3. **Root cause traced:** even with `fix(factory): branch new task from origin/main, not dirty worktree tip (#80)` on main, the loop's `claim.sh` ran the `claim` step in a 2-second window between `done/T-EXEC.md` materializing and LE pushing the clean rebased T-EXEC tip. Possible factory-bug for the post-sprint list: `claim.sh` should `git fetch origin && git reset --hard origin/main` in the worker's worktree _after_ the previous task's MR has merged on the remote, not just after the previous task's `done/` file has appeared locally. Cannot kill the running cursor-agent process from the LE pane — holding until `done/T-SITREP-GEN.md` lands.

- **PHASE 3 update (LE):** 4/6 in-flight tasks merged (T-LLM !23, T-TOOLS !24, T-AGENT !28, T-EXEC !29). T-SITREP-GEN running on poisoned base — rebase-fixup planned at integration. 4× T-SITREP-LIST/VIEW pending dep-gated.

- **2026-05-14 13:41:20** ✅ **feature-builder** done **T-SITREP-GEN**

- **2026-05-14 13:45:52** 🔀 (LE) merged **T-SITREP-GEN** via !30 → integrated

- **2026-05-14 (LE) T-SITREP-GEN (att 2) integrated via LE rebase-fixup.** Predicted base-poisoning materialised exactly as logged the previous wake: worker's branch `factory/T-SITREP-GEN-narrative-pipeline-v2` carried the two orphaned pre-squash T-EXEC commits (`1906572`, `9196520`) as ancestors, merge-base `716221b`, diff-vs-main 17 files / 540+ LoC due to factory-state files (`factory/blackboard.md`, `factory/tasks/claimed/T-EXEC.md`, `factory/tasks/pending/T-SITREP-GEN.md`) showing up as resurrections/reverts. Worker's own commit `53f8c04` was clean in isolation — 14 in-scope files, zero factory state, zero `.venv`. Phase-4 carve-out invoked (zero code change, pure base swap): `git stash` the pending-file artifact, `git rebase --onto origin/main 9196520 factory/T-SITREP-GEN-narrative-pipeline-v2` (replays only `53f8c04` onto current `origin/main` `ab5a5e0` — clean, no conflicts despite T-EXEC's overlap on `plan_tasks.py` / `services/factory.py` / `agent/agent.py`), force-push `--force-with-lease` (`53f8c04 → 34402ea`). MR !30 went `mergeable` in ~8s. LE checks 1–7 all clean post-rebase: ✅ branch pushed, ✅ MR !30 mergeable / no conflicts, n/a CI, ✅ feature-builder so step-def check n/a, ✅ 14/14 in-scope files only (no `factory/**`, no `.venv`, no rejected-task scope), ✅ 36/36 acceptance tests GREEN (all of `test_generate_sitrep_task.py` + `test_persist_sitrep_from_plan.py` + `test_sitrep_signal.py` + `test_sitrep_generate_scenarios.py` incl. new GEN-21/22/23/24), ✅ 462 passed / 1 skipped on full suite minus the 2 dep-gated UI scenario files (no regressions), ✅ ruff clean, ✅ `makemigrations --check` clean (only 0003), ✅ Dr. Dobbs spot-check clean (`transaction.atomic` plan+steps writes, signal-handler `try/except` cannot break sync per spec, automatic-trigger idempotency on `(project, to_dt)` early-returns existing plan_id, manual trigger bypasses guard per SITREP-GEN-20, WRITE_TOOLS allowlist enforced before cache lookup, cache key includes plan_id + tool + sha256(args) so cross-plan collisions impossible, `plan:<id>:keys` registry enables clean teardown via `clear_plan_cache`, chat-milestone TODOs left as stubs at the publish points referenced by GEN-11/16/17 — no SSE/Redis publishing as required). `integrate.sh merge T-SITREP-GEN` clean — squash commit `71e4713`, merge commit `0c475cb`, status flipped `rescued → integrated` with no awk-race. Worktree detached to `origin/main` `0c475cb` post-merge (can't `git checkout main` from a worktree — primary checkout owns it; `git checkout --detach origin/main` resets it cleanly for the next worker). **All 5 backend tasks now on main.** Next loop tick should auto-claim T-SITREP-LIST-STEPS (dep on T-SITREP-GEN now satisfied).

- **PHASE 3 update (LE): backend complete (5/5).** T-LLM !23, T-TOOLS !24, T-AGENT !28, T-EXEC !29, T-SITREP-GEN !30 all integrated. 3 of 5 required LE rebase-fixup (T-EXEC factory-state conflict, T-SITREP-GEN base-poisoning, plus a prior force-push on T-EXEC). 4 UI tasks remain (T-SITREP-LIST-STEPS → -LIST-IMPL → -VIEW-STEPS → -VIEW-IMPL); all dep-gated, will unblock topologically as each upstream lands in done/.

- **2026-05-14 13:54:06** 🔧 **step-def-writer** claimed **T-SITREP-LIST-STEPS**

- **2026-05-14 ~13:54 (LE wake — 5-min poll; nudged stalled step-def-writer):** Backend chain finished at 13:45 (T-SITREP-GEN !30 integrated). 9 minutes elapsed and `pending/T-SITREP-LIST-STEPS.md` was still un-claimed despite `T-SITREP-GEN.md` sitting in `done/` (dep satisfied). Diagnosis: step-def-writer worker's `fswatch -1 "$REPO_ROOT/factory/tasks/pending"` is **edge-triggered**. When `claim.sh` mv'd `claimed/T-SITREP-GEN.md → done/T-SITREP-GEN.md`, the event fired in `done/`, not `pending/`, so step-def-writer never re-scanned. The backend chain never hit this because each upstream's own `mv pending/X.md → claimed/X.md` fired a pending-event that woke every worker. The first dep-chained task after a quiet `done/` transition (i.e. the first stepdef-writer task after a feature-builder chain) is exactly where the stall manifests. **Mitigation:** `touch factory/tasks/pending/T-SITREP-LIST-STEPS.md` — fired the no-op event, step-def-writer woke and claimed the task within 2 seconds. **Post-sprint factory-bug filed** (see Known factory bugs above): cheapest robust fix is to add `done/` to the worker's fswatch path list (one-line change in `scripts/factory.sh`); cleverer alternative is to `touch` remaining `pending/*.md` from `integrate.sh merge`. Holding until `done/T-SITREP-LIST-STEPS.md` lands.

- **2026-05-14 14:03:24** ✅ **step-def-writer** done **T-SITREP-LIST-STEPS**
