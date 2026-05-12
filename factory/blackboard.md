# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 1 — Ingestion complete; awaiting human review before Phase 2 decomposition.

**Milestone:** AI → SitRep (GitLab IID 4, internal id 7419357)

**Sprint goal:** Implement the Gjallarhorn AI runtime (models → LLM layer → ToolExecutor → Agent → Celery tasks) and wire it to the SitRep generation pipeline, so every successful ingestion sync produces a SitRep narrative in the database, accessible via the production list and view screens.

**Branch base:** `features/gjallarhorn`

**Integration branch (to be created Phase 4):** `integration/ai-sitrep`

---

## Issue register

| # | ID | Title | Status | Depends on | Feature file |
|---|---|---|---|---|---|
| 60 | GJLR-MODELS | Models + migrations (SitRep, Conversation, ExecutionPlan, PlanStep) | open | — | — |
| 64 | GJLR-LLM | LLM layer: ABC + ClaudeLLM + retry_on_rate_limit | open | #60 | — |
| 65 | GJLR-TOOLS | ToolExecutor + narrative-phase read tools | open | #60, #64 | — |
| 66 | GJLR-AGENT | GjallarhornAgent: create_plan + execute_single_step | open | #65 | — |
| 67 | GJLR-EXECUTE-PLAN | execute_plan Celery task + resilience matrix | open | #66 | — |
| 61 | SITREP-GENERATE-1 | SitRep generation pipeline | open | #67, #66 | `docs/features/act-5-sitrep/sitrep-generate.feature` |
| 62 | SITREP-LIST+FIND-1 | SitRep list and find — production view | open | #61 | `docs/features/act-5-sitrep/sitrep-list-find.feature` |
| 63 | SITREP-VIEW_SITREP-1 | SitRep view — production view (narrative phase) | open | #61 | `docs/features/act-5-sitrep/sitrep-view.feature` |

**Dependency chain:** `#60 → #64 → #65 → #66 → #67 → #61 → #62 + #63`

---

## Test strategy

- All backend integration tests use **`ScriptedLLM`** (defined in `tests/gjallarhorn/conftest.py`, introduced in #64) — never the real Claude API.
- Celery runs in **eager mode** (`CELERY_TASK_ALWAYS_EAGER = True` in `huginn/settings/test.py`).
- Tests seed real DB rows via ORM / `factory_boy`; no fixtures files.
- Tests for #62 and #63 are Django test client integration tests (no Selenium).
- Real API calls (`@pytest.mark.requires_llm_api`) are opt-in and excluded from CI.

---

## Blocked / risks

- `ANTHROPIC_API_KEY` must be present in `.env` for `ClaudeLLM` to instantiate; `ImproperlyConfigured` raised otherwise. CI must inject it as a secret (or use `ScriptedLLM` only path).
- SSE / Redis publish stubs are `# TODO(chat-milestone)` throughout — do NOT implement them in this sprint.
- Write tools (`create_frago`, `extend_sitawareness`, `create_jira_issue`) are `# TODO(decisions-milestone)` — blocked from narrative phase.
- `process_user_message` on `GjallarhornAgent` must `raise NotImplementedError` — confirmed by test in #66.

---

## Open questions for human

_None currently — sprint plan is clear._

---

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-12** Phase 1 ingestion complete. Read milestone IID 4 (8 issues: #60–67). Read `docs/features/act-5-sitrep/*.feature` (3 files, 468 scenarios total). Read `docs/architecture/SAO.md §17` (Gjallarhorn AI architecture, all sub-sections). Wrote `factory/blueprints/system.md` and updated this blackboard. Awaiting human review before Phase 2 decomposition.
