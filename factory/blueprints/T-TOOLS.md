# Blueprint: T-TOOLS — ToolExecutor + 5 read tools

**Issue:** [#65](https://gitlab.com/dp2580/huginn/-/issues/65) — GJLR-TOOLS
**Task:** [`factory/tasks/pending/T-TOOLS.md`](../tasks/pending/T-TOOLS.md)

## Goal

Implement `gjallarhorn/agent/tool_executor.py` plus the five **narrative-phase
read tools** in `gjallarhorn/mcp_tools/`. After this task, every tool call goes
through the permission-aware dispatcher, returns the standardized
`{"success", "result", "error"}` envelope, and write tools are explicitly
blocked.

## Context

- T-LLM ships `LLM` ABC + `LLMResponse`. `ToolExecutor` does **not** depend on
  the LLM directly — it dispatches tool functions only.
- Read tools query existing models:
  - `ingestion.Increment` (kind `'commit'`) for commits + `Contributor` activity
  - `playbooks.Playbook` + `playbooks.PlaybookVersion`
  - `sitrep.Frago`, `sitrep.SituationalAwareness` + `SituationalAwarenessVersion`
- Every tool takes `project_id` and **must filter on it** — cross-project
  leakage is a security regression.

## Files touched

| File | Change |
|---|---|
| `gjallarhorn/agent/tool_executor.py` | create — `ToolExecutor(user, project)` with `WRITE_TOOLS` frozenset, `register`, `execute`. |
| `gjallarhorn/mcp_tools/data_tools.py` | create — `list_commits(project_id, from_dt, to_dt, limit=200)`, `get_contributor_activity(project_id, from_dt, to_dt)`. |
| `gjallarhorn/mcp_tools/playbook_tools.py` | create — `get_active_playbook(project_id)`. |
| `gjallarhorn/mcp_tools/sitrep_tools.py` | create — `get_active_situational_awareness(project_id)`, `list_active_fragos(project_id, at_dt)`. |
| `gjallarhorn/services/factory.py` | create — `build_executor(user, project) -> ToolExecutor` registers all 5 read tools. |

## Interfaces locked

- Envelope is **always** `{"success": bool, "result": Any, "error": str | None}`.
- `ToolExecutor.execute()` never raises — exceptions in tool functions become `{"success": False, "error": str(exc), "result": None}`.
- `WRITE_TOOLS = frozenset({'create_frago', 'extend_sitawareness', 'create_jira_issue', 'approve_decision'})` — calling any returns `{"success": False, "error": "Write tool '<name>' not enabled in narrative phase"}`.
- Tool function signature: every callable in the registry accepts `project_id` as first kwarg + tool-specific kwargs. `execute()` injects `project_id=self.project.pk` automatically.

## Risks

- Schema drift — read existing `ingestion/models/*.py`, `playbooks/models/*.py`,
  `sitrep/models/*.py` first to confirm field names; do **not** invent ORM
  fields. If a model lacks a field a tool needs, **stop and flag** rather
  than adding the field — that is a separate task.
- The `list_active_fragos(at_dt)` semantics: `effective_from ≤ at_dt` AND
  (`effective_to IS NULL` OR `effective_to > at_dt`) AND `is_active=True`.

## Acceptance

```
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_tool_executor_envelope.py \
  tests/gjallarhorn/test_data_tools_list_commits.py \
  tests/gjallarhorn/test_data_tools_contributor_activity.py \
  tests/gjallarhorn/test_playbook_tools.py \
  tests/gjallarhorn/test_sitrep_tools_sa.py \
  tests/gjallarhorn/test_sitrep_tools_fragos.py -x
```
…exits 0. Full suite green. Ruff clean.
