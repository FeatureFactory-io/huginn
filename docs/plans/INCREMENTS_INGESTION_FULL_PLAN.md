# Increments & sync engine — full rollout (BPE-01)

**Milestone:** Datasources & Projects (`dp2580/huginn`)
**Workflow:** `.cursor/workflows/BPE-reference/BPE-reference-01-Plan_Feature.md`
**GitLab:** `glab` CLI (issue titles `Act 2 Projects — Phase I–O (F12–F18)`)
**Dependency chain:** F12 (docs) → F13 (models) → F14 (SyncEngine + adapter ABC) → F15 (GitLab adapter) → F16 (Celery + beat) → F17 (Vitals tabs) → F18 (Increments tab UI + tests)

## Artifacts

| Phase | Doc | Executable checkpoint |
|-------|-----|----------------------|
| I / F12 | [F12_sync_specification_IMPLEMENTATION_PLAN.md](F12_sync_specification_IMPLEMENTATION_PLAN.md) | Docs review (no pytest) |
| J / F13 | [F13_increment_models_IMPLEMENTATION_PLAN.md](F13_increment_models_IMPLEMENTATION_PLAN.md) | `pytest tests/unit/test_increment_dto.py tests/unit/test_increment_model.py tests/unit/test_contributor_model.py tests/unit/test_ingestion_run_model.py -x -q` |
| K / F14 | [F14_sync_engine_core_IMPLEMENTATION_PLAN.md](F14_sync_engine_core_IMPLEMENTATION_PLAN.md) | `pytest tests/unit/test_sync_engine.py -x -q` |
| L / F15 | [F15_gitlab_commit_adapter_IMPLEMENTATION_PLAN.md](F15_gitlab_commit_adapter_IMPLEMENTATION_PLAN.md) | `pytest tests/unit/test_gitlab_commit_adapter.py tests/unit/test_gitlab_client.py -x -q` |
| M / F16 | [F16_sync_tasks_beat_IMPLEMENTATION_PLAN.md](F16_sync_tasks_beat_IMPLEMENTATION_PLAN.md) | `pytest tests/integration/test_sync_engine_e2e.py tests/unit/test_sync_due_projects.py -x -q` |
| N / F17 | [F17_projects_view_tabs_IMPLEMENTATION_PLAN.md](F17_projects_view_tabs_IMPLEMENTATION_PLAN.md) | `pytest tests/integration/test_projects_view_vitals_tab.py -x -q` |
| O / F18 | [F18_projects_increments_tab_IMPLEMENTATION_PLAN.md](F18_projects_increments_tab_IMPLEMENTATION_PLAN.md) | `pytest tests/integration/test_projects_view_increments_tab.py -x -q` |

## GitLab issues

See [GITLAB_ISSUES_INCREMENTS_INGESTION.md](GITLAB_ISSUES_INCREMENTS_INGESTION.md) and `docs/plans/.gitlab-issue-bodies/F{12..18}.md`.

## Definition of done (program)

- All seven issues closed; `pytest tests/ -x -q` green.
- Non-archived Project after successful sync shows commits on Increments tab (default Last 14 days).
- `IngestionRun` rows recorded per sync; failures set `Project.sync_state=error`.
