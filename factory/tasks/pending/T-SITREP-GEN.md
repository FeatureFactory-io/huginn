---
id: T-SITREP-GEN
role: feature-builder
attempt: 1
depends_on: [T-EXEC]
gitlab_issue: 61
branch: factory/T-SITREP-GEN-narrative-pipeline
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - ingestion/signals.py
  - ingestion/tasks.py
  - gjallarhorn/migrations/0003_sitrep_model_fields.py
  - gjallarhorn/models/execution_plan.py
  - gjallarhorn/models/plan_step.py
  - gjallarhorn/apps.py
  - gjallarhorn/services/sitrep_service.py
  - gjallarhorn/services/factory.py
  - gjallarhorn/tasks/sitrep_tasks.py
  - gjallarhorn/tasks/plan_tasks.py
  - gjallarhorn/agent/agent.py
  - gjallarhorn/agent/tool_executor.py
  - ui/views/sitrep.py
  - ui/urls.py
  - tests/gjallarhorn/test_sitrep_generate_scenarios.py
---

# Task T-SITREP-GEN — narrative-phase SitRep generation pipeline (auto + manual)

## Goal

Wire the full SitRep narrative pipeline on top of the executor T-EXEC just landed:

1. `ingestion.sync_project` success emits `sync_project_completed`.
2. A receiver in `gjallarhorn.apps.ready()` enqueues
   `generate_sitrep_for_project.delay(...)` with computed `from_dt` / `to_dt`
   (last SitRep `to_dt` if present, otherwise earliest commit).
3. `generate_sitrep_for_project` creates `Conversation(type='sitrep_generation')`
   + `ExecutionPlan` + 5 `PlanStep`s and delegates to `Agent.create_plan`
   (which enqueues `execute_plan` from T-EXEC).
4. On plan completion, `_persist_sitrep_from_plan(plan)` parses the final
   step's JSON `result`, attaches FRAGOs active at `to_dt`, and writes one
   `SitRep` row (`source_plan=plan`, `mode_at_generation=project.gjallarhorn_mode`,
   `playbook_version=<int>`).
5. Manual trigger view: `POST /sitrep/<int:project_pk>/generate/` enqueues
   with `trigger='manual'`. Returns **HTTP 202** with a JSON body the SitRep
   list page reads to show its toast (mockup uses `?generated=1` query — keep
   the redirect behavior as a 302 fallback for non-AJAX form posts; tests use
   the JSON 202 path per SITREP-GEN-03).

Migration **0003** adds `ExecutionPlan.planning_model`, `PlanStep.is_planning`,
`PlanStep.model_used` (SAO §17.5).

## Must read first

1. **GitLab issue #61** (`glab issue view 61`) — Implementation Plan §A–K is
   the verbatim spec (signal payload, task body, persist helper, model
   constants, cache wiring). Treat it as authoritative.
2. [`factory/blueprints/T-SITREP-GEN.md`](../../blueprints/T-SITREP-GEN.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md) — especially
   the `# Cache blocks (SAO §17.6)` and `# Resilience contract` sections.
4. `docs/architecture/SAO.md` §17.1 (deps), §17.5 (state machine + model
   assignment), §17.6 (intra-plan cache).
5. `docs/features/act-5-sitrep/sitrep-generate.feature` (SITREP-GEN-01…24) —
   acceptance contract.
6. The 4 RED test files (do **not** modify GEN-01…20; you may **add new
   tests** to cover GEN-21/22/23/24 — see "Test additions" below):
   - `tests/gjallarhorn/test_generate_sitrep_task.py`
   - `tests/gjallarhorn/test_persist_sitrep_from_plan.py`
   - `tests/gjallarhorn/test_sitrep_signal.py`
   - `tests/gjallarhorn/test_sitrep_generate_scenarios.py`
