---
id: T-TOOLS
role: feature-builder
attempt: 1
depends_on: [T-LLM]
gitlab_issue: 65
branch: factory/T-TOOLS-tool-executor
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - gjallarhorn/agent/tool_executor.py
  - gjallarhorn/mcp_tools/data_tools.py
  - gjallarhorn/mcp_tools/playbook_tools.py
  - gjallarhorn/mcp_tools/sitrep_tools.py
  - gjallarhorn/mcp_tools/__init__.py
  - gjallarhorn/services/factory.py
  - gjallarhorn/services/__init__.py
---

# Task T-TOOLS — ToolExecutor + 5 narrative-phase read tools

## Goal

Land `gjallarhorn/agent/tool_executor.py`, the 5 read tools in
`gjallarhorn/mcp_tools/`, and the `build_executor` factory so the 6 RED test
files below go GREEN. Write tools (`create_frago`, `extend_sitawareness`,
`approve_decision`, `create_jira_issue`) are blocked at the dispatcher level
and stay unimplemented this milestone.

## Must read first

1. **GitLab issue #65** — `glab issue view 65`. Implementation Plan §B–F has
   verbatim `ToolExecutor` code, tool signatures, and test inventory.
2. [`factory/blueprints/T-TOOLS.md`](../../blueprints/T-TOOLS.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. `docs/architecture/SAO.md` §17.4 (ToolExecutor + envelope).
5. The 6 RED test files (do **not** modify):
   - `tests/gjallarhorn/test_tool_executor_envelope.py`
   - `tests/gjallarhorn/test_data_tools_list_commits.py`
   - `tests/gjallarhorn/test_data_tools_contributor_activity.py`
   - `tests/gjallarhorn/test_playbook_tools.py`
   - `tests/gjallarhorn/test_sitrep_tools_sa.py`
   - `tests/gjallarhorn/test_sitrep_tools_fragos.py`
6. Existing models — read field names before writing queries:
   - `ingestion/models/*.py` (Increment, Contributor)
   - `playbooks/models/*.py` (Playbook, PlaybookVersion)
   - `sitrep/models/{frago.py,situational_awareness.py}`

## Acceptance criteria

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_tool_executor_envelope.py \
  tests/gjallarhorn/test_data_tools_list_commits.py \
  tests/gjallarhorn/test_data_tools_contributor_activity.py \
  tests/gjallarhorn/test_playbook_tools.py \
  tests/gjallarhorn/test_sitrep_tools_sa.py \
  tests/gjallarhorn/test_sitrep_tools_fragos.py -x
```
…exits 0. Full suite `.venv/bin/python -m pytest tests/ -x` green.

## Files in scope

- `gjallarhorn/agent/tool_executor.py` (NEW) — `ToolExecutor(user, project)`. See issue #65 §B for the verbatim class body. `WRITE_TOOLS = frozenset({'create_frago', 'extend_sitawareness', 'create_jira_issue', 'approve_decision'})`. Envelope: `{"success", "result", "error"}` — never raises.
- `gjallarhorn/mcp_tools/data_tools.py` (NEW) — `list_commits(project_id, from_dt, to_dt, limit=200)` queries `ingestion.Increment.objects.filter(project_id=…, kind='commit', committed_at__gte=from_dt, committed_at__lt=to_dt)`. Returns list of `{sha, author_email, message, committed_at}` dicts. `get_contributor_activity(project_id, from_dt, to_dt)` returns `[{email, commit_count}]` sorted desc.
- `gjallarhorn/mcp_tools/playbook_tools.py` (NEW) — `get_active_playbook(project_id)` returns `{workflow_markdown, version_number, playbook_id}` or raises `ValueError` if no Playbook assigned (executor wraps to envelope).
- `gjallarhorn/mcp_tools/sitrep_tools.py` (NEW) — `get_active_situational_awareness(project_id)` returns `{entries: [...], version}` or `{}` if none. `list_active_fragos(project_id, at_dt)` returns `[{id, title, body}]` for FRAGOs where `is_active=True AND effective_from ≤ at_dt AND (effective_to IS NULL OR effective_to > at_dt)`.
- `gjallarhorn/mcp_tools/__init__.py` — re-export tool functions for ergonomic imports.
- `gjallarhorn/services/factory.py` (NEW) — `build_executor(user, project) -> ToolExecutor` instantiates the executor and registers all 5 read tools by name (`list_commits`, `get_contributor_activity`, `get_active_playbook`, `get_active_situational_awareness`, `list_active_fragos`).
- `gjallarhorn/services/__init__.py` — export `build_executor`.

## Do not touch

- `gjallarhorn/agent/agent.py` — T-AGENT owns the agent.
- `gjallarhorn/llm/*` — T-LLM owns the LLM layer.
- Any test file under `tests/gjallarhorn/`.
- Any model file in `ingestion/`, `playbooks/`, `sitrep/`. If a field is
  missing, **stop** and flag — adding fields is out of scope.

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-TOOLS-tool-executor

# … implement …

.venv/bin/python -m pytest tests/gjallarhorn/test_tool_executor_envelope.py tests/gjallarhorn/test_data_tools_list_commits.py tests/gjallarhorn/test_data_tools_contributor_activity.py tests/gjallarhorn/test_playbook_tools.py tests/gjallarhorn/test_sitrep_tools_sa.py tests/gjallarhorn/test_sitrep_tools_fragos.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(gjallarhorn): ToolExecutor + narrative-phase read tools"
git push -u origin factory/T-TOOLS-tool-executor

glab mr create \
  --source-branch factory/T-TOOLS-tool-executor \
  --target-branch main \
  --title "feat(gjallarhorn): ToolExecutor + 5 narrative-phase read tools" \
  --description "Implements GJLR-TOOLS (#65). 6 RED test files go GREEN.

Closes #65" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest \
  tests/gjallarhorn/test_tool_executor_envelope.py \
  tests/gjallarhorn/test_data_tools_list_commits.py \
  tests/gjallarhorn/test_data_tools_contributor_activity.py \
  tests/gjallarhorn/test_playbook_tools.py \
  tests/gjallarhorn/test_sitrep_tools_sa.py \
  tests/gjallarhorn/test_sitrep_tools_fragos.py -x
# expect: 0 failed
```

## Do not

- Do NOT implement write tools — return failure envelope only.
- Do NOT raise from tool functions to the caller — `ToolExecutor.execute()`
  swallows and wraps everything. Tool functions raise normally; the executor
  is the only thing that swallows.
- Do NOT query without `project_id` — cross-project leakage is a regression.
- Do NOT add `async`/`await`.

# Result

status:
branch:
mr:
commit_sha:
