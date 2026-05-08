# ACT3-PLAYBOOK-06: Playbook editor (CREATE + EDIT) — strip Tables section and Dimensions column

## Scope
After the model migration from ACT3-PLAYBOOK-05 lands, remove:
- The Tables section (`<section>` 4) from `_editor_form.html`
- The Dimensions column from the Variables table in `_editor_form.html`
- The catalog-drift banner from `_editor_form.html`
- All `table_slots`, `entity_choices`, `catalog_drift_banner` references from `PlaybooksCreateView`, `PlaybooksEditView` in `ui/views/playbooks.py`
- Corresponding cleanup in `ui/views/mockups/playbooks.py`

## @reimplement scenarios implemented by this issue

- `PLAYBOOKS-CREATE_PLAYBOOK-02` — form has three regions (Metadata, Workflow, Variables)
- `PLAYBOOKS-CREATE_PLAYBOOK-09` — Add Variable inserts editable row
- `PLAYBOOKS-CREATE_PLAYBOOK-10` — Variable row has documented columns (no Dimensions)
- `PLAYBOOKS-CREATE_PLAYBOOK-11` — Donland captures "Commits today" Variable
- `PLAYBOOKS-CREATE_PLAYBOOK-12` — Duplicate row action
- `PLAYBOOKS-CREATE_PLAYBOOK-14` — Drag-handle reorders; Variables appear in informer bar and Variables tab in declared order
- `PLAYBOOKS-CREATE_PLAYBOOK-27` — Saving creates v1 and redirects
- `PLAYBOOKS-CREATE_PLAYBOOK-29` — Clone-from-seed prefills Workflow and Variables (no Tables)
- `PLAYBOOKS-CREATE_PLAYBOOK-30` — Full clone + save flow
- `PLAYBOOKS-CREATE_PLAYBOOK-32` — Keyboard reorder
- `PLAYBOOKS-EDIT_PLAYBOOK-01` — Form pre-populated with latest version content (no Tables)
- `PLAYBOOKS-EDIT_PLAYBOOK-13` — Adding a Variable captured in v(N+1)
- `PLAYBOOKS-EDIT_PLAYBOOK-22` — Existing SitReps keep variables_snapshot unchanged

---

