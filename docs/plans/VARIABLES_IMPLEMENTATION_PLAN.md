# Variables Feature — Implementation Plan

**Feature files:** `docs/features/act-7-variables/variables-datapoints.feature` (12 scenarios),
`docs/features/act-7-variables/variables-view.feature` (46 scenarios)

**Governed by:** BPE-01 Plan Feature — FeatureFactory Playbook

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `gjallarhorn/services/sitrep_service.py` | 53–100 | Extend `build_narrative_plan_steps` to insert Variable assessment steps; extend `_persist_sitrep_from_plan` to parse `datapoints` and write VariableDatapoint rows |
| `gjallarhorn/agent/agent.py` | 60–150 | Follow `_execute_data_step` / `_execute_planning_step` pattern; add `_execute_variable_assessment_step` as a third branch in `execute_single_step` |
| `gjallarhorn/models/plan_step.py` | 1–40 | Add `is_variable_assessment = BooleanField(default=False)` — do NOT rename or reorder existing fields |
| `sitrep/models/sitrep.py` | 1–54 | Add `variables_snapshot = JSONField(default=list, blank=True)` — follow existing field ordering convention |
| `roe/models.py` | 60–79 | Add `y_axis_label = CharField(max_length=128, blank=True, default="")` to `RulesOfEngagementVariable` |
| `tests/gjallarhorn/test_sitrep_service_steps.py` | 1–40 | Follow this exact fixture-free pattern for all new service unit tests; `test_no_variable_or_decision_language` must be updated when Variable steps are added |
| `tests/factories.py` | 1–40 | Add `RulesOfEngagementVariableFactory`, `SitRepFactory`, `VariableDatapointFactory` here — follow existing `DjangoModelFactory` patterns |
| `gjallarhorn/mcp_tools/roe_tools.py` | 1–20 | Extend `get_active_roe` OR add `get_roe_variables` here — follow same return-dict pattern |

---

## Do Not Do

- Do NOT create a new Django app — Variables live in `sitrep/` (model + service) and `gjallarhorn/` (generation pipeline)
- Do NOT add a manager/repository layer — services call the ORM directly
- Do NOT rename `is_planning` on `PlanStep` — add a new `is_variable_assessment` flag alongside it
- Do NOT use `FloatField` for `VariableDatapoint.value` — the spec mandates string values ("92%", "8d", "15"); use `CharField(max_length=64, null=True, blank=True)`
- Do NOT use `'amber'` for the orange traffic-light color — the spec and all feature files use `'orange'` (SAO §17 typo)
- Do NOT FK `VariableDatapoint.roe_variable` to `PlaybookVariable` — the correct model is `RulesOfEngagementVariable` (SAO §17 uses an old name)
- Do NOT add async (no `async def`, no `asyncio`) — Celery + Django ORM, synchronous throughout
- Do NOT build a REST API — all UI surfaces via Django views returning HTML/JSON fragments (ECharts data endpoint is a JSON Django view, not DRF)
- Do NOT add `VariableDatapoint` to the `analytics/` app — it belongs in `sitrep/` per SAO §1 dependency rules
- Do NOT re-run completed PlanSteps — `get_next_pending_step()` filters by `status="pending"`; trust this contract

---

## SAO.md Sections That Apply

- **§1 Application Blocks** — `VariableDatapoint` lives in `sitrep/`; `gjallarhorn/` writes it; `ui/` reads it. Dependency direction must not be violated.
- **§1 Dependency Rules** — `gjallarhorn/` writes to `sitrep/`; `ui/` reads from all apps.
- **§17.6 Token Economy & Prompt Caching** — Variable assessment steps use the execution model (Sonnet); narrative-composition step uses the planning model (Opus). Intra-plan tool-result cache applies to data steps.
- **§17.7 SitRep Generation Flow** — extend the 5-step plan to a 4+N+1 plan (4 data-collection, N per-Variable assessment, 1 narrative-composition); `_persist_sitrep_from_plan` must be extended to parse and persist `datapoints`.
- **§3 Code Organization** — tests in `tests/unit/`, `tests/integration/`, `tests/gjallarhorn/`, `tests/ui/`; no test files in repo root.

---

## SAO Discrepancies — Resolve Before Implementing

The following SAO §17 definitions diverge from the authoritative feature spec and must be treated as SAO drafting errors. Implement per the feature spec:

