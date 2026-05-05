# F09 PROJECTS-VIEW_PROJECT-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ingestion/models/__init__.py](../../../ingestion/models/__init__.py) | Project | Detail reads via ORM for URL shell |
| [ui/services/projects_service.py](../../../ui/services/projects_service.py) | `enqueue_immediate_project_sync` | POST-only action → `NotImplementedError` |
| [ui/views/projects.py](../../../ui/views/projects.py) | ProjectsDetailView, ProjectsSyncNowView | |
| [ui/templates/ui/projects/detail.html](../../../ui/templates/ui/projects/detail.html) | full | Actions link to F10/F11 routes |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | `/projects/<pk>/`, `/projects/<pk>/sync/` |
| [docs/features/act-2-projects/projects-view.feature](../../features/act-2-projects/projects-view.feature) | full | Recent activity deferred |

## Do Not Do

- Do NOT hydrate Playbook assignment or sync timelines from relational state until schemas exist.

## Implementation Steps (skeleton)

1. `ProjectsDetailView` GET renders `project` resolved with `select_related('datasource')`.
2. `ProjectsSyncNowView` POST validates row exists → `enqueue_immediate_project_sync` (raises until MIT).
3. Detail template: Edit / Archive links; POST form for sync (CSRF).

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_projects_view.py -x -q
```