## Prerequisites
- ACT3-PLAYBOOK-05 must be merged first (`PlaybookTable` model and service functions deleted).

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ui/templates/ui/playbooks/_editor_form.html` | 8–13 | Catalog-drift banner block — delete entirely |
| `ui/templates/ui/playbooks/_editor_form.html` | 96–130 | Variables table — remove `<th>Dimensions</th>` and corresponding `<td>` input (lines 111–112, 123–124) |
| `ui/templates/ui/playbooks/_editor_form.html` | 132–170 | Tables `<section>` — delete entirely |
| `ui/views/playbooks.py` | 103–193 | `PlaybooksCreateView` — remove `_padded_table_slots`, `entity_choices`, `table_slots` from GET/POST context; remove `parse_tables_from_post` and `tables` handling from POST |
| `ui/views/playbooks.py` | 255–346 | `PlaybooksEditView` — same cleanup; also remove `scan_version_for_drift` / `catalog_drift_banner` / `_annotate_table_display` calls |

---

## Do Not Do

- Do NOT create a new Django app
- Do NOT add async
- Do NOT add a REST API endpoint
- Do NOT modify `PlaybooksDetailView` or `playbooks/detail.html` in this issue — that is ACT3-PLAYBOOK-07
- Do NOT add drag-and-drop JS libraries — use the existing sortable pattern or defer to a follow-up

---

## SAO.md Sections That Apply

- §1 Application Blocks: `ui/` views read from all apps, no business logic; templates are Django server-rendered
- §2 Integration & API Design: Web UI only — no REST API for v1; all interactions are HTMX swaps
- §5 Test Strategy: pytest + Django test client; no E2E; view tests assert status code and template context

---

## Implementation Plan

### Step 1 — Update `_editor_form.html`

1. Delete lines 8–13 (catalog-drift banner `{% if catalog_drift_banner %}...{% endif %}`).
2. In the Variables table header (line 104–112), remove `<th scope="col">Dimensions</th>`.
3. In the Variables table row (lines 116–125), remove the `<td>...<input name="var_{{ idx }}_dimensions">...</td>` cell.
4. Delete lines 132–170 (the entire Tables `<section>` — section 4).
5. Update the section badge in the Variables header from `<span class="badge">3</span>` to remain `3` (it is already 3; just verify the numbering is still correct with only 3 regions).

### Step 2 — Update `ui/views/playbooks.py` — `PlaybooksCreateView`

**GET handler (line 107–145):**
- Remove `_annotate_table_display(snapshot)` call (line 131).
- Remove `table_slots` and `entity_choices` from the `ctx` dict (lines 142–143).

**POST handler (line 147–192):**
- Remove `tbls, terr = parse_tables_from_post(request.POST)` (line 152).
- Remove `*terr` from the `errors` merge (line 153).
- Remove `"tables": tbls` from the `snapshot` dict (line 162).
- Remove `_annotate_table_display(snapshot)` call (line 165).
- Remove `table_slots` and `entity_choices` from both the error ctx and the success path.
- Remove `tables=tbls` from `create_playbook_with_version(...)` call.

Remove the now-unused `_padded_table_slots`, `_annotate_table_display` helpers from the file (if they exist in `views/playbooks.py`; they likely exist in both views and service — confirm the service version was removed in ACT3-PLAYBOOK-05).

**Remove top-level constants:**
- `PAD_TBL_ROWS = 12` (line 34).
- `PlaybookTable` from import (line 19).
- `parse_tables_from_post` from import (line 28).
- `catalog_drift_messages_all_versions` from import (line 24).

### Step 3 — Update `ui/views/playbooks.py` — `PlaybooksEditView`

**GET handler (line 259–285):**
- Remove `scan_version_for_drift` import usage and the `drift_lines` / `banner_txt` computation (lines 264–268).
- Remove `_annotate_table_display(snapshot)` call (line 268).
- Remove `catalog_drift_banner`, `table_slots`, `entity_choices` from `ctx`.

**POST handler (line 287–346):**
- Remove `tbls, terr = parse_tables_from_post(...)` and `*terr`.
- Remove `"tables": tbls` from snapshot dict.
- Remove `scan_version_for_drift` / `banner_txt` computation in POST.
- Remove `_annotate_table_display(snapshot)`.
- Remove `catalog_drift_banner`, `table_slots`, `entity_choices` from both error ctx and success.
- Remove `tables=tbls` from `append_playbook_version(...)` call.

Remove unused imports at the top of `views/playbooks.py`:
- `scan_version_for_drift` from `playbooks.catalog`
- `PlaybookTable` from `playbooks.models`
- `parse_tables_from_post`, `catalog_drift_messages_all_versions` from `ui.services.playbooks_service`

### Step 4 — Update `ui/views/mockups/playbooks.py`

In `MOCK_PLAYBOOK_DETAIL` dicts (IDs 1–4, lines 68–240):
- Remove `"tables": [...]` key from every dict.
- Remove `"show_catalog_drift"` and `"catalog_drift_banner"` keys from every dict.

In `playbooks_create` view (line 257–304):
- Remove `"tables": []` from `empty_form`.
- Remove `"tables": list(src["tables"])` from both `seed`/`clone` branches.

In `playbooks_edit` view (line 322–343):
- Remove `"tables": list(pb["tables"])` from form dict.

### Step 5 — Write view tests

File: `tests/integration/test_playbooks_create_edit_views.py` (new):

- `test_create_form_has_three_regions`: GET `/playbooks/create/`; assert response contains "Metadata", "Workflow", "Variables"; assert "Tables" NOT in body.
- `test_create_form_variables_table_has_no_dimensions_column`: assert "Dimensions" NOT in variables table header.
- `test_create_post_saves_variables_no_tables`: POST with one variable; assert `PlaybookVariable` created; assert no `PlaybookTable` rows.
- `test_edit_form_has_no_catalog_drift_banner`: GET `/playbooks/<pk>/edit/`; assert `data-testid="playbooks-catalog-drift-banner"` NOT in body.
- `test_edit_form_pre_populates_variables`: GET edit; assert variable name from latest version is in body.

### Step 6 — Checkpoint

```bash
pytest tests/integration/test_playbooks_create_edit_views.py tests/integration/test_playbooks_operational.py -x
```

### Step 7 — Full suite

```bash
pytest tests/ -x
```

### Step 8 — Commit

```
feat(playbooks): strip Tables section and Dimensions column from Playbook editor

Removes the Tables region (section 4), Dimensions column in Variables
table, and catalog-drift banner from _editor_form.html.  Strips
table_slots, entity_choices, and catalog-drift logic from
PlaybooksCreateView and PlaybooksEditView.
```

---

## Acceptance Criteria

- [ ] `pytest tests/integration/test_playbooks_create_edit_views.py tests/integration/test_playbooks_operational.py -x` passes
- [ ] No regressions: `pytest tests/ -x` passes
- [ ] GET `/playbooks/create/` response body does NOT contain "Tables" section or "Dimensions" column header
- [ ] POST to create with valid variables saves a Playbook with `PlaybookVariable` rows and no `PlaybookTable` rows
