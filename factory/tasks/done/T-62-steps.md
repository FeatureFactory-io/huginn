---
id: T-62-steps
role: step-def-writer
depends_on: []
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/62"
branch: feature/sitrep-list-steps
---

# Task T-62-steps — SITREP-LIST+FIND-1 step definitions (RED stubs)

## Objective
Write one pytest test stub per scenario in sitrep-list-find.feature (22 scenarios).
Each stub calls pytest.fail("RED"). No production code.

## Blueprint
`factory/blueprints/T-62-steps.md`

## Feature file to translate
`docs/features/act-5-sitrep/sitrep-list-find.feature`

## Files in scope
```
tests/ui/__init__.py                             (new if absent)
tests/ui/test_sitrep_list_scenarios.py           (new — 22 stubs)
```

## Step-by-step
1. Read `docs/features/act-5-sitrep/sitrep-list-find.feature` in full.
2. Write 22 stub functions (see blueprint for naming convention).
3. Confirm `pytest tests/ui/test_sitrep_list_scenarios.py` exits non-zero (all fail).
4. Push branch, open MR targeting `features/gjallarhorn`.

## Acceptance criteria
```
pytest tests/ui/test_sitrep_list_scenarios.py --co -q
```
Must list exactly 22 test names. All 22 must FAIL (not error — FAIL).

```
pytest tests/ -x --ignore=tests/ui/test_sitrep_list_scenarios.py
```
Must pass.

## Do not do
- Do NOT write production code.
- Do NOT write passing assertions.
- One function per scenario — no merging.

## Allowed tools
`git`, `python`, `pytest`

## Result
- Branch pushed: feature/sitrep-list-steps
- MR URL: https://gitlab.com/dp2580/huginn/-/merge_requests/10
- Checkpoint exit code: 0 (19 tests collected, all FAIL)
- Notes: Establishes RED baseline for T-62-impl
