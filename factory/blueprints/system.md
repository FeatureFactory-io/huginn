# System blueprint — AI → SitRep (narrative phase)

**Milestone:** `AI -> SitRep` (GitLab #7419357)
**Sprint goal:** Wire Gjallarhorn to produce a SitRep narrative from the doctrine
layer (Playbook + FRAGOs + SitAwareness) and ingested commits — every sync, every
manual trigger. Variables and Decisions are explicitly out of scope.

This document orients workers to the production layout. Read it once before
your first task. The authoritative architecture spec is
[`docs/architecture/SAO.md`](../../docs/architecture/SAO.md) §17 — when this
blueprint and SAO disagree, **SAO wins**.

---

## Top-level architecture (SAO §17.1, §17.2)

```
ingestion/                  sitrep/                       gjallarhorn/  (NEW WORK)
─────────                  ──────                       ──────────────
sync_project (Celery)  →   SitRep            ←──────    services/sitrep_service.py
                           Frago                       ↓
                           SituationalAwareness     ← read tools (mcp_tools/)
                                                        ↓
playbooks/                                            agent/agent.py  GjallarhornAgent
──────────                                              ├─ llm/        LLM ABC + ClaudeLLM
PlaybookVersion                                         ├─ tasks/      execute_plan, sitrep_tasks
PlaybookVariable                                        └─ models/     ExecutionPlan, PlanStep
                                                                       Conversation
                                                                       ↓
                                                       ui/             list + view
```

**Dependency rule (SAO §17.1):** `gjallarhorn/` reads from `ingestion/`, `sitrep/`,
`playbooks/`; writes `SitRep` rows to `sitrep/` (via the plan-completion hook).
In this milestone gjallarhorn does **not** write Decisions or VariableDatapoints —
those are future sprints. No write tools are wired.

---

## What already exists (do not re-implement)

Inherited from the wiped Composer-2 attempt, **kept** as the foundation:

| Asset | Path | Status |
|---|---|---|
| Models | `gjallarhorn/models/{conversation,execution_plan,plan_step}.py` | 25 tests GREEN |
| Migrations 0001+0002 | `gjallarhorn/migrations/0001_initial.py`, `0002_sitrep_plan_fields.py` | applied |
| LLM ABC + dataclass | `gjallarhorn/llm/base.py` | DO NOT MODIFY |
| `ScriptedLLM` fixture | `tests/gjallarhorn/conftest.py` | DO NOT MODIFY |
| SitRep model + migrations | `sitrep/models/sitrep.py`, `sitrep/migrations/0006_sitrep.py` | unique on `(project, to_dt)` |
| Mockups | `ui/templates/ui/mockups/sitrep/{list,view}.html` | port from these, do not redesign |

**21 RED tests** in `tests/gjallarhorn/` currently fail at collection (`ModuleNotFoundError`)
because the modules under test do not exist yet. The factory's job is to turn
each one GREEN, in dependency order, without modifying the test files.

`ExecutionPlan` already carries the state-machine helpers (`mark_started`,
`mark_completed`, `mark_failed`, `mark_paused_for_retry`, `update_progress`,
`get_next_pending_step`) and `InvalidStateTransitionError` — those tests are
already GREEN. T-EXEC layers `execute_plan` on top.

---

## File layout you will create (SAO §17.2)

```
gjallarhorn/
├── llm/
│   ├── base.py                  # EXISTS — do not modify
│   ├── claude.py                # T-LLM (#64)
│   └── retry.py                 # T-LLM (#64)
├── agent/
│   ├── prompts.py               # T-LLM (#64) — SITREP_NARRATIVE_SYSTEM_PROMPT
│   ├── tool_executor.py         # T-TOOLS (#65)
│   ├── exceptions.py            # T-AGENT (#66) — ToolExecutionError
│   └── agent.py                 # T-AGENT (#66) — GjallarhornAgent
├── mcp_tools/
│   ├── data_tools.py            # T-TOOLS (#65) — list_commits, get_contributor_activity
│   ├── playbook_tools.py        # T-TOOLS (#65) — get_active_playbook
│   └── sitrep_tools.py          # T-TOOLS (#65) — get_active_sa, list_active_fragos
├── services/
│   ├── factory.py               # T-EXEC (#67) — create_agent(); T-TOOLS adds build_executor
│   └── sitrep_service.py        # T-AGENT (#66) build_narrative_plan_steps; T-SITREP-GEN extends
├── tasks/
│   ├── plan_tasks.py            # T-EXEC (#67) — execute_plan
│   └── sitrep_tasks.py          # T-SITREP-GEN (#61) — generate_sitrep_for_project
├── migrations/
│   └── 0003_planning_model_is_planning_model_used.py  # T-SITREP-GEN (#61) — see SAO §17.5
└── apps.py                      # T-SITREP-GEN (#61) — ready() connects auto-trigger signal

ingestion/
└── signals.py                   # T-SITREP-GEN (#61) — sync_project_completed Signal

sitrep/
└── (read only this milestone — SitRep rows written via gjallarhorn plan-completion hook)

ui/
├── views/sitrep.py              # T-SITREP-LIST (#76) — list + generate POST; T-SITREP-VIEW (#77) — detail
├── templates/ui/sitrep/
│   ├── list.html                # T-SITREP-LIST — port from ui/templates/ui/mockups/sitrep/list.html
│   └── view.html                # T-SITREP-VIEW — port from ui/templates/ui/mockups/sitrep/view.html
└── urls.py                      # T-SITREP-LIST + T-SITREP-VIEW — add 3 URL patterns
```

---

## Acceptance contracts

| GitLab issue | LE task | Authoritative feature file | RED tests to turn GREEN |
|---|---|---|---|
| #64 | `T-LLM` | (no feature file — infra) | `test_llm_contract.py`, `test_retry_on_rate_limit.py`, `test_prompts.py` |
| #65 | `T-TOOLS` | (no feature file — infra) | `test_tool_executor_envelope.py`, `test_data_tools_*.py`, `test_playbook_tools.py`, `test_sitrep_tools_*.py` |
| #66 | `T-AGENT` | (no feature file — infra) | `test_agent_create_plan.py`, `test_agent_execute_single_step.py`, `test_agent_process_user_message_deferred.py`, `test_sitrep_service_steps.py` |
| #67 | `T-EXEC` | (no feature file — infra) | `test_execution_plan_state_machine.py`, `test_execute_plan_*.py` (6 files) |
| #61 | `T-SITREP-GEN` | `docs/features/act-5-sitrep/sitrep-generate.feature` | `test_generate_sitrep_task.py`, `test_persist_sitrep_from_plan.py`, `test_sitrep_signal.py`, `test_sitrep_generate_scenarios.py` |
| #76 | `T-SITREP-LIST-STEPS` (writer) + `T-SITREP-LIST-IMPL` (builder) | `docs/features/act-5-sitrep/sitrep-list-find.feature` | `tests/ui/test_sitrep_list_scenarios.py` (writer creates) |
| #77 | `T-SITREP-VIEW-STEPS` (writer) + `T-SITREP-VIEW-IMPL` (builder) | `docs/features/act-5-sitrep/sitrep-view.feature` | `tests/ui/test_sitrep_view_scenarios.py` (writer creates) |

The 21 backend RED tests are already committed on `main`. **Workers may not
modify test files** for tasks T-LLM, T-TOOLS, T-AGENT, T-EXEC, T-SITREP-GEN —
the contracts are fixed. (Exception: T-SITREP-GEN adds *new* tests for
SITREP-GEN-21/22/23/24 which currently have no coverage — call this out in the
MR description.)

---

## Test conventions

- `pytest` + `pytest-django` only. No `pytest-bdd` for the backend tasks —
  scenario coverage is via direct integration tests that reference the
  scenario ID in their docstring. The two UI tasks (#76/#77) wrap each Gherkin
  scenario as its own pytest function with a `# SCENARIO: SITREP-…` comment.
- **No network.** `ScriptedLLM` from `tests/gjallarhorn/conftest.py` is the
  only LLM in tests. `ClaudeLLM` is imported lazily and never instantiated.
- `CELERY_TASK_ALWAYS_EAGER = True` in `huginn/settings/test.py` — already in
  place. All Celery `.delay()` calls run synchronously in tests.
- Test runner: `.venv/bin/python -m pytest …` from worktree root.

---

## Branching, MRs, and commits

- Trunk-based: all task branches target **`main`**.
- Branch name pattern: `factory/<task-id>-<slug>` (e.g. `factory/T-LLM-llm-layer`).
- MR title = the headline of the GitLab issue (or a clearer one). MR body must
  end with `Closes #<issue-iid>`.
- One MR per task. Squash-merge with `--remove-source-branch`.
- Commit messages follow Conventional Commits (`feat(gjallarhorn): …`,
  `test(gjallarhorn): …`). Workers may make multiple commits inside one MR
  for readable TDD steps (RED → GREEN → REFACTOR) — `integrate.sh merge`
  squashes them.

---

## Mode at generation and operating modes (SAO §17.9)

- `Project.gjallarhorn_mode` is a field already in `ingestion/`. Default
  `semi_auto`. The narrative-phase pipeline must **read** this at generation
  time and store it on the `SitRep` as `mode_at_generation`. No mode-aware
  branching otherwise this milestone — both modes generate the same narrative
  output (no Decisions are proposed).

## Cache blocks (SAO §17.6) — narrative only

When workers assemble the LLM system prompt in `Agent.execute_single_step`,
each system block must carry `cache_control: {"type": "ephemeral"}`. There are
exactly **4 blocks** in this milestone:

1. `SITREP_NARRATIVE_SYSTEM_PROMPT` (constant in `gjallarhorn/agent/prompts.py`).
2. Active Playbook Workflow markdown + Variable *definitions* (read, do not compute).
3. Active FRAGOs body text concatenated (enabled + in-window at `to_dt`).
4. Situational Awareness capsule.

Variables snapshots, Decisions, and SitRep history are **not** in any block in
this milestone — they're future-sprint additions.

## Resilience contract (SAO §17.5)

- `RateLimitError` / `TimeoutError` / `OSError` in `execute_plan` →
  `plan.mark_paused_for_retry(exc)` + `self.retry(countdown=…)`. Completed
  steps are never re-run on retry — guarded by `get_next_pending_step()`.
- Any other exception → `plan.mark_failed(exc)`. No SitRep row written. Recovery
  notification is a **TODO** stub for the Chat milestone.

---

## Do not (sprint-wide)

- **Do not call the real Claude API in any test.** Use `ScriptedLLM`.
- **Do not modify** `gjallarhorn/llm/base.py`, `tests/gjallarhorn/conftest.py`,
  `gjallarhorn/models/*`, or `gjallarhorn/migrations/0001_initial.py` /
  `0002_sitrep_plan_fields.py`.
- **Do not** implement write tools (`create_frago`, `extend_sitawareness`,
  `approve_decision`, `create_jira_issue`) — those land in the Decisions
  milestone. T-TOOLS only registers a write-block in `ToolExecutor`.
- **Do not** implement `process_user_message` — must `raise NotImplementedError`.
- **Do not** add SSE / Redis publishing. Mark publish points with
  `# TODO(chat-milestone): publish …`.
- **Do not** redesign `ui/templates/ui/sitrep/*.html` — **port** from the
  mockup files at `ui/templates/ui/mockups/sitrep/`.
- **Do not** introduce `FOB-*` Screen IDs anywhere — Huginn uses the unprefixed
  `{ENTITY}-{OPERATION}-{VERSION}` scheme (`.cursor/rules/no-fob-screen-ids.mdc`).

## Definition of done per task

A task is done when, in the worktree:
1. `pytest <its checkpoint command>` exits 0.
2. `pytest tests/ -x` exits 0 — no regressions across the suite.
3. `ruff check . && ruff format --check .` is clean.
4. Branch pushed; MR opened; `Closes #NN` in the MR description; CI green
   *or* N/A (Huginn's `.gitlab-ci.yml` workflow rule restricts the app
   pipeline to `release/x.y.z` branches per SAO §9, so most factory MRs will
   not have a pipeline — that is expected).
5. `# Result` block filled in: `status`, `branch`, `mr`, `commit_sha`.
