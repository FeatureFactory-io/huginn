# F03 DATASOURCES-CREATE_DATASOURCE-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/views/datasources.py](../../../ui/views/datasources.py) | full | Extend with wizard shell `CreateView` |
| [ingestion/models/__init__.py](../../../ingestion/models/__init__.py) | DataSource | Fields target for persisted row when implemented |
| [docs/features/act-1-datasources/datasources-create.feature](../../features/act-1-datasources/datasources-create.feature) | full | Wizard steps — skeleton single-step form |
| [docs/architecture/SAO.md](../../architecture/SAO.md) | 61–66 | GitLab REST via `python-gitlab` eventual client |

## Do Not Do

- Do NOT mutate mockups frozen paths.
- Do NOT hit live GitLab in tests — stub client raises `NotImplementedError`.

## SAO Sections That Apply

- §2 External connectors — GitLab library choice for later fill
- §3 ui vs ingestion — client under `ingestion.integrations`; service orchestrates from `ui.services`

## Implementation Steps (skeleton)

1. `ingestion.integrations.gitlab_client.GitlabClient` thin stub (`verify_token` / helpers → `NotImplementedError`).
2. `DataSourcesService` with `create_gitlab_source`, `test_gitlab_connection` → delegate client / `NotImplementedError`.
3. `DataSourcesCreateView` GET form; POST `action=test-connection` vs save — catch `NotImplementedError` with banner.
4. Template + URL `datasources/create/`.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_datasources_create.py -x -q
```
