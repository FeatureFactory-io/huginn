# F16 — Sync Celery tasks + beat schedule (BPE)

**gitlab_iid:** 29
**Depends on:** F15

## Context Map

| File | Note |
|------|------|
| [ingestion/tasks.py](../../ingestion/tasks.py) | `sync_project`, `sync_due_projects` |
| [ui/services/projects_service.py](../../ui/services/projects_service.py) | Call real sync task |
| [huginn/settings/test.py](../../huginn/settings/test.py) | CELERY_TASK_ALWAYS_EAGER if needed |

## Do Not Do

- Do NOT leave `sync_project_placeholder` as the only task — replace implementation or alias rename with deprecation comment

## SAO.md Sections That Apply

- §6 Performance — Celery beat
- §7 Celery job failure policy

## Implementation Plan

1. `@shared_task(name="ingestion.sync_project") def sync_project(project_id: int)`: call `SyncEngine().run_for_project(project_id)`; keep old name `ingestion.sync_project_placeholder` as thin wrapper calling same for one release OR migrate all call sites to `sync_project`.
2. Implement `sync_due_projects`: iterate active projects; `_is_due(project, now)` using `sync_schedule` + `last_sync_at` (hourly: >1h, every_6h: >6h, daily: >24h).
3. Data migration: `django_celery_beat` IntervalSchedule 15 min + PeriodicTask for `ingestion.sync_due_projects`.
4. Integration test: mock GitLab with responses, `CELERY_TASK_ALWAYS_EAGER=True`, import triggers sync or call task directly; assert Increment rows + IngestionRun.

## Checkpoint

`pytest tests/integration/test_sync_engine_e2e.py tests/unit/test_sync_due_projects.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint + full suite green
