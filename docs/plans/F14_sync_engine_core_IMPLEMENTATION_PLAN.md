# F14 — SyncEngine core + DataSourceAdapter ABC (BPE)

**gitlab_iid:** 27
**Depends on:** F13

## Context Map

| File | Note |
|------|------|
| [ingestion/services/sync_engine.py](../../ingestion/services/sync_engine.py) | New orchestrator |
| [ingestion/adapters/base.py](../../ingestion/adapters/base.py) | DataSourceAdapter ABC |
| [ingestion/adapters/__init__.py](../../ingestion/adapters/__init__.py) | ADAPTER_REGISTRY |

## Do Not Do

- Do NOT implement GitLab HTTP in F14 — StubAdapter in tests only
- Do NOT put business logic in `ui/views`
- Do NOT add async views

## SAO.md Sections That Apply

- §1 Ingestion sync engine
- §7 Idempotency — upsert by (project, kind, external_id)

## Implementation Plan

1. `DataSourceAdapter` with `fetch_increments(project, *, since: datetime | None) -> Iterable[IncrementDTO]`.
2. `ADAPTER_REGISTRY` keyed by `DataSource.Type` values.
3. `SyncEngine.__init__(self, registry=None)`.
4. `run_for_project(project_id)`:
   - Load project; skip if archived
   - Coalesce: if IngestionRun with status=running exists for project without finished_at, return early (no parallel run)
   - Create IngestionRun status=running
   - `since = max(last successful run's cursor_to, now-90d)` (constant SYNC_LOOKBACK_DAYS)
   - For each adapter class in registry[ds.type]: instantiate, stream DTOs, upsert Contributor + Increment
   - On success: finalize run success, set cursor_to, counts, project sync_state ACTIVE, last_sync_at
   - On exception: run error_message, project ERROR
5. Unit tests with StubAdapter yielding N DTOs; idempotent second run; error path; archived skip; concurrency no-op

## Checkpoint

`pytest tests/unit/test_sync_engine.py -x -q`

## Acceptance Criteria

- [ ] Checkpoint + full suite green