7. Inherited assets (read for field names — **do not modify**):
   - `gjallarhorn/models/{conversation,execution_plan,plan_step}.py`
   - `sitrep/models/sitrep.py` (unique on `project, to_dt`; `source_plan` FK)
   - `ingestion/models/{project,increment}.py`
   - `gjallarhorn/services/factory.py` (T-EXEC's `create_agent` + `build_executor`)

## Acceptance criteria

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_generate_sitrep_task.py \
  tests/gjallarhorn/test_persist_sitrep_from_plan.py \
  tests/gjallarhorn/test_sitrep_signal.py \
  tests/gjallarhorn/test_sitrep_generate_scenarios.py -x
```
…exits 0. **Acceptance is the 4 test files above ONLY** — the rest of the
suite contains intentional RED tests for downstream tasks (T-SITREP-LIST-*,
T-SITREP-VIEW-*) and feature-builder UI work you must NOT implement. Confirm
no previously-GREEN tests regress, but do NOT chase the rest of the suite
green. Implement strictly the files in `## Files in scope` below; anything
outside is auto-reject. `python manage.py makemigrations --check` clean
(no orphan model edits).

## Test additions (NEW — narrowly scoped)

Workers may **add** test functions for these scenarios if they are not yet
present in `tests/gjallarhorn/test_sitrep_generate_scenarios.py`:

- `test_sitrep_gen_21_planning_model_recorded` — `plan.planning_model` ==
  `services.factory.PLANNING_MODEL` (`"claude-opus-4-5"`).
- `test_sitrep_gen_22_step_model_used` — final ("compose narrative") step
  has `model_used == PLANNING_MODEL`; other steps have `model_used ==
  EXECUTION_MODEL` (`"claude-sonnet-4-6"`). Use `ScriptedLLM` returning
  `LLMResponse(model=…)` per call.
- `test_sitrep_gen_23_intra_plan_tool_cache_hit` — script two steps that
  both call `list_commits(project_id, from_dt, to_dt)` with identical args;
  assert the underlying tool function is called **once** (use
  `unittest.mock.patch` on the `data_tools.list_commits` symbol the
  registered tool resolves to, plus `Django cache` set to LocMem).
- `test_sitrep_gen_24_cache_keys_cleared_on_terminate` — after `mark_completed`
  / `mark_failed`, `cache.get("plan:<plan_id>:tool:list_commits:<sha>")` is
  None. Use Django `cache` interface with `LocMemCache` (already the test
  default).

Write **only** these four. Do not invent further tests.

## Files in scope

- `ingestion/signals.py` (NEW) — `sync_project_completed = Signal()`. Payload:
  `sender=Project`, `project_id: int`, `completed_at: datetime`.
- `ingestion/tasks.py` (extend) — at the **end** of `sync_project()` success
  path: `sync_project_completed.send(sender=Project, project_id=…,
  completed_at=timezone.now())`. Wrap in `try/except` so signal handler
  failure cannot break sync. **Do not change the function signature.**
- `gjallarhorn/migrations/0003_sitrep_model_fields.py` (NEW) — adds
  `ExecutionPlan.planning_model = CharField(max_length=64, blank=True,
  default='')`, `PlanStep.is_planning = BooleanField(default=False)`,
  `PlanStep.model_used = CharField(max_length=64, blank=True, default='')`.
  Generate via `python manage.py makemigrations gjallarhorn -n
  sitrep_model_fields` and commit the result verbatim.
- `gjallarhorn/models/execution_plan.py` — add the `planning_model` field only
  (state-machine helpers are frozen; T-EXEC tests asserted them).
- `gjallarhorn/models/plan_step.py` — add `is_planning` + `model_used` only.
- `gjallarhorn/apps.py` — `ready()` imports the receiver module which
  `@receiver(sync_project_completed)` decorator wires up. The receiver
  `try/except`s and never raises into the sender.
- `gjallarhorn/services/sitrep_service.py` — extend `build_narrative_plan_steps`
  if needed (mark final step `is_planning=True`); add `_persist_sitrep_from_plan(plan)
  -> SitRep` private helper. Persist contract: parse final step `result` JSON
  (`{headline, situation_assessment, notable_activity?}`); on missing required
  field, call `plan.mark_failed(ValueError("missing field: <name>"))` and
  return `None` (do not raise to caller).
- `gjallarhorn/services/factory.py` — module-level constants
  `PLANNING_MODEL = "claude-opus-4-5"` and
  `EXECUTION_MODEL = "claude-sonnet-4-6"`. (Do NOT delete `create_agent` or
  `build_executor` from T-EXEC / T-TOOLS.)
- `gjallarhorn/tasks/sitrep_tasks.py` (NEW) — `@shared_task(name=
  "gjallarhorn.generate_sitrep_for_project") def
  generate_sitrep_for_project(project_id, from_dt_iso, to_dt_iso,
  trigger='automatic') -> str` (returns plan_id hex). Idempotent on
  `(project, to_dt, trigger='automatic')` — early-return existing plan_id
  if a SitRep already covers that `to_dt`; manual trigger bypasses the
  guard per SITREP-GEN-20.
- `gjallarhorn/tasks/plan_tasks.py` — replace T-EXEC's
  `# TODO(sitrep-generate): _persist_sitrep_from_plan(plan)` with the actual
  call, gated on `plan.conversation.conversation_type == 'sitrep_generation'`.
- `gjallarhorn/agent/agent.py` — in `create_plan`, stamp `plan.planning_model =
  PLANNING_MODEL`; in `execute_single_step`, write `step.model_used` from
  `LLMResponse.model` (or from constant when test path elides the field).
- `gjallarhorn/agent/tool_executor.py` — add intra-plan Django-cache wrapper
  (read-only tools only). Key: `f"plan:{self.plan_id}:tool:{name}:{sha256}"`.
  Constructor takes optional `plan_id: str | None`; cache is bypassed when
  `plan_id is None`. Add `clear_plan_cache(plan_id)` helper called from
  `mark_completed` / `mark_failed`.
- `ui/views/sitrep.py` (NEW) — `sitrep_generate_view(request, project_pk)`
  POST handler. `@login_required`, project lookup `get_object_or_404`, parse
  `period` form field for "Since last SitRep" / "Custom" with `from_dt` /
  `to_dt`, enqueue `generate_sitrep_for_project.delay(...)` with
  `trigger='manual'`, return `JsonResponse({"status":"queued","plan_id":…},
  status=202)` for AJAX or 302 to `?generated=1` for form POSTs.
- `ui/urls.py` — add `path("projects/<int:project_pk>/sitrep/generate/",
  sitrep_generate_view, name="sitrep-generate")`. Do NOT add list/view
  patterns — those are T-SITREP-LIST/VIEW.

## Do not touch

- `gjallarhorn/llm/base.py`, `tests/gjallarhorn/conftest.py`.
- `gjallarhorn/migrations/0001_initial.py`, `0002_sitrep_plan_fields.py`.
- `gjallarhorn/llm/{claude.py,retry.py}`, `gjallarhorn/agent/prompts.py` —
  T-LLM territory.
- `gjallarhorn/agent/{tool_executor.py except cache hook}` core logic — T-TOOLS.
- T-EXEC's `execute_plan` body except the documented `_persist_sitrep_from_plan`
  call insertion.
- `sitrep/models/sitrep.py` — frozen.
- `ui/templates/ui/sitrep/*.html` — owned by T-SITREP-LIST / T-SITREP-VIEW.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-SITREP-GEN-narrative-pipeline

# … implement; generate migration; write the four new tests …

.venv/bin/python -m pytest \
  tests/gjallarhorn/test_generate_sitrep_task.py \
  tests/gjallarhorn/test_persist_sitrep_from_plan.py \
  tests/gjallarhorn/test_sitrep_signal.py \
  tests/gjallarhorn/test_sitrep_generate_scenarios.py -x
.venv/bin/python -m pytest tests/ -x
.venv/bin/python manage.py makemigrations --check
ruff check . && ruff format --check .

git add -A
git commit -m "feat(gjallarhorn): SitRep narrative-phase generation pipeline (auto + manual)"
git push -u origin factory/T-SITREP-GEN-narrative-pipeline

glab mr create \
  --source-branch factory/T-SITREP-GEN-narrative-pipeline \
  --target-branch main \
  --title "feat(gjallarhorn): SitRep generation pipeline (narrative phase)" \
  --description "Implements SITREP-GENERATE-1 (#61). Auto-trigger via signal, manual trigger via POST view, plan-completion side-effect persists SitRep with FRAGOs M2M. Adds migration 0003 (planning_model, is_planning, model_used). Adds intra-plan tool-result cache (SAO §17.6). Includes new tests for GEN-21/22/23/24.

Closes #61" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_generate_sitrep_task.py \
  tests/gjallarhorn/test_persist_sitrep_from_plan.py \
  tests/gjallarhorn/test_sitrep_signal.py \
  tests/gjallarhorn/test_sitrep_generate_scenarios.py -x
# expect: 0 failed
.venv/bin/python manage.py makemigrations --check
# expect: exit 0
```

## Do not

- Do NOT call the real Claude API. `ScriptedLLM` everywhere.
- Do NOT add SSE / Redis publishing — leave `# TODO(chat-milestone): publish
  plan_started / plan_completed / rate_limit_status` comments at the publish
  points referenced by SITREP-GEN-11/16/17. The tests for those scenarios
  assert behavior the chat milestone wires up; this milestone leaves a stub.
- Do NOT modify SITREP-GEN-01…20 test files. Only add the four named
  GEN-21/22/23/24 functions.
- Do NOT introduce `FOB-*` Screen IDs (`.cursor/rules/no-fob-screen-ids.mdc`).
- Do NOT add `Conversation(user=…)` requiring a real user — use a synthetic
  `system` user pattern or `null=True` if the model already supports it. If
  blocked, **stop** and flag in the result block — do not invent a new
  semantic for `Conversation`.

# Result

status:
branch:
mr:
commit_sha:

<!-- Fill all four fields before scripts/done.sh runs. Empty = blocked. -->
