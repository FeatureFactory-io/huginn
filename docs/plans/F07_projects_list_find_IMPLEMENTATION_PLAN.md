# F07 PROJECTS-LIST+FIND-1 — Implementation Plan (BPE-01 skeleton)

## Context Map

| File | Lines | Note |
| --- | --- | --- |
| [ingestion/models/__init__.py](../../ingestion/models/__init__.py) | Project | Rows listable after implementation; skeleton keeps `projects=[]` in view |
| [ingestion/admin.py](../../../ingestion/admin.py) | ProjectAdmin | Register for ops visibility |
| [ingestion/migrations/0002_project_model.py](../../../ingestion/migrations/0002_project_model.py) | full | Depends on DataSource FK |
| [ui/views/projects.py](../../../ui/views/projects.py) | ProjectsListView | `login_required`, empty shell context |
| [ui/templates/ui/projects/list.html](../../../ui/templates/ui/projects/list.html) | full | Heading, count via length filter |
| [ui/urls.py](../../../ui/urls.py) | urlpatterns | `GET /projects/` |
| [docs/features/act-2-projects/projects-list-find.feature](../../features/act-2-projects/projects-list-find.feature) | full | Filters/columns deferred |

## Do Not Do

- Do NOT populate list from ORM in the skeleton slice (implementation wires `ProjectsService` + queryset rules).
- Do NOT add `FOB-*` identifiers.
- Do NOT edit `ui/templates/ui/mockups/**` for this footprint.

## SAO.md Sections That Apply

- Application blocks — `ingestion` owns `Project`; `ui` renders shells.

## Implementation Steps (skeleton)

1. `Project` model + migration + admin registration.
2. `ProjectsListView` @ `GET /projects/` — `login_required`, render with `projects=[]`.
3. Template `ui/projects/list.html` — title, count badge from `|length`, empty state.
4. Integration tests: GET 200 + title; DB row does **not** appear on list (skeleton).

## Checkpoint

```bash
.venv/bin/python -m pytest tests/integration/test_projects_list_find.py -x -q
```
