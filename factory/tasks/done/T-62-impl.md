---
id: T-62-impl
role: feature-builder
depends_on: [T-61-impl, T-62-steps]
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/62"
branch: feature/sitrep-list-impl
---

# Task T-62-impl — SITREP-LIST+FIND-1 production view

## Objective
Implement the SitRep list production view and template. Turn all 22 RED stubs GREEN.

## Blueprint
`factory/blueprints/T-62-impl.md`

## System context
`factory/blueprints/system.md` — "Scope constraints" and "Existing code workers must read"

## Files in scope
```
ui/views/sitrep_views.py                         (new)
ui/templates/ui/sitrep/list.html                 (new — port from mockup)
ui/urls.py                                       (modify — add sitrep URL patterns)
tests/ui/test_sitrep_list_scenarios.py           (modify — implement 22 stubs GREEN)
```
Mockup to read (do not modify): `ui/templates/ui/mockups/sitrep/list.html`
Mockup view to read (do not modify): `ui/views/mockups/sitrep.py`

## Step-by-step
1. Read `ui/templates/ui/mockups/sitrep/list.html` and `ui/views/mockups/sitrep.py` — understand layout and context variables.
2. Read `docs/features/act-5-sitrep/sitrep-list-find.feature` for exact data-testid and text requirements.
3. Implement `sitrep_list` view + generate POST handler.
4. Port mockup template → `ui/templates/ui/sitrep/list.html`.
5. Wire URLs.
6. Implement 22 test stubs (Django test client, no Selenium).
7. Run checkpoint.
8. Push branch, open MR targeting `feature/sitrep-generate-impl`.

## Acceptance criteria (checkpoint)
```
pytest tests/ui/test_sitrep_list_scenarios.py -x
```
All 22 must pass, including:
- `test_sitrep_list_find_01_page_header` — response contains "SitReps — atlas-backend"
- `test_sitrep_list_find_07_sorted_newest_first` — first row is most recent
- `test_sitrep_list_find_11_filter_by_manual` — only manual SitReps returned
- `test_sitrep_list_find_15_generate_button_visible` — data-testid="generate-sitrep-btn" in HTML
- `test_sitrep_list_find_17_since_last_disabled` — disabled attribute on option when no prior
- `test_sitrep_list_find_20_preset_fires_generate_toast` — POST → 202, toast text in response
- `test_sitrep_list_find_21_empty_state` — "No SitReps yet." in response when empty
- `test_sitrep_list_find_22_generate_button_accessible_label` — aria-label present

Full suite: `pytest tests/ -x`

## Do not do
- Do NOT use Selenium or Playwright — Django test client only.
- Do NOT modify the mockup templates or views.
- Do NOT implement the SitRep view page (T-63-impl scope).
- Do NOT add SSE (chat-milestone scope).

## Allowed tools
`git`, `python`, `pytest`, `ruff`, `manage.py`

## Result
<!-- Worker fills in after completion -->
- Branch pushed:
- MR URL:
- Checkpoint exit code:
- Scenario count green (22):
- Notes:

# Result

status: passed
branch: ""
mr: ""
commit_sha: ""

_(worker: fill branch, merge request IID, commit SHA; set status to failed or blocked if applicable)_
