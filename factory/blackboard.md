# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 3 — Execution in progress. T-LLM merged (!23 → main). T-TOOLS now eligible (only upstream was T-LLM); 7 downstream tasks gated in `blocked/` until their upstreams complete.

**Eligible now (`pending/`):** T-TOOLS (feature-builder; depends_on: T-LLM ✅).

**Gated (`blocked/`, awaiting upstream):**
- T-AGENT — needs T-TOOLS
- T-EXEC — needs T-AGENT
- T-SITREP-GEN — needs T-EXEC
- T-SITREP-LIST-STEPS — needs T-SITREP-GEN
- T-SITREP-LIST-IMPL — needs T-SITREP-LIST-STEPS
- T-SITREP-VIEW-STEPS — needs T-SITREP-LIST-IMPL
- T-SITREP-VIEW-IMPL — needs T-SITREP-VIEW-STEPS

**Promotion rule (LE):** when each `done/T-X.md` reaches `status: integrated`, move every `blocked/T-Y.md` whose `depends_on` is now fully satisfied → `pending/`.

**Milestone:** AI → SitRep (GitLab ID 7419357)

**Sprint goal:** Wire Gjallarhorn to produce SitReps from the doctrine layer and ingested data. First SitRep, first color-coded Project on the Tactical Plot.

**Branch base:** `main` (trunk-based; MRs target `main` per SAO §9).

---

## Issue register

| # | ID | Title | Role | Status | Depends on | Feature file / tests |
|---|---|---|---|---|---|---|
| 64 | T-LLM | [GJLR-LLM] LLM layer: ABC + ClaudeLLM + retry_on_rate_limit | feature-builder | **integrated** (!23) | — | `test_llm_contract.py`, `test_retry_on_rate_limit.py`, `test_prompts.py` |
| 65 | T-TOOLS | [GJLR-TOOLS] ToolExecutor + narrative-phase read tools | feature-builder | **pending (eligible)** | T-LLM ✅ | `test_tool_executor_envelope.py`, `test_data_tools_*.py`, `test_playbook_tools.py`, `test_sitrep_tools_*.py` |
| 66 | T-AGENT | [GJLR-AGENT] GjallarhornAgent: create_plan + execute_single_step | feature-builder | blocked | T-LLM ✅, T-TOOLS | `test_agent_create_plan.py`, `test_agent_execute_single_step.py`, `test_agent_process_user_message_deferred.py`, `test_sitrep_service_steps.py` |
| 67 | T-EXEC | [GJLR-EXECUTE-PLAN] execute_plan Celery task + resilience matrix | feature-builder | blocked | T-AGENT | `test_execution_plan_state_machine.py`, `test_execute_plan_*.py` |
| 61 | T-SITREP-GEN | [SITREP-GENERATE-1] SitRep generation pipeline (narrative phase) | feature-builder | blocked | T-EXEC | `test_generate_sitrep_task.py`, `test_persist_sitrep_from_plan.py`, `test_sitrep_signal.py`, `test_sitrep_generate_scenarios.py` |
| 76 | T-SITREP-LIST-STEPS | [SITREP-LIST+FIND-1] RED tests | step-def-writer | blocked | T-SITREP-GEN | (new) `tests/ui/test_sitrep_list_scenarios.py` |
| 76 | T-SITREP-LIST-IMPL | [SITREP-LIST+FIND-1] List screen + generate POST | feature-builder | blocked | T-SITREP-LIST-STEPS | `tests/ui/test_sitrep_list_scenarios.py` GREEN |
| 77 | T-SITREP-VIEW-STEPS | [SITREP-VIEW_SITREP-1] RED tests | step-def-writer | blocked | T-SITREP-LIST-IMPL | (new) `tests/ui/test_sitrep_view_scenarios.py` |
| 77 | T-SITREP-VIEW-IMPL | [SITREP-VIEW_SITREP-1] SitRep detail view | feature-builder | blocked | T-SITREP-VIEW-STEPS | `tests/ui/test_sitrep_view_scenarios.py` GREEN |

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

- **LE pre-gates tasks into `blocked/`** — LE moves downstream tasks to `blocked/` when it detects their deps aren't merged yet. This is wrong: `blocked/` is only for tasks that were **claimed, ran, and failed** (written by `done.sh --blocked`). Pre-emptive gating is already handled by `claim.sh` (checks `done/` for each dep). Tasks buried in `blocked/` are invisible to workers forever. **Fix:** add explicit guidance to `prompts/lead-engineer.md` — "Never move a task to `blocked/` manually. If a task has unmet deps, leave it in `pending/`; `claim.sh` will reject it until deps land in `done/`. Only `done.sh --blocked` may create files in `blocked/`."

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
