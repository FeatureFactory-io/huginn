## Orient Summary — 2026-05-26

### Target
Act: act-7-variables
Feature files:
- `docs/features/act-7-variables/variables-datapoints.feature` (12 scenarios)
- `docs/features/act-7-variables/variables-view.feature` (46 scenarios)

### Iteration Goal
Implement Variables & Datapoints: RoE variables → Gjallarhorn computation → VariableDatapoint
storage → informer bar / Variables tab / SitRep columns UI.

### Scenarios in Scope (grouped into 6 implementation slices)

The 58 BDD scenarios map to 6 implementation slices (S1–S6) — one GitLab issue each:

| Slice | Title | BDD coverage |
|-------|-------|-------------|
| S1 | Data Model | DP-04, 05, 06, 07, 08, 11, 12 |
| S2 | Gjallarhorn Pipeline | DP-01, 02, 03, 04, 05, 06, 07, 08, 09, 11 |
| S3 | Service Layer | VIEW-01..10 (data retrieval) |
| S4 | UI Backend | VIEW-01..46 (backend views + endpoints) |
| S5 | UI Templates | VIEW-01..46 (HTML + ECharts JS) |
| S6 | Integration Tests | All 58 scenarios (DP + VIEW) |

All 58 scenarios are in scope — no deferrals.

### Scenarios Deferred
None.

### Velocity Trend
Stable → improving (previous iteration W19: velocity_ratio 11/11 = 1.0, footprint_accuracy 0.92).

### Dominant Drift
F01 YAML checkpoint wording (from W19 — minor; no structural risk).

### Scope Validation
- 58 BDD scenarios grouped into 6 slices — manageable with clear dependency ordering.
- No scope risk flags: velocity was perfect in W19; dominant drift was cosmetic.
- scope_override: not_needed (scope is clear and maps directly to the implementation plan).

### Dependency Order
```
S1 → S2 (parallel with S3) → S4 (parallel with S5) → S6
```

### Risk Flags
- `test_no_variable_or_decision_language` in `tests/gjallarhorn/test_sitrep_service_steps.py`
  will break when S2 inserts Variable steps into the pipeline. Must be updated as part of S2.
- ECharts JS: no existing pattern in codebase — introduce in S5, document in issue.