| SAO field | SAO says | Correct (per feature spec) |
|-----------|----------|---------------------------|
| `VariableDatapoint.value` | `FloatField(null=True)` | `CharField(max_length=64, null=True, blank=True)` — values are strings like `"92%"`, `"8d"` |
| `VariableDatapoint.color` | `'green'|'amber'|'red'` | `'green'|'orange'|'red'|'grey'` — `'amber'` → `'orange'`; `'grey'` added for no-data |
| `VariableDatapoint.variable` | FK to `PlaybookVariable` | FK to `roe.RulesOfEngagementVariable` (old model name in SAO) |
| `VariableDatapoint` | no `y_axis_label` | Add `y_axis_label = CharField(max_length=128)` — stored from Gjallarhorn output |
| `VariableDatapoint` | no `variable_name` denormalized | Add `variable_name = CharField(max_length=255)` — frozen at generation time |
| `VariableDatapoint` | no `sitrep` FK | Add `sitrep = ForeignKey(SitRep, on_delete=CASCADE)` — primary relationship |
| `RulesOfEngagementVariable` | no `y_axis_label` | Add `y_axis_label = CharField(max_length=128, blank=True, default="")` |
| `SitRep` | no `variables_snapshot` | Add `variables_snapshot = JSONField(default=list, blank=True)` |

---

## Implementation Plan

### Branch

```
git checkout -b feature/variables-and-datapoints
```

---

### Phase 1 — Data Model

**Step 1.1 — `RulesOfEngagementVariable.y_axis_label`**

- Add `y_axis_label = models.CharField(max_length=128, blank=True, default="")` to `RulesOfEngagementVariable` in `roe/models.py`
- Generate migration: `python manage.py makemigrations roe`
- Register field in `roe/admin.py`
- Update `roe/seed_constants.py` — add `y_axis_label` to each seed variable (e.g. "merged MRs", "days", "% linked", etc.)
- Tests (`tests/unit/test_roe_variable_model.py`):
  - `test_y_axis_label_defaults_blank` — `RulesOfEngagementVariable` can be created without `y_axis_label`
  - `test_y_axis_label_stored_and_retrieved`
- Commit: `feat(roe): add y_axis_label to RulesOfEngagementVariable`

**Step 1.2 — `SitRep.variables_snapshot`**

- Add `variables_snapshot = models.JSONField(default=list, blank=True)` to `SitRep` in `sitrep/models/sitrep.py`
- Generate migration: `python manage.py makemigrations sitrep`
- Tests (`tests/unit/test_sitrep_model.py`):
  - `test_variables_snapshot_defaults_to_empty_list`
  - `test_variables_snapshot_accepts_datapoints_list`
- Commit: `feat(sitrep): add variables_snapshot JSONField to SitRep`

**Step 1.3 — `VariableDatapoint` model**

- Create `sitrep/models/variable_datapoint.py`:

```python
class VariableDatapoint(models.Model):
    sitrep           = ForeignKey('sitrep.SitRep', on_delete=CASCADE, related_name='datapoints')
    roe_variable     = ForeignKey('roe.RulesOfEngagementVariable', null=True, blank=True,
                                  on_delete=SET_NULL, related_name='datapoints')
    variable_name    = CharField(max_length=255)      # denormalized — frozen at generation time
    y_axis_label     = CharField(max_length=128, blank=True, default='')
    value            = CharField(max_length=64, null=True, blank=True)   # "92%", "8d", None
    color            = CharField(max_length=16)       # 'green'|'orange'|'red'|'grey'
    from_dt          = DateTimeField()
    to_dt            = DateTimeField()
    source_plan_step = ForeignKey('gjallarhorn.PlanStep', null=True, blank=True, on_delete=SET_NULL)
    created_at       = DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [UniqueConstraint(fields=['sitrep', 'roe_variable'],
                                        name='uq_vdp_sitrep_roe_variable')]
        ordering = ['sitrep', 'roe_variable__sort_order']
```

- Export from `sitrep/models/__init__.py`
- Generate migration: `python manage.py makemigrations sitrep`
- Register in `sitrep/admin.py`
- Add `VariableDatapointFactory` to `tests/factories.py`
- Tests (`tests/unit/test_variable_datapoint_model.py`):
  - `test_create_minimal` — fields `sitrep`, `variable_name`, `color`, `from_dt`, `to_dt` sufficient
  - `test_color_choices` — only green/orange/red/grey accepted (validator or constraint)
  - `test_value_nullable` — `value=None` is valid (grey color)
  - `test_unique_sitrep_roe_variable` — duplicate `(sitrep, roe_variable)` raises IntegrityError
  - `test_ordering_by_sort_order`
- Commit: `feat(sitrep): add VariableDatapoint model`

**Step 1.4 — `PlanStep.is_variable_assessment`**

