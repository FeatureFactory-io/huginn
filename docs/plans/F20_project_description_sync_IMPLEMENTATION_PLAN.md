# F20 — Project Description Sync (Plan Feature, BPE-01)

Branch: `feature/project-description-sync`.

## SAO.md Sections That Apply

- §1 Application Blocks — `ingestion/integrations/` owns external HTTP, services orchestrate; `ui/` reads only.
- §3 Code Organization — extend `ingestion/` and `ui/`; no new Django app.
- §4 Data Architecture — Django migration, expand-only (TextField, blank=True default).
- §5 Test Strategy — pytest, stub HTTP via `unittest.mock.patch` on `urlopen` where needed, `factory_boy`; no E2E.
- §7 Error Handling — metadata refresh failures must not break "Sync now"; graceful degradation.
- §16 Documentation — Sphinx-style docstrings on new public methods.

## Do Not Do

- Do NOT add a new Django app.
- Do NOT call the GitLab API from views or templates — only from `ingestion/integrations/` and orchestration services under `ingestion/services/`.
- Do NOT make metadata-refresh failure abort `Sync now` (graceful — log + continue with sync dispatch).
- Do NOT add a per-sync GitLab `GET /projects/:id` to `SyncEngine.run_for_project` (background scheduled syncs stay metadata-cheap).
- Do NOT mock domain behavior in integration tests — stub transport (`urlopen`) where needed.
- Do NOT add JS — server-rendered template change only.
- Do NOT change the Project PK / unique constraints; expand-only.

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ingestion/models/__init__.py` | Project model | `description = models.TextField(blank=True, default="")`; migration `0008_project_description`. |
| `ingestion/integrations/gitlab_client.py` | `get_project` | `GET /api/v4/projects/:id`, 500-char truncation for description. |
| `ui/services/projects_service.py` | `persist_imported_project_selection` | Pass `description[:500]` into `Project.objects.create`. |
| `ui/views/projects.py` | `ProjectsSyncNowView` | Call `refresh_project_metadata` before enqueue; `ConnectionError` swallowed at service boundary. |
| `ui/templates/ui/projects/detail.html` | Identity card | `data-testid="project-description"`. |
| `ingestion/services/project_metadata.py` | `refresh_project_metadata` | GitLab-only v1; logs and returns on failure. |

## Implementation summary (executed)

1. **Schema:** `Project.description` + migration `0008_project_description`.
2. **Import:** Catalog `description` persisted (max 500 chars).
3. **GitLab:** `GitlabClient.get_project(project_id)` with truncation and HTTP error mapping to `ConnectionError`.
4. **Service:** `ingestion/services/project_metadata.py` — `refresh_project_metadata(project)` updates description, optionally name/source_url/source_path.
5. **Sync now:** `ProjectsSyncNowView` calls refresh before `ProjectsService.enqueue_immediate_project_sync`.
6. **Guard:** Scheduled `SyncEngine` does not touch `Project.description` (integration test asserts).
7. **UI:** Vitals Identity shows Description row; Tactical Plot `_description_for_project` prefers `project.description` over `source_path`.
8. **BDD:** Scenarios appended to `projects-view.feature`, `projects-import.feature`, `projects-sync-engine.feature`.

## Tests

- Unit: `test_project_has_description_field_default_empty`, `test_gitlab_client_get_project_*`.
- Integration: import persists description; refresh metadata; sync now refreshes / tolerates GitLab failure; scheduled sync invariant; Vitals renders description / em dash.

## Checkpoint

```
pytest tests/integration/test_projects_import_persists_description.py \
       tests/integration/test_refresh_project_metadata.py \
       tests/integration/test_projects_sync_now_refreshes_description.py \
       tests/integration/test_scheduled_sync_does_not_refresh_metadata.py \
       tests/integration/test_projects_view_vitals_tab.py \
       tests/unit/test_gitlab_client_get_project.py \
       tests/unit/test_project_model.py -x
```

Full suite: `pytest tests/ -x`
