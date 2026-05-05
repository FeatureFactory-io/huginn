# F04 DATASOURCES-VIEW_DATASOURCE-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/views/datasources.py](../../../ui/views/datasources.py) | full | Mirror list→detail PK routing |
| [ingestion/models/__init__.py](../../../ingestion/models/__init__.py) | DataSource | Read-only display fields |
| [docs/features/act-1-datasources/datasources-view.feature](../../features/act-1-datasources/datasources-view.feature) | full | Hydrate fields progressively |

## Do Not Do

- Do NOT fetch live GitLab in detail view skeleton.

## SAO Sections That Apply

- §3 Code Organization — Django class-based/template pattern

## Implementation Steps

1. `DataSourcesDetailView` `@login_required`, `pk` lookup.
2. `ui/datasources/detail.html`.
3. URL `datasources/<int:pk>/`.
4. Integration test with seeded `DataSource`.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_datasources_view.py -x -q
```