- Add `is_variable_assessment = models.BooleanField(default=False)` to `PlanStep` in `gjallarhorn/models/plan_step.py`
- Generate migration: `python manage.py makemigrations gjallarhorn`
- Tests (`tests/unit/test_plan_step_model.py`):
  - `test_is_variable_assessment_defaults_false`
  - `test_step_type_exclusivity` — a step should not have both `is_planning=True` and `is_variable_assessment=True`
- Commit: `feat(gjallarhorn): add is_variable_assessment flag to PlanStep`

---

### Phase 2 — MCP Tool: `get_roe_variables`

**Step 2.1 — Extend `gjallarhorn/mcp_tools/roe_tools.py`**

- Add `get_roe_variables(project_id: int) -> list[dict] | None`:
  - Returns list of `{name, abbrev, y_axis_label, calculating, interpreting}` for the active RoE version, in `sort_order`
  - Returns `None` if no RoE assigned or no variables defined
- Register tool in `ToolExecutor`
- Tests (`tests/gjallarhorn/test_roe_tools.py`):
  - `test_returns_variables_in_sort_order`
  - `test_returns_none_when_no_roe`
  - `test_returns_none_when_no_variables`
  - `test_each_variable_dict_has_required_keys`
- Commit: `feat(gjallarhorn): add get_roe_variables MCP tool`

---

### Phase 3 — Generation Pipeline

**Step 3.1 — `build_variable_assessment_steps` helper**

- Add to `gjallarhorn/services/sitrep_service.py`:

```python
def build_variable_assessment_steps(roe_variables: list) -> list[dict]:
    """One assessment step per RulesOfEngagementVariable, using execution model.

    Each step instructs the LLM to apply the variable's calculating + interpreting
    rules to the collected data and return {"value": "<str>", "color": "<green|orange|red|grey>"}.
    """
```

- Each step: `is_planning=False`, `is_variable_assessment=True`, `tool=""`, action = `"Assess {name} ({abbrev})"`, `expected_outcome = '{"value": "...", "color": "green|orange|red|grey"}'`
- Tests (`tests/gjallarhorn/test_sitrep_service_steps.py`):
  - `test_build_variable_steps_one_per_variable`
  - `test_variable_step_has_is_variable_assessment_true`
  - `test_variable_step_is_planning_false`
  - `test_variable_step_action_contains_name_and_abbrev`
  - `test_empty_variables_returns_empty_list`

**Step 3.2 — Extend `build_narrative_plan_steps`**

- Fetch `roe_variables` via `get_roe_variables(project_id)` (or pass them in)
- Insert Variable assessment steps between step 4 and the final narrative step
- Total steps: 4 + N + 1 (N = variable count; 0 when no RoE or no variables)
- Update `expected_outcome` of narrative step to include `datapoints` array
- **Update** `test_no_variable_or_decision_language` — this test WILL fail; rename it `test_narrative_only_mode_has_no_variable_steps` and add a `@pytest.mark.skip` or pass `roe_variables=[]` explicitly to preserve the narrative-only codepath
- Tests:
  - `test_with_two_variables_returns_seven_steps` (4 + 2 + 1)
  - `test_with_no_variables_still_returns_five_steps`
  - `test_variable_steps_are_between_data_and_narrative`
- Commit: `feat(gjallarhorn): build variable assessment steps in SitRep plan`

**Step 3.3 — `GjallarhornAgent._execute_variable_assessment_step`**

- In `gjallarhorn/agent/agent.py`, add third branch in `execute_single_step`:
  ```python
  elif step.is_variable_assessment:
      self._execute_variable_assessment_step(plan, step)
  ```
- `_execute_variable_assessment_step(plan, step)`:
  - Gather collected data from prior steps (same `_format_collected_data(plan)`)
  - Add variable-specific context: name, abbrev, calculating rule, interpreting rule
  - Single LLM call using **execution model** (Sonnet) — NOT `_planning_model()`
  - Parse response JSON: `{"value": "...", "color": "..."}`
  - Store in `step.result`; set `step.model_used`
  - On parse error: set `value=None`, `color='grey'` — do not fail the plan
- Tests (`tests/gjallarhorn/test_variable_assessment_step.py`):
  - `test_variable_step_calls_execution_model`
  - `test_variable_step_result_has_value_and_color`
  - `test_malformed_llm_response_defaults_to_grey`
  - `test_variable_step_does_not_use_planning_model`

**Step 3.4 — Extend `_persist_sitrep_from_plan`**

