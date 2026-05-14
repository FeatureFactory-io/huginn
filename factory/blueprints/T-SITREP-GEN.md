# Blueprint: T-SITREP-GEN — SitRep generation pipeline (narrative phase)

**Issue:** [#61](https://gitlab.com/dp2580/huginn/-/issues/61) — SITREP-GENERATE-1
**Task:** [`factory/tasks/pending/T-SITREP-GEN.md`](../tasks/pending/T-SITREP-GEN.md)
**Feature file:** [`docs/features/act-5-sitrep/sitrep-generate.feature`](../../docs/features/act-5-sitrep/sitrep-generate.feature) (SITREP-GEN-01 … SITREP-GEN-24)

## Goal

Wire the end-to-end SitRep narrative pipeline:

1. `ingestion.sync_project` success emits `sync_project_completed` signal.
2. A receiver in `gjallarhorn.apps.ready()` enqueues
   `generate_sitrep_for_project.delay(...)` with computed `from_dt` / `to_dt`.
3. `generate_sitrep_for_project` creates `Conversation` + `ExecutionPlan` + 5
   `PlanStep`s and delegates to `Agent.create_plan` (which enqueues T-EXEC's
   `execute_plan`).
4. On plan completion, `_persist_sitrep_from_plan(plan)` reads the final
   step's `result` JSON, looks up FRAGOs active at `to_dt`, and writes one
   `SitRep` row (M2M FRAGOs attached, `source_plan` linked).
5. Manual trigger: `POST /sitrep/<project_slug>/generate/` enqueues with
   `trigger='manual'` and returns 302 → list with `?generated=1`.

Migration **0003** adds `planning_model` to `ExecutionPlan` + `is_planning` and
`model_used` to `PlanStep` (SAO §17.5).

## Context

- All the LLM/Agent/Tools/execute_plan plumbing is in place after T-EXEC.
  T-SITREP-GEN sits **on top** and wires the auto-trigger + plan-completion
  side effects.
- Issue #61 has the full implementation plan (§A–K) with code stubs verbatim.
- Add SITREP-GEN-21/22/23/24 tests **only if not already present** in
  `tests/gjallarhorn/test_sitrep_generate_scenarios.py` — they cover model
  assignment (Opus vs Sonnet) and intra-plan tool-result cache. The
  blackboard notes these as "no test yet" so workers may write them.
- For the **model-assignment** scenarios (SITREP-GEN-21/22): add two
  module-level constants in `gjallarhorn/services/factory.py`:
  - `PLANNING_MODEL = "claude-opus-4-5"`
  - `EXECUTION_MODEL = "claude-sonnet-4-6"`
  Wire `Agent.create_plan` to stamp `plan.planning_model = PLANNING_MODEL` and
  to set each step's `is_planning` flag (final "Compose SitRep narrative"
  step → `True`). `execute_single_step` writes `step.model_used` from the
  `LLMResponse.model` field after each call (or from constants in test paths).
- For SITREP-GEN-23/24 (**intra-plan tool-result cache**): add a Redis
  pass-through cache to `ToolExecutor.execute()`. Use Django `cache` interface
  (sane fallback to dummy cache in tests). Key pattern from SAO §17.6:
  `plan:{plan_id}:tool:{tool_name}:{sha256(canonical_json(args))}`. Wire
  `plan_id` into `ToolExecutor` (constructor or per-call context). The cache
  scopes to **read-only** tools. Delete `plan:{plan_id}:tool:*` keys on
  `plan.mark_completed()` and `plan.mark_failed()`.

## Files touched

| File | Change |
|---|---|
| `ingestion/signals.py` | NEW — `sync_project_completed = Signal()`. |
| `ingestion/tasks.py` | extend `sync_project()` body to `sync_project_completed.send(sender=Project, project_id=..., completed_at=timezone.now())` on success. |
| `gjallarhorn/migrations/0003_sitrep_model_fields.py` | NEW — adds `ExecutionPlan.planning_model`, `PlanStep.is_planning`, `PlanStep.model_used`. |
| `gjallarhorn/models/execution_plan.py` | add `planning_model = CharField(blank=True)` field. |
| `gjallarhorn/models/plan_step.py` | add `is_planning = BooleanField(default=False)` + `model_used = CharField(blank=True)` fields. |
| `gjallarhorn/apps.py` | wire `ready()` to import the receiver. |
| `gjallarhorn/services/sitrep_service.py` | extend `build_narrative_plan_steps` if needed; add `_persist_sitrep_from_plan(plan) -> SitRep` private helper. |
| `gjallarhorn/services/factory.py` | add `PLANNING_MODEL` + `EXECUTION_MODEL` constants. |
| `gjallarhorn/tasks/sitrep_tasks.py` | NEW — `generate_sitrep_for_project(project_id, from_dt_iso, to_dt_iso, trigger='automatic')` Celery task. |
| `gjallarhorn/tasks/plan_tasks.py` | wire `_persist_sitrep_from_plan(plan)` call in `execute_plan` success branch (only when `plan.conversation.conversation_type == 'sitrep_generation'`). Replace the TODO comment T-EXEC left. |
| `gjallarhorn/agent/agent.py` | stamp `plan.planning_model = PLANNING_MODEL` in `create_plan`; set `step.is_planning` on the final step in `build_narrative_plan_steps` (or in `create_plan`); write `step.model_used` in `execute_single_step`. |
| `gjallarhorn/agent/tool_executor.py` | add intra-plan Redis cache hook (read-only tools) + cleanup at plan-terminate. |
| `ui/views/sitrep.py` | NEW — `sitrep_generate_view(request, project_slug)` POST handler. Returns 302 with `?generated=1`. (T-SITREP-LIST will add the URL route; T-SITREP-GEN may add the route here if needed for tests.) |

## Interfaces locked

- `generate_sitrep_for_project(project_id: int, from_dt_iso: str, to_dt_iso: str, trigger: str = 'automatic') -> str` returns `plan_id` (UUID hex).
- Idempotency: `(project, to_dt, trigger='automatic')` → returns existing plan id; manual trigger can regenerate.
- `_persist_sitrep_from_plan(plan: ExecutionPlan) -> SitRep` — called from `execute_plan` success branch when `plan.conversation.conversation_type == 'sitrep_generation'`. Reads final step `result`, attaches FRAGOs active at `to_dt`, sets `mode_at_generation` from `project.gjallarhorn_mode`, `playbook_version` from active version, `source_plan=plan`. Bad JSON in final step → `plan.mark_failed(...)` with the missing field name; no SitRep row.
- `sync_project_completed.send(sender=Project, project_id=..., completed_at=...)` — receiver wraps `try/except`, must not propagate to `sync_project`.

## Risks

- `ingestion.sync_project` signature is **frozen** — only the body changes.
  Confirm by reading the function before editing.
- Migration 0003 must `python manage.py makemigrations --check` clean **after** the migration is generated. Use `makemigrations gjallarhorn -n sitrep_model_fields` and commit the generated file.
- `Conversation` model has a `UniqueConstraint(user, project)` — the
  auto-trigger receiver runs for a Project with no user-bound conversation
  yet. Use a synthetic "system" user, or relax the constraint, or set
  `conversation_type='sitrep_generation'` and a `user=None` if the model
  allows. Check existing model behavior; if blocked, **flag** — do not silently
  invent a new model semantic. (Quick check path: T-AGENT may already model
  this.)
- The mockup at `ui/templates/ui/mockups/sitrep/list.html` shows a
  `?generated=1` toast trigger; align the manual trigger 302 with that
  query param contract.

## Acceptance

```
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_generate_sitrep_task.py \
  tests/gjallarhorn/test_persist_sitrep_from_plan.py \
  tests/gjallarhorn/test_sitrep_signal.py \
  tests/gjallarhorn/test_sitrep_generate_scenarios.py -x
```
…exits 0. `python manage.py makemigrations --check` clean.
**Acceptance is the test files listed in the task's `## Acceptance criteria`
ONLY** — downstream RED tests (T-SITREP-LIST-*, T-SITREP-VIEW-*) are out of
scope; do NOT implement them. Confirm no previously-GREEN tests regress.
