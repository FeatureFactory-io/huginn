---
id: T-EXEC
role: feature-builder
attempt: 2
previous_attempt: factory/tasks/rejected/T-EXEC/20260514-125626.txt
depends_on: [T-AGENT]
gitlab_issue: 67
branch: factory/T-EXEC-execute-plan
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - gjallarhorn/tasks/plan_tasks.py
  - gjallarhorn/services/factory.py
  - huginn/settings/test.py
---

# Task T-EXEC — execute_plan Celery task with full resilience matrix

## Remediation (attempt 2 — LE)

**Attempt 1 was rejected.** The `plan_tasks.py` body itself is correct
(73 LoC, clean resilience matrix); the failure was at the `git` level:

1. **Stale base — branch built on the rejected T-AGENT commit `6fa587f`.**
   The previous attempt branched off the worktree's existing tip without
   `git reset --hard origin/main` first, so the branch picked up the
   rejected T-AGENT-attempt-1 work and dragged its scope into the MR.
   Result: 17 files changed instead of the 3 in scope, including all of
   T-AGENT (`agent/agent.py`, `agent/exceptions.py`, `agent/__init__.py`,
   `agent/tool_executor.py`), all of T-TOOLS (`mcp_tools/*` —
   already-merged !24), and all of T-SITREP-GEN
   (`tasks/sitrep_tasks.py`, `services/sitrep_service.py`, `apps.py`).

2. **MR !26 closed.** Open a fresh MR off attempt-2's branch.

### Required start sequence (do not skip the reset)

```bash
cd .worktrees/feature-builder
git fetch origin
git checkout main
git reset --hard origin/main           # main currently has T-LLM + T-TOOLS only
git branch -D factory/T-EXEC-execute-plan || true
git push origin --delete factory/T-EXEC-execute-plan || true
git checkout -b factory/T-EXEC-execute-plan
```

Verify the base is clean before writing any code:

```bash
git log --oneline origin/main..HEAD     # expect: empty (your branch == main)
ls gjallarhorn/agent/                    # expect: ENOENT (T-AGENT not merged yet)
ls gjallarhorn/tasks/plan_tasks.py 2>&1  # expect: ENOENT
```

If `gjallarhorn/agent/` exists, **stop** — your reset failed.

### Reusable from attempt 1

The body of `gjallarhorn/tasks/plan_tasks.py` from the rejected branch
(commit `b7a23393` on `factory/T-EXEC-execute-plan` before the force-push)
is correct and acceptance-test-ready. You may copy it verbatim. Confirm
it still matches the verbatim spec in **issue #67 §C** before committing.

### Dependency note

This task `depends_on: [T-AGENT]`. T-AGENT is currently in `pending/`
(also attempt 2). The factory's `claim.sh` will reject this task until
T-AGENT lands in `done/`. **Do not branch off T-AGENT's branch** —
branch off `main` after T-AGENT's MR is merged.

### Files in scope (unchanged)

Only the 3 files listed in the frontmatter. Anything else is an auto-reject.

---

## Goal

Replace T-AGENT's `execute_plan` stub with the production body: completed
steps never re-run on retry, `RateLimitError`/`TimeoutError`/`OSError` →
`mark_paused_for_retry` + Celery `self.retry`, any other exception →
`mark_failed`. Also add `create_agent` in `services/factory.py` so production
code (not tests) can construct a `GjallarhornAgent` with the real `ClaudeLLM`.

`ExecutionPlan` state-machine helpers and `InvalidStateTransitionError` are
already implemented on the model — do **not** add them again.

## Must read first

1. **GitLab issue #67** — `glab issue view 67`. Implementation Plan §C–F has
   verbatim `execute_plan` body, factory helper, and test inventory.
