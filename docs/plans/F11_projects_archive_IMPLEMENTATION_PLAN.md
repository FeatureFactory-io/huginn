# F11 PROJECTS-ARCHIVE_PROJECT-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ingestion/models/__init__.py](../../../ingestion/models/__init__.py) | Project.status | ARCHIVED wired in implementation; service stub only here |
| [ui/services/projects_service.py](../../../ui/services/projects_service.py) | `archive_project` | POST → `NotImplementedError` |
| [ui/views/projects.py](../../../ui/views/projects.py) | ProjectsArchiveView | GET confirm + POST |
| [ui/templates/ui/projects/archive.html](../../../ui/templates/ui/projects/archive.html) | full | |
| [ui/templates/ui/projects/detail.html](../../../ui/templates/ui/projects/detail.html) | Archive link | |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | `/projects/<pk>/archive/` |
| [docs/features/act-2-projects/projects-archive.feature](../../features/act-2-projects/projects-archive.feature) | full | Dashboard filters deferred |

## Do Not Do

- Do NOT implement modal focus-trap (feature accessibility) until UI passes acceptance for this screen.

## Implementation Steps (skeleton)

1. `ProjectsArchiveView` confirmation GET; POST → `archive_project` (raises until implementation).
2. Detail links to archive route.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_projects_archive.py -x -q
```