- After `SitRep.objects.create(...)`, call `_persist_variable_datapoints(sitrep, plan)`
- Add `_persist_variable_datapoints(sitrep, plan)`:
  - Collect all `is_variable_assessment=True` steps from plan
  - For each: extract `{variable_name, value, color}` from `step.result`
  - Resolve `roe_variable` FK from `variable_name` (match against active RoE version)
  - Set `y_axis_label` from the resolved `RulesOfEngagementVariable.y_axis_label`
  - `VariableDatapoint.objects.get_or_create(sitrep=sitrep, roe_variable=v, defaults={...})`
  - Build `datapoints` list: `[{variable_name, abbrev, y_axis_label, value, color}, ...]`
  - Write `sitrep.variables_snapshot = datapoints` + `sitrep.save(update_fields=['variables_snapshot'])`
- Tests (`tests/gjallarhorn/test_sitrep_service_persist.py`):
  - `test_persist_creates_one_datapoint_per_variable`
  - `test_persist_sets_variables_snapshot_on_sitrep`
  - `test_persist_idempotent_on_duplicate_plan_run`
  - `test_persist_grey_when_value_null`
  - `test_persist_links_source_plan_step`
  - `test_persist_no_datapoints_when_no_variable_steps`
- Commit: `feat(gjallarhorn): persist VariableDatapoints and variables_snapshot after SitRep generation`

---

### Phase 4 — Service Layer

**Step 4.1 — `VariableDatapointService`**

- Create `sitrep/services/variable_datapoint_service.py`:
  - `get_latest_per_variable(project) -> dict[str, VariableDatapoint]` — keyed by `variable_name`; used by informer bar
  - `get_for_period(project, roe_version, from_dt, to_dt) -> QuerySet` — used by Variables tab charts
  - `get_snapshot(sitrep) -> list[dict]` — returns `sitrep.variables_snapshot`; falls back to DB query for legacy SitReps where snapshot is empty
- Tests (`tests/unit/test_variable_datapoint_service.py`):
  - `test_get_latest_per_variable_returns_most_recent`
  - `test_get_latest_per_variable_empty_when_no_datapoints`
  - `test_get_for_period_filters_by_date_range`
  - `test_get_snapshot_returns_json_field_content`
  - `test_get_snapshot_falls_back_to_db_for_legacy_sitrep`
- Commit: `feat(sitrep): add VariableDatapointService`

---

### Phase 5 — UI Backend

**Step 5.1 — ECharts data endpoint**

- Add to `ui/views/sitrep.py` (or new `ui/views/variables.py`):
  - `GET /projects/<pk>/variables/chart-data/?abbrev=<Tp>&period=<today|this_week|...>&from_dt=&to_dt=`
  - Returns JSON: `{variable_name, abbrev, y_axis_label, datapoints: [{ts, value, color}, ...]}`
  - Reads via `VariableDatapointService.get_for_period`
- Add URL pattern in `ui/urls.py`
- Tests (`tests/ui/test_variables_chart_data.py`):
  - `test_chart_data_returns_200_with_datapoints`
  - `test_chart_data_empty_list_when_no_datapoints`
  - `test_chart_data_404_for_unknown_project`
  - `test_chart_data_requires_abbrev_param`

**Step 5.2 — Variables tab view**

- Add `variables_view(request, pk)` to `ui/views/`:
  - Loads active RoE variables
  - Loads `VariableDatapointService.get_latest_per_variable(project)` for current values
  - Passes `period` (from query param, default `today`)
  - Returns `VARIABLES-VIEW-1` template
- Tests (`tests/ui/test_variables_view.py`):
  - `test_variables_tab_renders_for_project_with_roe`
  - `test_variables_tab_empty_state_no_roe`
  - `test_variables_tab_empty_state_no_variables`
  - `test_variables_tab_redirects_anonymous`
  - `test_period_param_passed_to_context`

**Step 5.3 — Project view: Variables tab + informer bar data**

- Update `ui/views/projects_view.py`:
  - Pass `informer_bar_data` (list of `{abbrev, color, value, y_axis_label}`) to context from `VariableDatapointService.get_latest_per_variable`
  - Add `?tab=variables` branch — renders Variables tab content inline (not redirect)
- Tests (`tests/ui/test_projects_view.py`):
  - `test_vitals_tab_contains_informer_bar`
  - `test_informer_bar_empty_when_no_roe`
  - `test_informer_bar_shows_grey_when_no_datapoints`

**Step 5.4 — SitRep list/view: Variables data**

