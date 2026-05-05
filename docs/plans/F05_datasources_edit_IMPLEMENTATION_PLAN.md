# F05 DATASOURCES-EDIT_DATASOURCE-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/services/datasources_service.py](../../../ui/services/datasources_service.py) | full | Add `update_gitlab_source` |
| [ui/views/datasources.py](../../../ui/views/datasources.py) | full | Edit GET/POST |
| [docs/features/act-1-datasources/datasources-edit.feature](../../features/act-1-datasources/datasources-edit.feature) | full | Fields + validation |

## Do Not Do

- Do NOT persist token changes in skeleton without encryption story.

## Implementation Steps

1. `DataSourcesService.update_gitlab_source(...) -> NotImplementedError`.
2. `DataSourcesEditView` + `ui/datasources/edit.html`.
3. URL `datasources/<int:pk>/edit/`.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_datasources_edit.py -x -q
```