2. [`factory/blueprints/T-EXEC.md`](../../blueprints/T-EXEC.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. `docs/architecture/SAO.md` §17.5 (Plans & Async Execution, resilience matrix).
5. Existing model: `gjallarhorn/models/execution_plan.py` — confirm
   `mark_started`, `mark_paused_for_retry`, `mark_completed`, `mark_failed`,
   `update_progress`, `get_next_pending_step` all exist. **Do not modify.**
6. The 6 RED test files (do **not** modify):
   - `tests/gjallarhorn/test_execution_plan_state_machine.py`
   - `tests/gjallarhorn/test_execute_plan_happy_path.py`
   - `tests/gjallarhorn/test_execute_plan_rate_limit_retry.py`
   - `tests/gjallarhorn/test_execute_plan_permanent_failure.py`
   - `tests/gjallarhorn/test_execute_plan_partial_resume.py`
   - `tests/gjallarhorn/test_execute_plan_max_retries_exhausted.py`

## Acceptance criteria

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_execution_plan_state_machine.py \
  tests/gjallarhorn/test_execute_plan_happy_path.py \
  tests/gjallarhorn/test_execute_plan_rate_limit_retry.py \
  tests/gjallarhorn/test_execute_plan_permanent_failure.py \
  tests/gjallarhorn/test_execute_plan_partial_resume.py \
  tests/gjallarhorn/test_execute_plan_max_retries_exhausted.py -x
```
…exits 0. **Acceptance is the 6 test files above ONLY.** The rest of the
suite contains intentional RED tests for downstream tasks (T-SITREP-GEN,
T-SITREP-LIST-*, T-SITREP-VIEW-*). Confirm no previously-GREEN tests
regress, but do NOT implement those downstream subjects. Anything outside
the files-in-scope list below will be auto-rejected.

## Files in scope

- `gjallarhorn/tasks/plan_tasks.py` — REPLACE T-AGENT's stub body with the verbatim implementation from issue #67 §C. Keep `_build_agent_for_plan` and add `_retry_countdown` as module-level helpers (tests monkey-patch `_build_agent_for_plan` to inject a `ScriptedLLM`-backed agent).
- `gjallarhorn/services/factory.py` — add `create_agent(user=None, project=None) -> GjallarhornAgent` per issue #67 §D. Uses `ClaudeLLM(api_key=settings.ANTHROPIC_API_KEY)` + `build_executor(user, project)`. Lazy-import `ClaudeLLM` to keep test setup free of `ANTHROPIC_API_KEY`.
- `huginn/settings/test.py` — confirm or add `CELERY_TASK_ALWAYS_EAGER = True` and `CELERY_TASK_EAGER_PROPAGATES = True`.

## Do not touch

- `gjallarhorn/models/*` — state-machine helpers already exist.
- `gjallarhorn/agent/*` — owned by T-AGENT.
- `gjallarhorn/llm/*` — owned by T-LLM.
- Any test file.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-EXEC-execute-plan

# … implement …

.venv/bin/python -m pytest tests/gjallarhorn/test_execution_plan_state_machine.py tests/gjallarhorn/test_execute_plan_happy_path.py tests/gjallarhorn/test_execute_plan_rate_limit_retry.py tests/gjallarhorn/test_execute_plan_permanent_failure.py tests/gjallarhorn/test_execute_plan_partial_resume.py tests/gjallarhorn/test_execute_plan_max_retries_exhausted.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(gjallarhorn): execute_plan Celery task + resilience matrix"
git push -u origin factory/T-EXEC-execute-plan

glab mr create \
  --source-branch factory/T-EXEC-execute-plan \
  --target-branch main \
  --title "feat(gjallarhorn): execute_plan Celery task + resilience matrix" \
  --description "Implements GJLR-EXECUTE-PLAN (#67). 6 RED test files go GREEN.

Closes #67" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_execution_plan_state_machine.py \
  tests/gjallarhorn/test_execute_plan_happy_path.py \
  tests/gjallarhorn/test_execute_plan_rate_limit_retry.py \
  tests/gjallarhorn/test_execute_plan_permanent_failure.py \
  tests/gjallarhorn/test_execute_plan_partial_resume.py \
  tests/gjallarhorn/test_execute_plan_max_retries_exhausted.py -x
# expect: 0 failed
```

## Do not

- Do NOT touch `ExecutionPlan` model — state-machine helpers already exist.
- Do NOT mark a plan `failed` on `RateLimitError` — must be `mark_paused_for_retry` (the model auto-fails when retry_count exceeds max).
- Do NOT write the SitRep persistence side-effect — that's T-SITREP-GEN.
  Leave `# TODO(sitrep-generate): _persist_sitrep_from_plan(plan)` comment.
- Do NOT add SSE/Redis publishing.
- Do NOT add `execute_decision_outcome` — Decisions milestone.

# Result

status: integrated
branch: factory/T-EXEC-execute-plan
mr: 29
commit_sha: 91965208

Auto-filled by rescue-result.sh — worker exited without writing Result block.
