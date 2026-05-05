# F10 PROJECTS-EDIT_PROJECT-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/services/projects_service.py](../../../ui/services/projects_service.py) | `update_project_configuration` | POST → `NotImplementedError` |
| [ui/views/projects.py](../../../ui/views/projects.py) | ProjectsEditView | |
| [ui/templates/ui/projects/edit.html](../../../ui/templates/ui/projects/edit.html) | full | Display name + read-only source path shell |
| [ui/templates/ui/projects/detail.html](../../../ui/templates/ui/projects/detail.html) | Edit link | |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | `/projects/<pk>/edit/` |
| [docs/features/act-2-projects/projects-edit.feature](../../features/act-2-projects/projects-edit.feature) | full | Playbook + schedule deferred |

## Do Not Do

- Do NOT implement playbook dropdown or sync schedule persistence in this footprint.

## Implementation Steps (skeleton)

1. `ProjectsEditView` GET pre-populates display name; POST calls `update_project_configuration` (raises until MIT).
2. Detail surface links to edit route.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_projects_edit.py -x -q
```
