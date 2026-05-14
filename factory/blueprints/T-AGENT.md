# Blueprint: T-AGENT — GjallarhornAgent (create_plan, execute_single_step)

**Issue:** [#66](https://gitlab.com/dp2580/huginn/-/issues/66) — GJLR-AGENT
**Task:** [`factory/tasks/pending/T-AGENT.md`](../tasks/pending/T-AGENT.md)

## Goal

Land `gjallarhorn/agent/agent.py` (`GjallarhornAgent`) and
`gjallarhorn/services/sitrep_service.py` (`build_narrative_plan_steps`),
wiring the `LLM` ABC + `ToolExecutor` + `ExecutionPlan`/`PlanStep` persistence.
`process_user_message` is deferred to the Chat milestone — it must
`raise NotImplementedError`.

## Context

- T-LLM ships `LLM`, `LLMResponse`, `ClaudeLLM`, `SITREP_NARRATIVE_SYSTEM_PROMPT`.
- T-TOOLS ships `ToolExecutor` + `build_executor` factory.
- `ExecutionPlan` + `PlanStep` already exist in `gjallarhorn/models/`. T-AGENT
  **does not** modify the model — only persists rows through it.
- `create_plan` must enqueue `execute_plan.delay(plan_id)`. The `execute_plan`
  task itself is T-EXEC; here, **lazy-import** to avoid circular deps:
  `from gjallarhorn.tasks.plan_tasks import execute_plan` inside the function.

## Files touched

| File | Change |
|---|---|
| `gjallarhorn/agent/agent.py` | create — `GjallarhornAgent(llm, tool_executor)` with `create_plan`, `execute_single_step`, `process_user_message` (NotImplementedError). |
| `gjallarhorn/agent/exceptions.py` | create — `ToolExecutionError(Exception)`. |
| `gjallarhorn/agent/__init__.py` | extend exports — `GjallarhornAgent`, `ToolExecutionError`. |
| `gjallarhorn/services/sitrep_service.py` | create — `build_narrative_plan_steps(project_id, from_dt, to_dt) -> list[dict]` returning the 5 canonical steps (see issue §D). |
| `gjallarhorn/services/__init__.py` | export `build_narrative_plan_steps`. |
| `gjallarhorn/tasks/plan_tasks.py` | create **stub** with a `@shared_task` named `gjallarhorn.execute_plan` that takes `plan_id` and immediately calls the agent for each step. T-EXEC will replace this with the full resilience matrix. The stub exists so `create_plan` can import + enqueue without circular fail. **Mark the stub clearly** so T-EXEC knows to rewrite it. |

## Interfaces locked

- `GjallarhornAgent.create_plan(conversation, goal, steps) -> ExecutionPlan`:
  - Wraps row creation in `transaction.atomic()`.
  - Sets `plan.progress_total = len(steps)`, `plan.status = 'pending'`.
  - Creates one `PlanStep` per dict in `steps` with `order = i+1`.
  - Calls `execute_plan.delay(str(plan.plan_id))` (lazy import).
  - Returns the saved `ExecutionPlan` instance.
- `GjallarhornAgent.execute_single_step(plan, step) -> None`:
  - Builds 4-block `system_blocks` (cache_control:ephemeral) per SAO §17.6.
  - Calls `self.llm.generate_with_tools(messages, NARRATIVE_TOOLS, system_blocks)`.
  - For each `tool_call`: dispatches via `self.tool_executor.execute(...)`; on `{"success": False}` raises `ToolExecutionError(tool_name, error)`.
  - Stores `step.result = {"tool_results": [...], "synthesis": response.content}`, `step.outcome_assessment = response.content`, `step.status = 'completed'`, saves.
- `GjallarhornAgent.process_user_message(...)` — body is `raise NotImplementedError("Chat surfaces in a future milestone")`.
- `build_narrative_plan_steps(project_id, from_dt, to_dt)` — returns the 5 canonical steps verbatim from issue #66 §D. Step 5 action contains "narrative"; step 1 action contains "commits".

## Risks

- The execute_plan stub is a deliberate pre-bake for T-EXEC. Make sure it:
  - Has a `# TODO(T-EXEC): replace with full resilience matrix per SAO §17.5` banner.
  - Calls `plan.mark_started()`, iterates `plan.get_next_pending_step()`, calls `agent.execute_single_step` per step, then `plan.mark_completed()`.
  - Does **not** add retry/exception handling — that's T-EXEC's job. The minimum body just makes the agent tests pass (`test_enqueues_execute_plan` asserts `status != 'pending'` after `create_plan` with `CELERY_TASK_ALWAYS_EAGER=True`).
- 4-block system prompt: callers (`execute_single_step`) need a `project` to assemble blocks 2/3/4 (Playbook, FRAGOs, SA). The conversation's project comes from `plan.conversation.project`. Use `self.tool_executor.execute('get_active_playbook', ...)` etc. — but be defensive: if `success=False`, fall back to an empty block but **still emit 4 blocks** (test asserts `len == 4`).

## Acceptance

```
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_agent_create_plan.py \
  tests/gjallarhorn/test_agent_execute_single_step.py \
  tests/gjallarhorn/test_agent_process_user_message_deferred.py \
  tests/gjallarhorn/test_sitrep_service_steps.py -x
```
…exits 0. Ruff clean. **Acceptance is the 4 test files above ONLY** — other
RED tests in the suite belong to downstream tasks (T-EXEC, T-SITREP-GEN).
Confirm no previously-GREEN test regresses, but do NOT implement those
downstream subjects to make them pass — that's out of scope and will be
rejected.
