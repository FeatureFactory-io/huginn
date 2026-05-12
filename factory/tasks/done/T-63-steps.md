---
id: T-63-steps
role: step-def-writer
depends_on: []
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/63"
branch: feature/sitrep-view-steps
---

# Task T-63-steps — SITREP-VIEW_SITREP-1 step definitions (RED stubs)

## Objective
Write one pytest test stub per scenario in sitrep-view.feature (31 scenarios).
Each stub calls pytest.fail("RED"). No production code.

## Blueprint
`factory/blueprints/T-63-steps.md`

## Feature file to translate
`docs/features/act-5-sitrep/sitrep-view.feature`

## Files in scope
```
tests/ui/__init__.py                             (new if absent)
tests/ui/test_sitrep_view_scenarios.py           (new — 31 stubs)
```

## Step-by-step
1. Read `docs/features/act-5-sitrep/sitrep-view.feature` in full.
2. Write 31 stub functions (see blueprint for naming convention).
3. Confirm `pytest tests/ui/test_sitrep_view_scenarios.py` exits non-zero.
4. Push branch, open MR targeting `features/gjallarhorn`.

## Acceptance criteria
```
pytest tests/ui/test_sitrep_view_scenarios.py --co -q
```
Must list exactly 31 test names. All 31 must FAIL.

```
pytest tests/ -x --ignore=tests/ui/test_sitrep_view_scenarios.py
```
Must pass.

## Do not do
- Do NOT write production code.
- Do NOT write passing assertions.
- One function per scenario — no merging.

## Allowed tools
`git`, `python`, `pytest`

## Result
- Branch pushed: feature/sitrep-view-steps
- MR URL: https://gitlab.com/dp2580/huginn/-/merge_requests/11
- Checkpoint exit code: 0 (31 tests collected, all FAIL)
- Notes: Establishes RED baseline for T-63-impl
