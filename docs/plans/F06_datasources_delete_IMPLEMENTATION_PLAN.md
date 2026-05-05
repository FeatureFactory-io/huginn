# F06 DATASOURCES-DELETE_DATASOURCE-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ui/services/datasources_service.py](../../../ui/services/datasources_service.py) | full | Add `soft_delete_gitlab_source` |
| [docs/features/act-1-datasources/datasources-delete.feature](../../features/act-1-datasources/datasources-delete.feature) | full | Modal UX — page confirm for skeleton |

## Do Not Do

- Do NOT cascade-delete projects in skeleton without human-specified policy.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_datasources_delete.py -x -q
```
