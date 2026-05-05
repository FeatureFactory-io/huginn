# F08 PROJECTS-IMPORT-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/services/projects_service.py](../../../ui/services/projects_service.py) | new | Snapshot + persist → `NotImplementedError` |
| [ui/views/projects.py](../../../ui/views/projects.py) | ProjectsImportView | GET shell; POST delegates to service |
| [ui/templates/ui/projects/import.html](../../../ui/templates/ui/projects/import.html) | full | Breadcrumb back to list |
| [ui/templates/ui/projects/list.html](../../../ui/templates/ui/projects/list.html) | Import link | |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | `projects/import/` |
| [docs/features/act-2-projects/projects-import.feature](../../features/act-2-projects/projects-import.feature) | full | API + table behaviour deferred |

## Do Not Do

- Do NOT call live GitLab in tests or skeleton code paths.
- Do NOT add `FOB-*` identifiers.

## SAO.md Sections That Apply

- ingestion vs ui separation — remote fetching belongs behind service + integrations in MIT.

## Implementation Steps (skeleton)

1. `ProjectsService.load_remote_projects_snapshot` / `persist_imported_project_selection` → `NotImplementedError`.
2. `ProjectsImportView` — GET informational shell; POST calls `persist_imported_project_selection` (raises until MIT).
3. Link from projects list to import route.
4. Integration tests: GET 200; POST propagates `NotImplementedError`.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_projects_import.py -x -q
```
