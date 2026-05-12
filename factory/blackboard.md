# Blackboard — factory current state

<!-- LE edits this section in place -->

**Phase:** 3 — Execution (Batch 3: Sonnet 4.5 — UI views)

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

- ~~`ANTHROPIC_API_KEY`~~ — **resolved**: confirmed present in `.env`.
- SSE / Redis publish stubs are `# TODO(chat-milestone)` throughout — do NOT implement them in this sprint.
- Write tools (`create_frago`, `extend_sitawareness`, `create_jira_issue`) are `# TODO(decisions-milestone)` — blocked from narrative phase.
- `process_user_message` on `GjallarhornAgent` must `raise NotImplementedError` — confirmed by test in #66.

---

## Open questions for human

_None._

---

# Event log

<!-- Append-only: LE and workers add dated lines -->
- **2026-05-12 12:52** ✅ **Batch 1 COMPLETE** (Sonnet 4.5). All 7 tasks done:
  - Backend chain: T-60 (MR !5), T-64 (MR !6), T-65a (MR !7), T-65b (MR !8)
  - Step-defs: T-61-steps (MR !9, 20 RED), T-62-steps (MR !10, 19 RED), T-63-steps (MR !11, 31 RED)
  - Total: 5 models, LLM layer, ToolExecutor, 5 tools, 70 RED test stubs
  - All existing tests pass (388 passed)
- **2026-05-12** Phase 3 Batch 3 started (Sonnet 4.5). All backend tasks done (T-60, T-64, T-65a, T-65b, T-66, T-67, T-61-impl). Unblocked: T-62-impl (22 stubs, sitrep list view) + T-63-impl (31 stubs, sitrep detail view). Running factory.sh mini-sprint.
- **2026-05-12** Phase 3 Batch 1 started (Sonnet 4.5). Executing: T-60 → T-64 → T-65a → T-65b (sequential chain) + T-61-steps, T-62-steps, T-63-steps (parallel, no code deps). Batch 2 (Sonnet 4.6 thinking): T-66 → T-67 → T-61-impl. Batch 3 (Sonnet 4.5): T-62-impl, T-63-impl.
- **2026-05-12** Phase 2 decomposition started. Human confirmed ANTHROPIC_API_KEY present. Task register:
  - **pending**: T-60, T-61-steps, T-62-steps, T-63-steps
  - **blocked**: T-64 (→T-60), T-65a (→T-64), T-65b (→T-65a), T-66 (→T-65b), T-67 (→T-66), T-61-impl (→T-67+T-61-steps), T-62-impl (→T-61-impl+T-62-steps), T-63-impl (→T-61-impl+T-63-steps)
- **2026-05-12** Phase 1 ingestion complete. Read milestone IID 4 (8 issues: #60–67). Read `docs/features/act-5-sitrep/*.feature` (3 files, 468 scenarios total). Read `docs/architecture/SAO.md §17` (Gjallarhorn AI architecture, all sub-sections). Wrote `factory/blueprints/system.md` and updated this blackboard. Awaiting human review before Phase 2 decomposition.
