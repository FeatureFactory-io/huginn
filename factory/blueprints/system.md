# System Blueprint — Huginn / AI → SitRep sprint

> **Canonical source:** `docs/architecture/SAO.md` (esp. §3, §17).
> This file is a worker-readable digest. When in doubt, SAO.md wins.

---

## Repository layout (relevant apps only)

```
huginn/
├── ingestion/
│   ├── models/          # Project, DataSource, Increment (commits/MRs), Contributor, IngestionRun
│   ├── adapters/        # DataSourceAdapter ABC + per-source extractors
│   ├── services/        # SyncEngine — orchestrates extraction; fires sync_project_completed signal
│   └── tasks.py         # sync_project Celery task → calls SyncEngine
├── analytics/
│   ├── models/          # Playbook, PlaybookVersion, Variable, Threshold
│   └── services/        # Master Variable computation (NOT touched this sprint)
├── sitrep/
│   ├── models/          # SitRep ← NEW (this sprint #60)
│   │                    # Also: Frago, SituationalAwareness, SituationalAwarenessVersion (pre-existing)
│   └── services/        # SitRep / Frago / SA CRUD helpers (pre-existing; extend as needed)
├── gjallarhorn/         # NEW — entire app created this sprint
│   ├── llm/
│   │   ├── base.py      # LLM ABC + LLMResponse dataclass (#64)
│   │   ├── claude.py    # ClaudeLLM — claude-sonnet-4-6, thinking enabled (#64)
│   │   └── retry.py     # retry_on_rate_limit decorator (#64)
│   ├── agent/
│   │   ├── agent.py     # GjallarhornAgent(llm, tool_executor) (#66)
│   │   ├── tool_executor.py  # Permission-aware dispatcher → {success,result,error} (#65)
│   │   ├── prompts.py   # SITREP_NARRATIVE_SYSTEM_PROMPT (#64)
│   │   └── exceptions.py    # ToolExecutionError, InvalidStateTransitionError (#65, #67)
│   ├── mcp_tools/
│   │   ├── data_tools.py     # list_commits, get_contributor_activity (#65)
│   │   ├── playbook_tools.py # get_active_playbook (#65)
│   │   └── sitrep_tools.py   # get_active_situational_awareness, list_active_fragos (#65)
│   ├── models/
│   │   ├── conversation.py   # Conversation, Message (#60)
│   │   ├── execution_plan.py # ExecutionPlan + state-machine helpers (#60 fields; #67 helpers)
│   │   └── plan_step.py      # PlanStep (#60)
│   ├── services/
│   │   ├── sitrep_service.py # build_narrative_plan_steps, _persist_sitrep_from_plan (#66, #61)
│   │   └── factory.py        # build_executor(user,project), create_agent() (#65, #67)
│   └── tasks/
│       ├── plan_tasks.py     # execute_plan Celery task (#67)
│       └── sitrep_tasks.py   # generate_sitrep_for_project Celery task (#61)
├── ui/
│   ├── views/           # SitRep list + view production views (#62, #63)
│   └── templates/ui/
│       ├── sitrep/list.html  # Production list template (#62)
│       └── sitrep/view.html  # Production view template (#63)
│       └── mockups/sitrep/   # Existing mockups — source of truth for UI layout
└── huginn/
    ├── settings/test.py # CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True
    └── celery.py        # Celery app — broker=Redis
```

---

## Key interfaces (normative — do not deviate)

### `LLM` ABC (`gjallarhorn/llm/base.py`)
```python
class LLM(ABC):
    @abstractmethod
    def generate_with_tools(
        self,
        messages: list[dict],
        tools: list[dict],
        system_blocks: list[dict],    # 4 cache-control blocks
    ) -> LLMResponse: ...

@dataclass
class LLMResponse:
    content: str
    stop_reason: str          # 'end_turn' | 'tool_use'
    usage: dict               # input_tokens, output_tokens, cache_read_input_tokens
    tool_calls: list[dict] = field(default_factory=list)
    model: str = ''
```

### `ToolExecutor.execute()` envelope (always returns, never raises)
```python
{"success": True,  "result": <any>,  "error": None}
{"success": False, "result": None,   "error": "<message>"}
```

### `GjallarhornAgent` public surface (`gjallarhorn/agent/agent.py`)
```python
class GjallarhornAgent:
    def create_plan(self, conversation, goal, steps) -> ExecutionPlan: ...
    def execute_single_step(self, plan, step) -> None: ...
    def process_user_message(self, ...) -> None:
        raise NotImplementedError   # Chat milestone — DO NOT implement
```

