# ACT3-PLAYBOOK-07: Playbook detail (VIEW) — strip Tables panel and Validate Playbook action

## Scope
After ACT3-PLAYBOOK-05 (model migration) lands, remove from the Playbook detail view:
- The **Tables panel** section from `ui/templates/ui/playbooks/detail.html`
- The **Dimensions column** from the Variables read-only table in `detail.html`
- The **Validate Playbook** button and results block from `detail.html`
- The POST validate handler from `PlaybooksDetailView`
- The `versions__tables` prefetch from the detail view query

Also clean up mockup view (`ui/views/mockups/playbooks.py`) mock detail data.

## @reimplement scenarios implemented by this issue

- `PLAYBOOKS-VIEW_PLAYBOOK-05` — Variables panel lists Variables with columns: Name, Abbrev, Calculating, Interpreting, Hover (no Dimensions)
- `PLAYBOOKS-VIEW_PLAYBOOK-06` — Empty-state copy for zero Variables
- `PLAYBOOKS-VIEW_PLAYBOOK-12` — Older version snapshot shows Workflow + Variables (no Tables)
- `PLAYBOOKS-VIEW_PLAYBOOK-13` — Compare with current shows diff of Workflow + Variables sections (no Tables)
- `PLAYBOOKS-VIEW_PLAYBOOK-22` — Top actions are Clone and Edit only (no Validate Playbook)
- `PLAYBOOKS-VIEW_PLAYBOOK-23` — Clone opens Create pre-filled with Variables (no Tables)
- `PLAYBOOKS-EDIT_PLAYBOOK-14` — Removing a Variable does NOT delete historical VariableDatapoint rows; Variables tab still renders historical diagrams
- `PLAYBOOKS-LIST+FIND-19` — Clone from row action opens Create pre-filled with Variables (no Tables)

---

