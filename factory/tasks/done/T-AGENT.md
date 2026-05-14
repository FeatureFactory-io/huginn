---
id: T-AGENT
role: feature-builder
attempt: 1
depends_on: [T-LLM, T-TOOLS]
gitlab_issue: 66
branch: factory/T-AGENT-gjallarhorn-agent
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - gjallarhorn/agent/agent.py
  - gjallarhorn/agent/exceptions.py
  - gjallarhorn/agent/__init__.py
  - gjallarhorn/services/sitrep_service.py
  - gjallarhorn/services/__init__.py
  - gjallarhorn/tasks/plan_tasks.py
  - gjallarhorn/tasks/__init__.py
---

# Task T-AGENT — GjallarhornAgent + sitrep_service step builder + execute_plan stub

## Goal

Land `GjallarhornAgent` with `create_plan` / `execute_single_step`, the
`build_narrative_plan_steps` service, and a **minimal `execute_plan` Celery
task stub** that just lets `create_plan` enqueue without exploding (T-EXEC
will replace the stub body with the full resilience matrix).

`process_user_message` is deferred — raises `NotImplementedError`.

## Must read first

1. **GitLab issue #66** — `glab issue view 66`. Implementation Plan §B–E has
   the exact class body, `execute_single_step` recipe, and 5-step canonical
   `build_narrative_plan_steps` content.
2. [`factory/blueprints/T-AGENT.md`](../../blueprints/T-AGENT.md) — especially
   the execute_plan stub guidance.
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. `docs/architecture/SAO.md` §17.4 (Agent) + §17.5 (Plans).
5. The 4 RED test files (do **not** modify):
   - `tests/gjallarhorn/test_agent_create_plan.py`
   - `tests/gjallarhorn/test_agent_execute_single_step.py`
   - `tests/gjallarhorn/test_agent_process_user_message_deferred.py`
   - `tests/gjallarhorn/test_sitrep_service_steps.py`

## Acceptance criteria

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_agent_create_plan.py \
  tests/gjallarhorn/test_agent_execute_single_step.py \
  tests/gjallarhorn/test_agent_process_user_message_deferred.py \
  tests/gjallarhorn/test_sitrep_service_steps.py -x
```
…exits 0. Full suite `.venv/bin/python -m pytest tests/ -x` green.

## Files in scope

- `gjallarhorn/agent/exceptions.py` (NEW) — `ToolExecutionError(tool_name, error_message)` (see issue #66 §C).
- `gjallarhorn/agent/agent.py` (NEW) — `GjallarhornAgent(llm: LLM, tool_executor: ToolExecutor)`. Methods:
  - `create_plan(conversation, goal, steps) -> ExecutionPlan` — `transaction.atomic` wrap, lazy-imports `execute_plan` inside the function and calls `.delay(str(plan.plan_id))`. Sets `progress_total=len(steps)`.
  - `execute_single_step(plan, step) -> None` — builds 4-block `system_blocks` (each with `cache_control: {"type": "ephemeral"}`) using `SITREP_NARRATIVE_SYSTEM_PROMPT` + 3 tool calls (`get_active_playbook`, `list_active_fragos`, `get_active_situational_awareness`). On `{success: False}` from a tool call inside the LLM response, raises `ToolExecutionError`. Persists `step.result`, `step.outcome_assessment`, `step.status = 'completed'`.
  - `process_user_message(self, ...) -> None` — `raise NotImplementedError("Chat surfaces in a future milestone")`.
  - Private helpers `_format_previous_results(plan)`, `_build_system_blocks(plan)`.
  - `# TODO(chat-milestone): publish plan_started/plan_step_update` comments at the publish points.
- `gjallarhorn/agent/__init__.py` — export `GjallarhornAgent`, `ToolExecutionError`.
- `gjallarhorn/services/sitrep_service.py` (NEW) — `build_narrative_plan_steps(project_id, from_dt, to_dt) -> list[dict]` returning **exactly 5** steps. Verbatim copy from issue #66 §D.
- `gjallarhorn/services/__init__.py` — export `build_narrative_plan_steps`.
- `gjallarhorn/tasks/plan_tasks.py` (NEW STUB) — `@shared_task(bind=True, name="gjallarhorn.execute_plan") def execute_plan(self, plan_id: str)`. Minimal body: load plan, `mark_started()`, loop `get_next_pending_step()` → `agent.execute_single_step(plan, step)` → `update_progress`, then `mark_completed()`. NO retry / exception handling. **Banner comment:** `# TODO(T-EXEC): replace with full resilience matrix per SAO §17.5`. Use a private helper `_build_agent_for_plan(plan)` to keep T-EXEC's swap-in surgery surgical.
- `gjallarhorn/tasks/__init__.py` — re-export `execute_plan`.

## Do not touch

- `gjallarhorn/models/*` — model is frozen for this task.
- `gjallarhorn/llm/*` — owned by T-LLM.
- `gjallarhorn/agent/tool_executor.py` — owned by T-TOOLS.
- Any test file under `tests/gjallarhorn/`.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-AGENT-gjallarhorn-agent

# … implement …

.venv/bin/python -m pytest tests/gjallarhorn/test_agent_create_plan.py tests/gjallarhorn/test_agent_execute_single_step.py tests/gjallarhorn/test_agent_process_user_message_deferred.py tests/gjallarhorn/test_sitrep_service_steps.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(gjallarhorn): GjallarhornAgent + build_narrative_plan_steps + execute_plan stub"
git push -u origin factory/T-AGENT-gjallarhorn-agent

glab mr create \
  --source-branch factory/T-AGENT-gjallarhorn-agent \
  --target-branch main \
  --title "feat(gjallarhorn): GjallarhornAgent (create_plan, execute_single_step) + execute_plan stub" \
  --description "Implements GJLR-AGENT (#66). 4 RED test files go GREEN.

Includes a minimal execute_plan Celery task stub so create_plan can enqueue without circular import. T-EXEC (#67) will rewrite execute_plan with the full resilience matrix.

Closes #66" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_agent_create_plan.py \
  tests/gjallarhorn/test_agent_execute_single_step.py \
  tests/gjallarhorn/test_agent_process_user_message_deferred.py \
  tests/gjallarhorn/test_sitrep_service_steps.py -x
# expect: 0 failed
```

## Do not

- Do NOT call the real Claude API.
- Do NOT implement `process_user_message` — must `raise NotImplementedError`.
- Do NOT add SSE/Redis publishing — leave `# TODO(chat-milestone)` comments.
- Do NOT implement the full resilience matrix in `execute_plan` — that's T-EXEC.
- Do NOT add `from gjallarhorn.tasks.plan_tasks import execute_plan` at module
  top in `agent.py` — must be a function-local import to break the cycle.


# Result

status: rescued
branch: factory/T-AGENT-gjallarhorn-agent
mr: 25
commit_sha: b7a6f152

Auto-filled by rescue-result.sh — worker exited without writing Result block.