- `SitRepListView` — pass `variables_snapshot` (from `SitRep.variables_snapshot`) with each row
- `SitRepDetailView` — pass `variables_snapshot` and `agg_color` (derived from snapshot)
- `agg_color` helper: `max(colors by red > orange > green > grey)` — can live in `sitrep/models/sitrep.py` as a `@property`
- Tests (`tests/ui/test_sitrep_list_scenarios.py`):
  - Add `test_variables_column_shows_dot_informers`
  - Add `test_variables_column_dash_when_no_snapshot`
- Tests (`tests/ui/test_sitrep_view_scenarios.py`):
  - Add `test_variables_snapshot_section_shows_rows`
  - Add `test_status_badge_reflects_agg_color`
- Commit: `feat(ui): add Variables column to SitRep list and Variables Snapshot to SitRep view`

---

### Phase 6 — UI Frontend (Templates)

**Step 6.1 — `ui/templates/ui/variables/view.html`** (production template, not mockup)

- Extend `base.html`
- `data-testid="variables-view-loaded"`, screen anchor `VARIABLES-VIEW-1`
- Period selector (dropdown, links reload page with `?period=` param)
- Variable cards: each with header (abbrev + name + value + color band), ECharts chart div (`data-chart-variable="{{ v.abbrev }}"` + `data-chart-period="{{ period }}"`), collapsible Calculating, visible Interpreting, "Create FRAGO" + "View in Chat" links
- Empty states: no RoE, no variables, no datapoints per card
- Drill-down off-canvas panel (opened by HTMX `GET /projects/<pk>/variables/<abbrev>/drilldown/`)

**Step 6.2 — Update `ui/templates/ui/projects/view.html`**

- Variables tab pill in nav
- When `active_tab == 'variables'`: include Variables tab content
- Vitals tab: informer bar using `informer_bar_data` context (template loop over real data — not hardcoded)

**Step 6.3 — Update SitRep list + view templates**

- `sitrep/list.html`: Variables column with dot-informer loop (`{% for v in r.variables_snapshot %}`)
- `sitrep/view.html`: status badge + Variables Snapshot table driven by real `variables_snapshot` context

**Step 6.4 — ECharts JavaScript**

- In Variables tab template: `<script>` block that reads all `[data-chart-variable]` divs and initialises one ECharts instance per card, fetching data from `/projects/<pk>/variables/chart-data/?abbrev=<Tp>&period=<period>`
- Commit: `feat(ui): implement Variables tab, informer bar, and SitRep Variables column templates`

---

### Phase 7 — Integration Tests

- `tests/integration/test_variables_pipeline_e2e.py`:
  - `test_full_pipeline_with_two_variables` — fixture with Project + RoE (2 Variables) + mock LLM returning `datapoints`; run `_persist_sitrep_from_plan`; assert 2 `VariableDatapoint` rows created; assert `SitRep.variables_snapshot` populated; assert ECharts endpoint returns correct data
  - `test_pipeline_idempotent` — running persist twice does not double rows
  - `test_pipeline_grey_when_variable_uncomputed` — one Variable returns null value; assert `color='grey'`, `value=None`
  - `test_legacy_sitrep_no_snapshot_falls_back_to_db`
- Commit: `test(variables): add end-to-end pipeline integration tests`

---

### Phase 8 — Definition of Done check & finalize

- Run full test suite: `pytest tests/ -x` — must pass with no regressions
- Run linter: `make lint` (or `ruff check .`)
- All 58 scenarios in `variables-datapoints.feature` + `variables-view.feature` must be covered by at least one test
- Commit: `chore: DoD check — Variables feature complete`
- Open MR targeting `main`; description links feature files and this plan

---

## Checkpoint Commands

```bash
# Phase 1 — models
pytest tests/unit/test_roe_variable_model.py tests/unit/test_sitrep_model.py tests/unit/test_variable_datapoint_model.py tests/unit/test_plan_step_model.py -x

# Phase 2 — MCP tool
pytest tests/gjallarhorn/test_roe_tools.py -x

# Phase 3 — generation pipeline
pytest tests/gjallarhorn/test_sitrep_service_steps.py tests/gjallarhorn/test_variable_assessment_step.py tests/gjallarhorn/test_sitrep_service_persist.py -x

# Phase 4 — service
pytest tests/unit/test_variable_datapoint_service.py -x

# Phase 5 — UI backend
pytest tests/ui/test_variables_view.py tests/ui/test_variables_chart_data.py tests/ui/test_projects_view.py tests/ui/test_sitrep_list_scenarios.py tests/ui/test_sitrep_view_scenarios.py -x

# Phase 7 — integration
pytest tests/integration/test_variables_pipeline_e2e.py -x

# Full suite
pytest tests/ -x
```
