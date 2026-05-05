# F02 DATASOURCES-LIST+FIND-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [docs/architecture/SAO.md](../../architecture/SAO.md) | 22–34 | `ingestion/` owns connectors + raw models |
| [huginn/settings/base.py](../../huginn/settings/base.py) | INSTALLED_APPS | `ingestion` registered |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | Extend with `datasources/` routes |
| [docs/features/act-1-datasources/datasources-list-find.feature](../../features/act-1-datasources/datasources-list-find.feature) | full | Rows, filters, badges — skeleton shows table shell |

## Do Not Do

- Do NOT freeze or edit mockup HTML under `ui/templates/ui/mockups/**` (design reference only).
- Do NOT add `FOB-*` identifiers.
- Do NOT put list business rules in the view — queryset only; services in later acts as needed.

## SAO.md Sections That Apply

- §1 Application Blocks — ingestion vs ui boundaries
- §3 Code Organization — templates under `ui/templates/ui/`

## Implementation Steps (skeleton)

1. `ingestion.models.DataSource` minimal fields: name, type, base_url, status, token metadata placeholders, timestamps.
2. `ingestion.admin` register for admin visibility.
3. Migration `0001_initial` (DataSource only).
4. `DataSourcesListView` @ `GET /datasources/` — `login_required`, empty/provided queryset, count badge.
5. Template `ui/datasources/list.html` — heading, table headers, empty state; row actions as disabled or text until F03–F06.
6. Integration test: logged-in client GET 200 + title.

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_datasources_list_find.py -x -q
```