### `execute_plan` Celery task — resilience matrix
| Exception type | Action |
|---|---|
| `anthropic.RateLimitError`, `TimeoutError`, `OSError` | `mark_paused_for_retry` → `self.retry(countdown=…)` |
| Any other `Exception` | `mark_failed(exc)` — no retry |
| All steps completed | `mark_completed()` → `_persist_sitrep_from_plan(plan)` |

Completed steps (`status='completed'`) are **never re-executed** on retry — `get_next_pending_step()` filters them out.

---

## Data flow — Flow A (ingestion sync → SitRep)

```
Celery Beat
  └─ sync_project (ingestion/tasks.py)
       └─ SyncEngine.run() → upserts Increments
            └─ sync_project_completed.send(project_id, completed_at)   ← Django signal
                 └─ signal receiver (gjallarhorn/tasks/sitrep_tasks.py)
                      └─ generate_sitrep_for_project.delay(project_id, from_dt, to_dt, 'automatic')
                           └─ resolve from_dt (last SitRep.to_dt OR earliest commit dt)
                           └─ idempotency guard: (project, to_dt) already in DB → return
                           └─ no Playbook assigned → WARNING + return
                           └─ create Conversation(type='sitrep_generation')
                           └─ agent.create_plan(conversation, goal, 5 steps)
                                └─ ExecutionPlan + PlanStep × 5 persisted
                                └─ execute_plan.delay(plan_id)
                                     └─ loop: get_next_pending_step()
                                          └─ agent.execute_single_step(plan, step)
                                               └─ build 4 system_blocks (Prompt+Playbook+FRAGOs+SA)
                                               └─ llm.generate_with_tools(messages, tools, blocks)
                                               └─ dispatch tool calls via ToolExecutor
                                               └─ step.status = 'completed'; step.result saved
                                     └─ all done → mark_completed()
                                     └─ _persist_sitrep_from_plan(plan) → SitRep row created
```

---

## Scope constraints for this sprint

| **In scope** | **Explicitly out of scope** |
|---|---|
| `gjallarhorn/` app (models, LLM, tools, agent, tasks) | SSE / Redis publish calls (all `# TODO(chat-milestone)`) |
| `sitrep/models/sitrep.py` (new `SitRep` model) | Write tools: `create_frago`, `extend_sitawareness`, `create_jira_issue` |
| Production list + view UI (#62, #63) | `process_user_message` on agent (Chat milestone) |
| Signal wiring (`sync_project_completed`) | VariableDatapoint writes |
| Integration tests (all 8 blocks, no mock) | `execute_decision_outcome` |
| | `gjallarhorn/views/` (chat views — Chat milestone) |

---

## Dependency rule (from SAO §17.1 — normative)

`gjallarhorn/` **reads from**: `sitrep/`, `analytics/`, `ingestion/`
`gjallarhorn/` **writes to**: `sitrep/` models (SitRep, Decision, VariableDatapoint)

No other app imports from `gjallarhorn/`. Django signal is the only coupling point from `ingestion/` → `gjallarhorn/`.

---

## Test conventions (apply in every task)

- `ScriptedLLM` (from `tests/gjallarhorn/conftest.py`) — never `ClaudeLLM` in tests.
- `CELERY_TASK_ALWAYS_EAGER = True` — tasks run synchronously in test process.
- Seed data via ORM inside each test function or `@pytest.fixture`; no YAML fixtures.
- Real-API tests marked `@pytest.mark.requires_llm_api`; excluded from default CI run.
- Every test file lives in `tests/<app>/test_<module>.py`.
- Checkpoint command per issue runs the specific test files for that issue; full suite with `pytest tests/ -x`.

---

## Existing code workers must read before touching

| File | Why |
|---|---|
| `ingestion/tasks.py` | `sync_project` task — signal fires here on success; do not break it |
| `ingestion/services/sync_engine.py` | Where to call `.send()` — check existing pattern first |
| `sitrep/models/frago.py` | `Frago` fields `is_active`, `effective_from`, `effective_to` — used by `list_active_fragos` tool |
| `sitrep/models/situational_awareness.py` | SA + SAVersion fields — used by `get_active_situational_awareness` tool |
| `analytics/models/` | `Playbook`, `PlaybookVersion` — used by `get_active_playbook` tool |
| `ui/templates/ui/mockups/sitrep/list.html` | Source of truth for #62 list template |
| `ui/templates/ui/mockups/sitrep/view.html` | Source of truth for #63 view template |
| `docs/architecture/SAO.md §17.5` | Exact `ExecutionPlan` + `PlanStep` field list — copy verbatim |
| `docs/architecture/SAO.md §17.11` | Exact `Conversation` + `Message` field list — copy verbatim |
