# Blueprint T-63-steps — SITREP-VIEW_SITREP-1 step definitions

## Design
Translate all 31 scenarios in `sitrep-view.feature` into pytest test stubs.
Each stub calls `pytest.fail("RED")`. No production code.

## Files touched
- `tests/ui/test_sitrep_view_scenarios.py` — new, 31 stubs

## Naming convention
```
def test_sitrep_view_01_header_project_and_date(): pytest.fail("RED")
...
def test_sitrep_view_31_status_badge_accessible(): pytest.fail("RED")
```

## Scenario inventory (from sitrep-view.feature)
01: Header shows Project name and date
02: Header shows assessed period (data-testid="sitrep-assessed-period")
03: Header Trigger badge Auto
04: Header Trigger badge Manual
05: Header shows Playbook version
06: Grey No Variables status badge (data-testid="sitrep-status-badge")
07: Mode at generation Semi-Auto (data-testid="sitrep-mode-badge")
08: Mode badge Auto
09: Section 1 heading "Situation Assessment"
10: Section 1 renders situation_assessment text
11: Section 1 has No Variables chip inline
12: Section 2 heading "Variables Snapshot"
13: Section 2 placeholder message
14: Section 3 heading "Decisions"
15: Section 3 placeholder "No Decisions proposed"
16: Section 4 heading "FRAGOs Applied"
17: Section 4 lists in-window FRAGOs with link to FRAGOS-VIEW_FRAGO-1
18: Section 4 shows multiple FRAGOs
19: Section 4 empty state
20: Deactivated FRAGO not listed
21: Section 5 heading "Notable Activity"
22: Section 5 renders contributor summary
23: Section 5 absent or placeholder when no commits
24: Open Decisions button visible (data-testid="sitrep-open-decisions-btn")
25: Open Variables button visible (data-testid="sitrep-open-variables-btn")
26: Generate for another period pre-selects Since this SitRep
27: Open Chat navigates to CHAT-FULLSCREEN-1 (stub only — chat deferred)
28: No edit/delete controls
29: Back navigation → SitRep list
30: Assessed period accessible label
31: Status badge accessible name

## Risks
- SITREP-VIEW-27 (Open Chat): assert that the link to CHAT-FULLSCREEN-1 exists in HTML; do not assert navigation works (chat not implemented this sprint).
- Tests 02, 06, 07 require `data-testid` attributes — these must match exactly.
