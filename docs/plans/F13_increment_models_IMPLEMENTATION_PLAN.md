# F13 — Increment, Contributor, IngestionRun models + DTOs (BPE)

**gitlab_iid:** 26
**Depends on:** F12 merged or scenarios frozen

## Context Map

| File | Note |
|------|------|
| [ingestion/models/__init__.py](../../ingestion/models/__init__.py) | Add Contributor, Increment, IngestionRun |
| [ingestion/domain/increments.py](../../ingestion/domain/increments.py) | New — IncrementDTO ABC, CommitIncrementDTO |
| [ingestion/admin.py](../../ingestion/admin.py) | Register new models |
| [tests/factories.py](../../tests/factories.py) | Factories for new models |

## Do Not Do

- Do NOT add SyncEngine or Celery in F13
- Do NOT add REST API endpoints
- Do NOT add `python-gitlab` — HTTP client stays in `integrations/`
- Do NOT create a new Django app

## SAO.md Sections That Apply

- §1 Application Blocks — `ingestion/` owns raw models
- §4 Data Architecture — append-only IngestionRun; unique (project, kind, external_id) on Increment
- §3 Code Organization — `snake_case` Python

## Implementation Plan

1. Add `ingestion/domain/increments.py` with `IncrementKind`, `ContributorDTO`, `IncrementDTO`, `CommitIncrementDTO`.
2. Add `Contributor` (FK DataSource, email, name, handle, timestamps); `Meta.constraints` UniqueConstraint(datasource, email).
3. Add `Increment` (FK project, datasource nullable, kind, external_id, occurred_at, contributor nullable, summary, payload JSONField, created_at); UniqueConstraint(project, kind, external_id); indexes.
4. Add `IngestionRun` (FK project, started_at, finished_at, status, cursor_to nullable, increments_ingested, contributors_touched, error_message, datasource nullable).
5. `makemigrations` → `0006_*.py`.
6. Register all three in admin.
7. Extend `tests/factories.py`.
8. Unit tests: DTO `stable_key`; model uniqueness; IngestionRun defaults.

## Checkpoint

`pytest tests/unit/test_increment_dto.py tests/unit/test_increment_model.py tests/unit/test_contributor_model.py tests/unit/test_ingestion_run_model.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint passes
- [ ] `pytest tests/ -x -q` passes
- [ ] `ruff check .` passes