## Prerequisites
- ACT3-PLAYBOOK-05 must be merged first.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ui/templates/ui/playbooks/detail.html` | 24–30 | Validate Playbook `<form>` button — delete entirely |
| `ui/templates/ui/playbooks/detail.html` | 40–52 | `{% if validate_results is not None %}` block — delete entirely |
| `ui/templates/ui/playbooks/detail.html` | 84–103 | Variables section — remove `<th>Dimensions</th>` (line 88), `<td>{{ v.dimensions_display }}</td>` (line 97), update `colspan` on empty row (line 100) |
| `ui/templates/ui/playbooks/detail.html` | 106–124 | Tables `<section>` — delete entirely |
| `ui/views/playbooks.py` | 196–252 | `PlaybooksDetailView` — remove `versions__tables` prefetch; remove `validate_results` from context; remove `GET ?validate=1` logic; simplify POST to redirect unconditionally |

---

## Do Not Do

- Do NOT create a new Django app
- Do NOT add async
- Do NOT modify the CREATE or EDIT views — that is ACT3-PLAYBOOK-06
- Do NOT remove the Versions tab or version log — only remove Tables and Validate
- Do NOT remove the "Compare with current" button — it stays disabled (`disabled title="Coming soon"`)

---

## SAO.md Sections That Apply

- §1 Application Blocks: `ui/` reads from all apps; `playbooks/` owns model layer
- §2 Integration & API Design: Web UI only, no REST API; all interactions are HTMX or form POST
- §5 Test Strategy: view tests via Django test client; assert status codes and template content

---

## Implementation Plan

### Step 1 — Update `ui/templates/ui/playbooks/detail.html`

1. Delete lines 24–30: the `<form method="post">` containing the Validate Playbook button.
2. Delete lines 40–52: the `{% if validate_results is not None %}` alert block.
3. In the Variables table (lines 84–103):
   - Remove `<th>Dimensions</th>` from the `<thead>` (line 88).
   - Remove `<td class="small">{{ v.dimensions_display }}</td>` from the `{% for v in snapshot.variables %}` loop (line 97).
   - Update the empty-state `<td colspan="6"` → `<td colspan="5"` (line 100).
   - Update empty-state text to: `"This Playbook has no Variables yet — only Vitals will render on assigned Projects."` (per PLAYBOOKS-VIEW_PLAYBOOK-06).
4. Delete lines 106–124: the entire Tables `<section>`.

### Step 2 — Update `ui/views/playbooks.py` — `PlaybooksDetailView`

**GET handler (lines 199–246):**
- Remove `"versions__tables"` from `prefetch_related(...)` call.
- Remove `validate_results: list[str] | None = None` block (lines 229–231).
- Remove `validate_results` from `ctx` dict.
- Remove `version_total` from `ctx` (only used in validate_results message).
- Remove `catalog_drift_messages_all_versions` import (from `ui.services.playbooks_service`).

**POST handler (lines 248–252):**
- Simplify to always redirect to detail without validate:
  ```python
  def post(self, request, pk):
      return redirect(reverse("playbooks-detail", args=[pk]))
  ```
- Remove `urlencode` import if no longer used.

**snapshot building:**
- Remove `_annotate_table_display(snapshot)` call (line 220) — function no longer exists after ACT3-PLAYBOOK-05.

**Imports to clean up at top of `views/playbooks.py`** (if still present after PLAYBOOK-06):
- `catalog_drift_messages_all_versions`
- `urlencode` (from `urllib.parse`) — remove if only used in validate redirect

### Step 3 — Update `ui/views/mockups/playbooks.py`

(In case some `tables`/`catalog_drift` keys remain after PLAYBOOK-06 for the mockup view endpoint):
- Remove `show_catalog_drift`, `catalog_drift_banner`, `tables` from all `MOCK_PLAYBOOK_DETAIL` dicts (IDs 1–4) if not already done.
- In `playbooks_view` view: remove any `catalog_drift_banner` context passing.

### Step 4 — Write view tests

File: `tests/integration/test_playbooks_detail_view.py` (new or extend existing):

- `test_detail_no_validate_button`: GET `/playbooks/<pk>/`; assert `data-testid="playbooks-validate-btn"` NOT in body.
- `test_detail_no_tables_section`: GET `/playbooks/<pk>/`; assert `data-testid` for tables NOT in body; assert "Tables" NOT in body (as a heading).
- `test_detail_variables_no_dimensions_column`: GET; assert "Dimensions" NOT in Variables section.
- `test_detail_variables_empty_state_copy`: GET for a Playbook with 0 variables; assert "This Playbook has no Variables yet" in body.
- `test_detail_clone_button_present`: GET; assert `data-testid="playbooks-clone-btn"` in body.
- `test_detail_post_redirects_to_detail`: POST to detail; assert 302 redirect to detail URL.

### Step 5 — Checkpoint

```bash
pytest tests/integration/test_playbooks_detail_view.py tests/integration/test_playbooks_operational.py -x
```

### Step 6 — Full suite

```bash
pytest tests/ -x
```

### Step 7 — Commit

```
feat(playbooks): strip Tables panel and Validate Playbook from detail view

Removes the Tables section and Dimensions column from the read-only
Variables table in detail.html.  Removes the Validate Playbook button
and validate_results logic from PlaybooksDetailView.  Top actions are
now Clone and Edit only.
```

---

## Acceptance Criteria

- [ ] `pytest tests/integration/test_playbooks_detail_view.py tests/integration/test_playbooks_operational.py -x` passes
- [ ] No regressions: `pytest tests/ -x` passes
- [ ] GET `/playbooks/<pk>/` body does NOT contain "Validate Playbook" button or "Tables" section
- [ ] Variables table in detail has exactly 5 columns: Name, Abbrev, Calculating, Interpreting, Hover
- [ ] Clone button is present; clicking it navigates to Create pre-filled with Variables (verified by test)
