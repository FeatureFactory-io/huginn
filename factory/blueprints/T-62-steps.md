# Blueprint T-62-steps — SITREP-LIST+FIND-1 step definitions

## Design
Translate all 22 scenarios in `sitrep-list-find.feature` into pytest test stubs.
Each stub calls `pytest.fail("RED")`. No production code.

## Files touched
- `tests/ui/test_sitrep_list_scenarios.py` — new, 22 stubs

Note: list/find tests live in `tests/ui/` (not `tests/gjallarhorn/`) because
they exercise Django views, not the AI backend.

## Naming convention
```
def test_sitrep_list_find_01_page_header(): pytest.fail("RED")
...
def test_sitrep_list_find_22_generate_button_accessible_label(): pytest.fail("RED")
```

## Scenario inventory (from sitrep-list-find.feature)
01: Page header shows Project name
02: Navigate from Project view → SitRep list
06: History table has required columns
07: History sorted newest first by default
08: Row View → SITREP-VIEW_SITREP-1
09: Manual trigger label
10: Auto trigger label
11: Filter by Manual
12: Filter by Auto
13: Filter by date range
14: Filter by Playbook version
15: Generate SitRep button visible
16: Period picker options
17: Since last SitRep disabled when none exists
18: Since last SitRep shows window label
19: Custom period opens datetime picker
20: Preset period fires generate + toast
21: Empty state when no SitReps
22: Generate button accessible label

## Risks
- Scenarios 03, 04, 05 are in sitrep-generate.feature, not this file — do not duplicate.
- Tests use Django test client, not Selenium.
- Scenarios testing HTMX toast (20) should assert response status + response body substring.
