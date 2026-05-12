---
id: T-61-impl
role: feature-builder
depends_on: [T-67, T-61-steps]
attempt: 1
issue: "https://gitlab.com/dp2580/huginn/-/issues/61"
branch: feature/sitrep-generate-impl
---

# Task T-61-impl — SITREP-GENERATE-1 implementation

## Objective
Implement generate_sitrep_for_project task, _persist_sitrep_from_plan, and signal wiring.
Turn all 20 RED stubs in test_sitrep_generate_scenarios.py GREEN, plus pass SREP-01–04 and GEN-01–08.

## Blueprint
`factory/blueprints/T-61-impl.md`

## System context
`factory/blueprints/system.md` — "Data flow — Flow A" (full pipeline)

## Files in scope
```
gjallarhorn/tasks/sitrep_tasks.py                    (new)
gjallarhorn/services/sitrep_service.py               (modify — add _persist_sitrep_from_plan)
gjallarhorn/tasks/plan_tasks.py                      (modify — wire _persist_sitrep_from_plan)
ingestion/services/sync_engine.py                    (modify — send signal on success)
ingestion/signals.py                                 (new or modify — sync_project_completed)
tests/gjallarhorn/test_sitrep_generate_scenarios.py  (modify — implement all 20 stubs)
tests/gjallarhorn/test_persist_sitrep_from_plan.py   (new)
tests/gjallarhorn/test_generate_sitrep_task.py       (new)
tests/gjallarhorn/test_sitrep_signal.py              (new)
```

## Step-by-step
1. Check `ingestion/signals.py` — does `sync_project_completed` exist? If not, create it.
2. Read `ingestion/services/sync_engine.py` to find the correct place to call `.send()`.
3. Implement `generate_sitrep_for_project` task (idempotency guard, no-playbook guard, plan creation).
4. Implement `_persist_sitrep_from_plan` in sitrep_service.py.
5. Wire call in plan_tasks.py (replace # TODO(sitrep-generate) stub).
6. Write and pass SREP-01–04 + GEN-01–08 tests.
7. Implement all 20 scenario stubs.
8. Run full checkpoint — must pass.
9. Push branch, open MR targeting `feature/gjlr-execute-plan`.

## Acceptance criteria (checkpoint)
```
pytest tests/gjallarhorn/test_sitrep_generate_scenarios.py \
       tests/gjallarhorn/test_persist_sitrep_from_plan.py \
       tests/gjallarhorn/test_generate_sitrep_task.py \
       tests/gjallarhorn/test_sitrep_signal.py -x
```
Must pass:
**SREP-01–04:**
- `test_persist_sitrep_from_plan` — one SitRep row, correct fields
- `test_persist_sitrep_fragos_m2m` — enabled FRAGOs attached; disabled excluded
- `test_persist_sitrep_notable_activity` — notable_activity stored verbatim
- `test_persist_sitrep_bad_step_result` — missing headline → plan failed, no SitRep

**GEN-01–08:**
- `test_generate_from_dt_no_prior` — from_dt = earliest commit dt
- `test_generate_from_dt_prior_exists` — from_dt = prior_sitrep.to_dt
- `test_generate_idempotency` — second call for same to_dt → returns existing plan
- `test_generate_no_playbook` — exits without Conversation/Plan/SitRep
- `test_generate_manual_trigger` — uses caller from_dt, bypasses idempotency guard
- `test_signal_auto_trigger` — sync_project_completed → SitRep created
- `test_signal_receiver_no_propagate` — exception in receiver doesn't propagate
- `test_flow_a_full_pipeline` — seed → signal → one SitRep, 5 steps completed

**All 20 SITREP-GEN scenarios must pass.**

Full suite: `pytest tests/ -x`

## Do not do
- Do NOT add SSE/Redis calls — # TODO(chat-milestone) stubs only.
- Do NOT write VariableDatapoint rows (SITREP-GEN-14 must confirm zero rows).
- Do NOT add views or URLs (T-62, T-63 scope).
- Do NOT implement Chat (SITREP-GEN-27 scope deferred).

## Allowed tools
`git`, `python`, `pytest`, `ruff`, `manage.py`

## Result
<!-- Worker fills in after completion -->
- Branch pushed:
- MR URL:
- Checkpoint exit code:
- Scenario count green (20):
- Notes:
