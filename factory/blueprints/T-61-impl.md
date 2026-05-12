# Blueprint T-61-impl — SITREP-GENERATE-1 implementation

## Design
Implement `gjallarhorn/tasks/sitrep_tasks.py` (`generate_sitrep_for_project`)
and `_persist_sitrep_from_plan` helper in `sitrep_service.py`. Wire the
`sync_project_completed` Django signal receiver. Turn all 20 RED stubs GREEN.

`generate_sitrep_for_project(project_id, from_dt, to_dt, trigger)`:
1. Idempotency guard: `SitRep.objects.filter(project=project, to_dt=to_dt).exists()` → return existing plan_id (automatic trigger only; manual skips guard).
2. No Playbook → `logger.warning(...)` + return.
3. `Conversation.objects.create(type='sitrep_generation', ...)`
4. `steps = build_narrative_plan_steps(project_id, from_dt, to_dt)`
5. `agent.create_plan(conversation, goal, steps)` → enqueues execute_plan.
6. Fill in `# TODO(sitrep-generate): _persist_sitrep_from_plan(plan)` stub in T-67's execute_plan.

`_persist_sitrep_from_plan(plan)`: parses final step result JSON
(`headline`, `situation_assessment`, `notable_activity`), creates `SitRep`, attaches FRAGOs.

Signal: `sync_project_completed.send(...)` fires in `ingestion/services/sync_engine.py`
after successful sync. Receiver in `gjallarhorn/tasks/sitrep_tasks.py` calls
`generate_sitrep_for_project.delay(...)`. Receiver exceptions must NOT propagate.

## Files touched
- `gjallarhorn/tasks/sitrep_tasks.py` — new: generate_sitrep_for_project + signal receiver
- `gjallarhorn/services/sitrep_service.py` — add _persist_sitrep_from_plan
- `gjallarhorn/tasks/plan_tasks.py` — remove # TODO stub; call _persist_sitrep_from_plan
- `ingestion/services/sync_engine.py` — add signal send on sync success
- `ingestion/signals.py` — define sync_project_completed signal (if not exists)
- `tests/gjallarhorn/test_sitrep_generate_scenarios.py` — implement all 20 stubs GREEN
- `tests/gjallarhorn/test_persist_sitrep_from_plan.py` — SREP-01–04
- `tests/gjallarhorn/test_generate_sitrep_task.py` — GEN-01–05
- `tests/gjallarhorn/test_sitrep_signal.py` — GEN-06–08

## Interfaces
```python
@shared_task(name='gjallarhorn.generate_sitrep_for_project')
def generate_sitrep_for_project(project_id, from_dt, to_dt, trigger='automatic'): ...

def _persist_sitrep_from_plan(plan: ExecutionPlan) -> SitRep: ...
```

## Risks
- Check whether `sync_project_completed` signal already exists in `ingestion/` before creating it.
- Signal receiver must catch ALL exceptions and log them — never re-raise.
- from_dt resolution for GEN-01: `ingestion.Increment.objects.filter(project=...).order_by('committed_at').values_list('committed_at', flat=True).first()`.
- Manual trigger bypasses idempotency guard per GEN-05 spec.
