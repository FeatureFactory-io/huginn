# Blueprint: T-EXEC — execute_plan Celery task + full resilience matrix

**Issue:** [#67](https://gitlab.com/dp2580/huginn/-/issues/67) — GJLR-EXECUTE-PLAN
**Task:** [`factory/tasks/pending/T-EXEC.md`](../tasks/pending/T-EXEC.md)

## Goal

Replace the T-AGENT stub in `gjallarhorn/tasks/plan_tasks.py` with the full
`execute_plan` Celery task body per SAO §17.5: completed steps never re-run,
rate-limit / network errors → `mark_paused_for_retry` + Celery retry,
permanent failures → `mark_failed`. Also add `create_agent` in
`gjallarhorn/services/factory.py`.

The state-machine helpers (`mark_started` / `mark_completed` / `mark_failed` /
`mark_paused_for_retry` / `update_progress` / `get_next_pending_step`) and
`InvalidStateTransitionError` **already exist** on `ExecutionPlan`
(see `gjallarhorn/models/execution_plan.py`); their tests
(`test_execution_plan_state_machine.py`) currently fail at collection only
because they import test infrastructure that depends on the agent stack —
once T-AGENT lands the model tests collect and pass. Re-confirm in your worktree.

## Context

- `_build_agent_for_plan(plan)` exists in T-AGENT's stub. T-EXEC keeps the
  helper at module scope so tests can monkey-patch it to inject
  `GjallarhornAgent(ScriptedLLM([...]), build_executor(...))`.
- `huginn/settings/test.py` must have `CELERY_TASK_ALWAYS_EAGER = True` and
  `CELERY_TASK_EAGER_PROPAGATES = True` — add if missing.
- The retry-countdown helper: `30 * 2 ** (plan.retry_count - 1)`, capped at 120.

## Files touched

| File | Change |
|---|---|
| `gjallarhorn/tasks/plan_tasks.py` | replace stub body with the full `execute_plan` per issue #67 §C. Preserve `_build_agent_for_plan` and `_retry_countdown` as module-level helpers. |
| `gjallarhorn/services/factory.py` | add `create_agent(user=None, project=None) -> GjallarhornAgent` (issue #67 §D). |
| `huginn/settings/test.py` | confirm `CELERY_TASK_ALWAYS_EAGER = True` + `CELERY_TASK_EAGER_PROPAGATES = True`. |

## Interfaces locked

- `execute_plan(self, plan_id: str)` — `@shared_task(bind=True, max_retries=5, name="gjallarhorn.execute_plan")`.
- Resilience matrix per SAO §17.5:
  - `RateLimitError | TimeoutError | OSError` → `plan.mark_paused_for_retry(exc)` + `raise self.retry(exc=exc, countdown=_retry_countdown(plan))`.
  - Any other `Exception` → `plan.mark_failed(exc)`.
- Reentrant safety: if `plan.mark_started()` raises `InvalidStateTransitionError`, return immediately (idempotent no-op for completed/failed plans).
- TODO stubs: `_notify_ai_of_plan_success/failure` are **comments only** in
  this task — the Chat milestone wires them.
- TODO stub: `_persist_sitrep_from_plan(plan)` is a comment in the success
  branch — T-SITREP-GEN wires it.

## Risks

- `RateLimitError` import path: `anthropic.RateLimitError` is the canonical
  rate-limit class. Tests patch `_build_agent_for_plan` to inject a
  `ScriptedLLM` that raises `anthropic.RateLimitError` from step N. Confirm
  the import path matches the installed `anthropic` SDK from T-LLM.
- The model already has `mark_paused_for_retry` that auto-fails when
  `retry_count >= max_retries`. Do **not** duplicate that logic in the task.

## Acceptance

```
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_execution_plan_state_machine.py \
  tests/gjallarhorn/test_execute_plan_happy_path.py \
  tests/gjallarhorn/test_execute_plan_rate_limit_retry.py \
  tests/gjallarhorn/test_execute_plan_permanent_failure.py \
  tests/gjallarhorn/test_execute_plan_partial_resume.py \
  tests/gjallarhorn/test_execute_plan_max_retries_exhausted.py -x
```
…exits 0. Full suite green. Ruff clean.
