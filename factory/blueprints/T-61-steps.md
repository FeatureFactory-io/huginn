# Blueprint T-61-steps — SITREP-GENERATE-1 step definitions

## Design
Translate all 20 scenarios in `sitrep-generate.feature` into pytest test function
stubs. Each stub asserts `False` (or uses `pytest.fail`) to establish a clean RED
baseline. The feature-builder (T-61-impl) then implements until they pass GREEN.

No production code is written in this task. The output is a single test file
`tests/gjallarhorn/test_sitrep_generate_scenarios.py` with one function per scenario.

## Files touched
- `tests/gjallarhorn/test_sitrep_generate_scenarios.py` — new, all 20 stubs

## Naming convention
Function names mirror scenario IDs:
```
def test_sitrep_gen_01_sync_complete_fires_task(): pytest.fail("RED")
def test_sitrep_gen_02_subsequent_sync_from_dt(): pytest.fail("RED")
...
def test_sitrep_gen_20_idempotency_no_duplicate(): pytest.fail("RED")
```

## What each stub covers (from sitrep-generate.feature)
- GEN-01/SITREP-GEN-01: sync complete → task enqueued
- GEN-02/SITREP-GEN-02: from_dt = prior SitRep.to_dt
- SITREP-GEN-03: manual trigger → 202 + toast
- SITREP-GEN-04: since-last-sitrep period resolves correctly
- SITREP-GEN-05: since-last-sitrep disabled when no prior
- SITREP-GEN-06: manual custom period
- SITREP-GEN-07: context includes Playbook + enabled FRAGOs, excludes disabled
- SITREP-GEN-08: context includes SA
- SITREP-GEN-09: context includes commits in window
- SITREP-GEN-10: FRAGOs outside window excluded
- SITREP-GEN-11: Conversation + ExecutionPlan created before stepping
- SITREP-GEN-12: plan includes commit-fetch + narrative-compose steps
- SITREP-GEN-13: completed plan writes SitRep with required fields
- SITREP-GEN-14: no VariableDatapoint rows written
- SITREP-GEN-15: mode_at_generation reflects project mode
- SITREP-GEN-16: plan_completed SSE stub fires (assert TODO comment present)
- SITREP-GEN-17: 429 pauses step + retries
- SITREP-GEN-18: completed steps not re-executed on retry
- SITREP-GEN-19: permanent failure marks plan failed
- SITREP-GEN-20: duplicate request → no duplicate SitRep

## Risks
- SITREP-GEN-16 (SSE): test must only assert the TODO comment exists in source, not that SSE fires — SSE is out of scope for this sprint.
- SITREP-GEN-03 (toast): test is a Django test client integration test, not Selenium.
