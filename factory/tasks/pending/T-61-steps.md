---
id: T-61-steps
role: step-def-writer
depends_on: []
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/61"
branch: feature/sitrep-generate-steps
---

# Task T-61-steps — SITREP-GENERATE-1 step definitions (RED stubs)

## Objective
Write one pytest test stub per scenario in sitrep-generate.feature (20 scenarios).
Each stub calls pytest.fail("RED") so the file is importable but all tests fail.
No production code. This establishes the baseline that T-61-impl turns GREEN.

## Blueprint
`factory/blueprints/T-61-steps.md`

## Feature file to translate
`docs/features/act-5-sitrep/sitrep-generate.feature`

## Files in scope
```
tests/gjallarhorn/test_sitrep_generate_scenarios.py   (new — 20 stubs)
```
No other files. If you feel you need to touch production code, stop — that is T-61-impl.

## Step-by-step
1. Read `docs/features/act-5-sitrep/sitrep-generate.feature` in full.
2. For each of the 20 Scenario blocks, write one pytest function:
   - Name: `test_sitrep_gen_NN_<snake_case_title>` matching the Scenario ID.
   - Body: a docstring quoting the scenario's Given/When/Then, then `pytest.fail("RED — not implemented")`.
3. Confirm `pytest tests/gjallarhorn/test_sitrep_generate_scenarios.py` exits non-zero (all fail).
4. Push branch, open MR targeting `features/gjallarhorn`.

## Acceptance criteria
```
pytest tests/gjallarhorn/test_sitrep_generate_scenarios.py --co -q
```
Must list exactly 20 test names. All 20 must FAIL (not error, not skip — FAIL).

```
pytest tests/ -x --ignore=tests/gjallarhorn/test_sitrep_generate_scenarios.py
```
Must pass (no regressions in existing tests).

## Do not do
- Do NOT implement any production code.
- Do NOT write fixtures or conftest entries.
- Do NOT write assert statements that could accidentally pass.
- Do NOT merge scenarios together — one function per scenario, exactly.

## Allowed tools
`git`, `python`, `pytest`

## Result
<!-- Worker fills in after completion -->
- Branch pushed:
- MR URL:
- Test count confirmed (20):
- Notes:
