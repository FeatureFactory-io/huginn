# ACT3-PLAYBOOK-05: Remove `PlaybookVariable.dimensions` and `PlaybookTable` — model + service layer

## Scope
Remove the deprecated `PlaybookVariable.dimensions` JSONField and the entire `PlaybookTable` model from the `playbooks` app. Remove the `catalog.py` slicer-validation module. Strip all dependent logic from the service layer (`ui/services/playbooks_service.py`). This is a prerequisite for ACT3-PLAYBOOK-06 and ACT3-PLAYBOOK-07.

## @reimplement scenarios unblocked by this issue
All `@reimplement` scenarios in `act-3-playbooks/` and `act-2-projects/` — the model deletion makes the schema consistent with the new architecture.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `playbooks/models.py` | 60–74 | `PlaybookVariable` — remove `dimensions = models.JSONField(default=list)` (line 74); do NOT touch other fields |
| `playbooks/models.py` | 83–107 | `PlaybookTable` class — delete entirely; a new migration must drop the table |
| `playbooks/migrations/0002_seed_featurefactory_playbook.py` | 18–130 | Seed data migration — remove `dimensions` key from every dict in `VARIABLE_ROWS`; remove all `PlaybookTable.objects.create()` calls; remove `PlaybookTable` from `apps.get_model` |
| `tests/factories.py` | 49–60 | `PlaybookVariableFactory` has `dimensions`; `PlaybookTableFactory` class — remove both |
| `ui/services/playbooks_service.py` | 71–192 | `_split_dimensions`, `parse_tables_from_post`, `_persist_table_rows`, `_annotate_table_display`, `catalog_drift_messages_all_versions`, `editor_snapshot_from_version` (tables/dimensions section) — strip all table/dimension handling |

---

## Do Not Do

- Do NOT create a new Django app
- Do NOT add async
- Do NOT add a manager/repository layer — services call ORM directly
- Do NOT use `--fake` to bypass migrations — write a proper schema migration
- Do NOT remove `PlaybookVariable` itself — only its `dimensions` field
- Do NOT keep `catalog.py` — delete the entire file; it only serves `PlaybookTable` validation

---

## SAO.md Sections That Apply

- §1 Application Blocks: `playbooks/` owns the model layer; `ui/services/` calls ORM directly, no manager layer
- §4 Data Architecture: Django migrations (numbered, tracked in VCS); expand-contract pattern for breaking schema changes; `factory_boy` for test data

---

## Implementation Plan

### Step 1 — Write migration `0003`

Create `playbooks/migrations/0003_remove_playbookvariable_dimensions_and_playbooktable.py`:

```python
from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ("playbooks", "0002_seed_featurefactory_playbook"),
    ]
    operations = [
        migrations.RemoveField(
            model_name="playbookvariable",
            name="dimensions",
        ),
        migrations.DeleteModel(
            name="PlaybookTable",
        ),
    ]
```

Run `pytest tests/ -x` — should fail on any test that references `PlaybookTable` or `dimensions`.

### Step 2 — Update `playbooks/models.py`

- Remove `dimensions = models.JSONField(default=list)` from `PlaybookVariable` (line 74).
- Delete the entire `PlaybookTable` class (lines 83–107).

### Step 3 — Delete `playbooks/catalog.py`

Delete the file entirely. It exists only to validate `PlaybookTable` slicers.

### Step 4 — Update `playbooks/admin.py`

- Remove `PlaybookTable` from import on line 5.
- Delete `PlaybookTableInline` class (lines 13–16).
- Remove `PlaybookTableInline` from `PlaybookVersionAdmin.inlines` (line 36).

### Step 5 — Update seed migration `0002`

In `playbooks/migrations/0002_seed_featurefactory_playbook.py`:

- Remove `"dimensions": [...]` from every dict in `VARIABLE_ROWS` (lines 26, 35, 44, 52, 59, 71, 80).
- Remove `PlaybookTable = apps.get_model("playbooks", "PlaybookTable")` from `seed_featurefactory_playbook`.
- Remove all three `PlaybookTable.objects.create(...)` calls (lines 109–129).
- Update the docstring/description to reflect "seven Variables" (no tables).

### Step 6 — Update `tests/factories.py`

- Remove `PlaybookTable` from `playbooks.models` import.
- Remove `dimensions = factory.LazyFunction(...)` from `PlaybookVariableFactory`.
- Delete `PlaybookTableFactory` class entirely.

### Step 7 — Update `tests/unit/test_playbook_models.py`

- Remove `PlaybookTable` from `playbooks.models` import.
- Remove `PlaybookTableFactory` from `tests.factories` import.
- Delete `test_tables_use_entity_choices` test function.

### Step 8 — Update `ui/services/playbooks_service.py`

Remove all `PlaybookTable`/catalog/dimensions-related code:

- Remove imports: `PlaybookTable` from models, `scan_version_for_drift`/`validate_table_row` from catalog.
- Delete functions: `_split_dimensions`, `parse_tables_from_post`, `_persist_table_rows`, `_annotate_table_display`, `catalog_drift_messages_all_versions`.
- Update `editor_snapshot_from_version`:
  - Remove the `.values("dimensions")` from the variables query.
  - Remove the `tbls = list(version.tables...)` query.
  - Remove `var_rows` dimensions processing; return simple dicts from `.values(...)`.
  - Remove `"tables"` key from return dict.
- Update `create_playbook_with_version`:
  - Remove `tables: list[dict[str, Any]]` parameter.
  - Remove `_persist_table_rows(ver, tables)` call.
- Update `append_playbook_version`:
  - Remove `tables: list[dict[str, Any]]` parameter.
  - Remove `_persist_table_rows(ver, tables)` call.

### Step 9 — Write tests

File: `tests/unit/test_playbook_models.py` — add:
- `test_playbook_variable_has_no_dimensions_field`: assert `PlaybookVariable` has no `dimensions` attribute.
- `test_playbook_table_does_not_exist`: assert `PlaybookTable` is not importable from `playbooks.models`.

File: `tests/unit/test_playbooks_service.py` (new):
- `test_editor_snapshot_no_dimensions`: create a `PlaybookVariable` via factory, call `editor_snapshot_from_version`, assert result has no `dimensions` key.
- `test_create_playbook_with_version_no_tables`: call `create_playbook_with_version(variables=[...])` — no `tables` param; assert version created with variables; no PlaybookTable rows.
- `test_append_playbook_version_no_tables`: similarly for `append_playbook_version`.

### Step 10 — Run full test suite

```bash
pytest tests/ -x
```

All must pass.

### Step 11 — Commit

```
feat(playbooks): remove PlaybookVariable.dimensions and PlaybookTable model

Drops the deprecated dimensions JSONField from PlaybookVariable and
removes the PlaybookTable model entirely.  Deletes catalog.py (slicer
validation).  Strips all table/dimension handling from playbooks_service.
Migration 0003 removes the schema objects.
```

---

## Acceptance Criteria

- [ ] `pytest tests/unit/test_playbook_models.py tests/unit/test_playbooks_service.py tests/integration/test_playbooks_operational.py -x` passes
- [ ] No regressions: `pytest tests/ -x` passes
- [ ] `python manage.py migrate` applies migration 0003 without errors on a fresh DB
- [ ] Admin for `PlaybookVersion` no longer shows a Tables inline
