---
id: T-63-impl
role: feature-builder
depends_on: [T-61-impl, T-63-steps]
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/63"
branch: feature/sitrep-view-impl
---

# Task T-63-impl — SITREP-VIEW_SITREP-1 production view

## Objective
Implement the SitRep detail view and template. Turn all 31 RED stubs GREEN.

## Blueprint
`factory/blueprints/T-63-impl.md`

## System context
`factory/blueprints/system.md` — "Existing code workers must read"

## Files in scope
```
ui/views/sitrep_views.py                         (modify — add sitrep_detail)
ui/templates/ui/sitrep/view.html                 (new — port from mockup)
ui/urls.py                                       (modify — add detail URL)
tests/ui/test_sitrep_view_scenarios.py           (modify — implement 31 stubs GREEN)
```
Mockup to read (do not modify): `ui/templates/ui/mockups/sitrep/view.html`

## Step-by-step
1. Read `ui/templates/ui/mockups/sitrep/view.html` — note all data-testid attrs and section structure.
2. Read `docs/features/act-5-sitrep/sitrep-view.feature` for exact text strings and testids.
3. Implement `sitrep_detail` view in `ui/views/sitrep_views.py`.
4. Port mockup → `ui/templates/ui/sitrep/view.html`.
5. Wire URL `projects/<slug>/sitreps/<int:pk>/`.
6. Implement 31 test stubs (Django test client).
7. Run checkpoint.
8. Push branch, open MR targeting `feature/sitrep-list-impl`.

## Acceptance criteria (checkpoint)
```
pytest tests/ui/test_sitrep_view_scenarios.py -x
```
All 31 must pass, including:
- `test_sitrep_view_06_no_variables_badge` — data-testid="sitrep-status-badge", text "No Variables", grey class
- `test_sitrep_view_07_mode_badge_semi_auto` — data-testid="sitrep-mode-badge", text "Semi-Auto"
- `test_sitrep_view_13_variables_placeholder` — "Variables will be available in a future release"
- `test_sitrep_view_15_no_decisions_placeholder` — "No Decisions proposed"
- `test_sitrep_view_17_fragos_list_with_link` — FRAGO title + link present in response
- `test_sitrep_view_19_fragos_empty_state` — "No FRAGOs were applied to this assessment"
- `test_sitrep_view_24_open_decisions_btn` — data-testid="sitrep-open-decisions-btn"
- `test_sitrep_view_25_open_variables_btn` — data-testid="sitrep-open-variables-btn"
- `test_sitrep_view_28_no_edit_delete_controls` — "Edit" and "Delete" absent from HTML
- `test_sitrep_view_30_assessed_period_accessible` — visible label for period element
- `test_sitrep_view_31_status_badge_accessible` — accessible name contains "No Variables"

Full suite: `pytest tests/ -x`

## Do not do
- Do NOT use Selenium or Playwright — Django test client only.
- Do NOT implement the Chat link destination — href stub is sufficient.
- Do NOT modify mockup templates or list view (T-62-impl scope).
- Do NOT add Decisions or Variables UI — placeholder text only.

## Allowed tools
`git`, `python`, `pytest`, `ruff`, `manage.py`

## Result
<!-- Worker fills in after completion -->
- Branch pushed:
- MR URL:
- Checkpoint exit code:
- Scenario count green (31):
- Notes:

# Result

status: passed
branch: ""
mr: ""
commit_sha: ""

_(worker: fill branch, merge request IID, commit SHA; set status to failed or blocked if applicable)_
