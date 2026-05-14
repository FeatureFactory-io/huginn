# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 0 — Preflight pending. Factory reset for AI → SitRep re-run. Previous crappy Composer-2 implementation wiped; models/migrations/RED tests retained as foundation. Ready for `scripts/preflight.sh "AI -> SitRep"` then Phase 1.

**Milestone:** AI → SitRep (GitLab IID to confirm via `glab milestone list`)

**Sprint goal:** Wire Gjallarhorn to produce SitReps from the doctrine layer and ingested data. First SitRep, first color-coded Project on the Tactical Plot.

**Branch base:** `main` (trunk-based; MRs target `main` per SAO §9).

---

## Issue register

| # | ID | Title | Role | Status | Depends on | Feature file / tests |
|---|---|---|---|---|---|---|
| 64 | T-LLM | [GJLR-LLM] LLM layer: ABC + ClaudeLLM + retry_on_rate_limit | feature-builder | pending | — (models retained) | `test_llm_contract.py`, `test_retry_on_rate_limit.py` |
| 65 | T-TOOLS | [GJLR-TOOLS] ToolExecutor + narrative-phase read tools | feature-builder | pending | #64 | `test_tool_executor_envelope.py`, `test_data_tools_*.py`, `test_*_tools_*.py` |
| 66 | T-AGENT | [GJLR-AGENT] GjallarhornAgent: create_plan + execute_single_step | feature-builder | pending | #64, #65 | `test_agent_create_plan.py`, `test_agent_execute_single_step.py` |
| 67 | T-EXEC | [GJLR-EXECUTE-PLAN] execute_plan Celery task + resilience matrix | feature-builder | pending | #66 | `test_execute_plan_*.py`, `test_execution_plan_state_machine.py` |
| 61 | T-SITREP-GEN | [SITREP-GENERATE-1] SitRep generation pipeline (narrative phase) | feature-builder | pending | #67 | `test_sitrep_generate_scenarios.py`, `test_generate_sitrep_task.py`, `test_persist_sitrep_from_plan.py`, `test_sitrep_service_steps.py`, `test_sitrep_signal.py` |
| 76 | T-SITREP-LIST | [SITREP-LIST+FIND-1] SitRep list + generate endpoint | feature-builder | pending | #61 | `tests/ui/test_sitrep_list_scenarios.py` (to be written as step-def-writer task) |
| 77 | T-SITREP-VIEW | [SITREP-VIEW_SITREP-1] SitRep detail view | feature-builder | pending | #76 | `tests/ui/test_sitrep_view_scenarios.py` (to be written as step-def-writer task) |

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
#64 (LLM) → #65 (Tools) → #66 (Agent) → #67 (execute_plan) → #61 (SitRep gen) → #76 (List) → #77 (View)
```

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

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-14 (LE) Factory reset for AI → SitRep re-run.** Previous Composer-2 implementation wiped (gjallarhorn llm/agent/tools/services/tasks, crappy sitrep GUI). Retained: models, migrations, llm/base.py (ABC), all backend RED tests (21 import errors = 21 RED contracts). SAO §17.5 updated with SitRep model schema + ExecutionPlan sitrep_* fields. GitLab: #60 closed (models retained), #61 checkpoint fixed (was pointing to non-existent test files), #65/#67 checkpoints expanded, #76 (SITREP-LIST+FIND-1) + #77 (SITREP-VIEW_SITREP-1) created with mockup references. Registration-0.1.0 factory archived. lint clean, 25 tests green. **Awaiting `scripts/preflight.sh` + Phase 1.**
