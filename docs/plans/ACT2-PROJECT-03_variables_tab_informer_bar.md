# ACT2-PROJECT-03: Project detail — add Variables tab and informer bar to Vitals

## Scope
Add a **Variables tab** to the Project detail page that shows time-series diagrams for all PlaybookVariables over a fixed set of period filters. Add an **informer bar** to the Vitals tab that renders one colored dot per PlaybookVariable, sourced from the latest SitRep's `variables_snapshot`.

## @reimplement scenarios implemented by this issue

- `PROJECTS-VIEW_VITALS-01` — Vitals tab visible alongside Variables and Increments tabs
- `PROJECTS-VIEW_VITALS-06` — Identity, Playbook, and Sync sections remain on Vitals; Variable diagrams are only on Variables tab
- `PROJECTS-VIEW_VITALS-08` — Informer bar renders one dot per PlaybookVariable in declared order
- `PROJECTS-VIEW_VITALS-09` — Informer bar dot hover shows name, abbrev, and value
- `PROJECTS-VIEW_VITALS-10` — Informer bar is present but empty when no Playbook assigned
- `PROJECTS-VIEW_VITALS-11` — Dot color reflects interpreting rule computed at last SitRep time

---

## Prerequisites

- ACT3-PLAYBOOK-05 must be merged (PlaybookVariable model has no `dimensions` field).
- Informer bar values come from the latest SitRep `variables_snapshot` JSON. If SitRep AI generation is not yet implemented, the informer bar should render using placeholder data from the Playbook's Variable definitions (name + abbrev) with neutral/grey dots.

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ui/templates/ui/projects/detail.html` | 40–63 | Project tab nav — add "Variables" tab item between Vitals and Increments |
| `ui/templates/ui/projects/detail.html` | 65–138 | Tab pane content — add informer bar component inside the Vitals pane; add Variables pane with period filter + diagram grid |
| `ui/views/projects.py` | 184–214 | `ProjectDetailView.get` — add "variables" to valid tab set; pass `informer_bar_items` and `variables_period` context vars |
| `ui/views/projects.py` | 194–200 | Tab validation: currently `{"vitals", "increments"}` — extend to `{"vitals", "increments", "variables"}` |
| `playbooks/models.py` | 60–81 | `PlaybookVariable` — `abbrev`, `interpreting` drive informer bar; `name` for tooltip |

---

## Do Not Do

- Do NOT create a new Django app
- Do NOT add async
- Do NOT add a REST API endpoint
- Do NOT implement the full SitRep AI generation pipeline in this issue — informer bar should degrade gracefully (grey dots) if no SitRep exists
- Do NOT implement actual ECharts diagram data in this issue if VariableDatapoint rows do not yet exist — render the diagram skeleton/empty state

---

## SAO.md Sections That Apply

- §1 Application Blocks: `ui/` reads from all apps; no business logic in templates; ECharts data served as JSON from Django views
- §2 Integration & API Design: Web UI only; all interactions are HTMX swaps or GET tab navigation
- §4 Data Architecture: Django ORM; `PlaybookVersion.variables.all()` for informer bar definition; `VariableDatapoint` rows (if model exists) or placeholder for diagrams
- §5 Test Strategy: pytest + Django test client; ECharts JSON endpoints tested by asserting JSON structure

---

## Implementation Plan

### Step 1 — Add Variables tab to project tab nav (`detail.html` lines 40–63)

Add a new `<li>` after the Vitals tab and before the Increments tab:

```html
<li class="nav-item" role="presentation">
  <a
    class="nav-link {% if active_tab == 'variables' %}active{% endif %}"
    href="{% url 'projects-detail' project.pk %}?tab=variables"
    role="tab"
    aria-selected="{% if active_tab == 'variables' %}true{% else %}false{% endif %}"
    id="project-tab-variables"
    data-testid="project-tab-variables"
  ><i class="fa-solid fa-chart-line me-1" aria-hidden="true"></i>Variables</a>
</li>
```

### Step 2 — Add informer bar inside the Vitals pane (`detail.html`)

Inside the Vitals tab pane, after the metric-card grid and before the closing `</div>`, add:

```html
<div class="mt-3" data-testid="project-informer-bar">
  {% if informer_bar_items %}
    <div class="d-flex flex-wrap gap-2 align-items-center">
      {% for dot in informer_bar_items %}
        <span
          class="hg-informer-dot hg-informer-dot--{{ dot.color }}"
          title="{{ dot.name }} ({{ dot.abbrev }}): {{ dot.value|default:'—' }}"
          data-testid="informer-dot-{{ dot.abbrev }}"
          tabindex="0"
          aria-label="{{ dot.name }}: {{ dot.value|default:'no data' }}"
        >{{ dot.abbrev }}</span>
      {% endfor %}
    </div>
  {% else %}
    <p class="text-muted small mb-0" data-testid="informer-bar-empty">No Playbook assigned</p>
  {% endif %}
</div>
```

Add CSS for `.hg-informer-dot` in `static/css/huginn.css`:
- Base: small pill, monospace font, fixed width, border-radius.
- `--green`: Bootstrap success green background.
- `--orange`: Bootstrap warning orange background.
- `--red`: Bootstrap danger red background.
- `--grey` (default/no-data): muted grey background.

### Step 3 — Add Variables tab pane (`detail.html`)

In the tab pane `{% if active_tab == 'vitals' %}...{% elif ... %}` block, add a third branch for `variables`:

```html
{% elif active_tab == 'variables' %}
<div id="project-pane-variables" role="tabpanel" aria-labelledby="project-tab-variables" tabindex="0">
  <div class="mb-3 d-flex flex-wrap gap-2 hg-variables-period-outer" role="group" aria-label="Variables period">
    <div class="btn-group btn-group-sm hg-variables-period flex-wrap" role="group">
      {% for key, label in variables_period_choices %}
      <a
        href="{% url 'projects-detail' project.pk %}?tab=variables&period={{ key }}"
        class="btn {% if variables_period == key %}btn-primary{% else %}btn-outline-secondary{% endif %}"
        data-testid="variables-period-{{ key }}"
        aria-label="Show Variables for {{ label }}"
      >{{ label }}</a>
      {% endfor %}
    </div>
  </div>
  {% if playbook_variables %}
    <div class="row row-cols-1 row-cols-md-2 row-cols-xl-3 g-3" data-testid="variables-diagram-grid">
      {% for var in playbook_variables %}
      <div class="col">
        <div class="card border-0 shadow-sm rounded-3" data-testid="variables-diagram-{{ var.abbrev }}">
          <div class="card-header bg-white py-2">
            <span class="fw-semibold small">{{ var.name }}</span>
            <code class="small text-muted ms-2">{{ var.abbrev }}</code>
          </div>
          <div class="card-body p-2">
            <div class="hg-variables-chart-placeholder text-muted small text-center py-4"
                 data-chart-var="{{ var.abbrev }}"
                 data-chart-period="{{ variables_period }}">
              No datapoints yet for this period.
            </div>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
  {% else %}
    <p class="text-muted mb-0" data-testid="variables-empty-state">No Variables defined on the assigned Playbook.</p>
  {% endif %}
</div>
```

### Step 4 — Update `ProjectDetailView.get` in `ui/views/projects.py`

1. Extend valid tab set: `{"vitals", "increments", "variables"}` (line 195).
2. Add period picker constants (mirroring Increments range pattern):

```python
VARIABLES_PERIOD_LABELS = {
    "today": "Today",
    "yesterday": "Yesterday",
    "this_week": "This week",
    "last_week": "Last week",
    "last_30d": "30 days",
}
VARIABLES_PERIOD_ORDER = ["today", "yesterday", "this_week", "last_week", "last_30d"]
```

3. Resolve `variables_period` from query string (default: `"this_week"`).
4. Build `informer_bar_items`:
   - Get the assigned Playbook's latest version variables.
   - For each variable, look up the latest SitRep `variables_snapshot` (if model exists) to get `color` and `value`.
   - If no SitRep exists, use `color="grey"` and `value=None`.
   - Return as list of dicts: `{"name", "abbrev", "color", "value"}`.
5. Build `playbook_variables`:
   - Return ordered list of `{"name", "abbrev"}` dicts from `PlaybookVersion.variables`.
6. Pass `informer_bar_items`, `playbook_variables`, `variables_period`, `variables_period_choices` to template context.
7. For `ProjectsSyncNowView.post`, add `"variables"` to valid tab redirect set (line 233).

### Step 5 — Add `_get_informer_bar_items` helper

In `ui/views/projects.py` or `ui/services/` (if logic is > 20 lines):

```python
def _get_informer_bar_items(project) -> list[dict]:
    """Return informer bar dots from the assigned Playbook + latest SitRep."""
    playbook = project.assigned_playbook
    if not playbook:
        return []
    ver = playbook.versions.order_by("-version_number").first()
    if not ver:
        return []
    vars_ = list(ver.variables.order_by("sort_order").values("name", "abbrev"))
    # If SitRep model exists, look up latest snapshot values here.
    # For now, render grey dots (no SitRep data yet).
    return [{"name": v["name"], "abbrev": v["abbrev"], "color": "grey", "value": None} for v in vars_]
```

### Step 6 — Add CSS for `.hg-informer-dot` in `static/css/huginn.css`

```css
.hg-informer-dot {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--bs-font-monospace);
  font-size: 0.7rem;
  font-weight: 600;
  min-width: 2.4rem;
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  cursor: default;
}
.hg-informer-dot--green  { background: var(--bs-success-bg-subtle); color: var(--bs-success-text-emphasis); }
.hg-informer-dot--orange { background: var(--bs-warning-bg-subtle); color: var(--bs-warning-text-emphasis); }
.hg-informer-dot--red    { background: var(--bs-danger-bg-subtle);  color: var(--bs-danger-text-emphasis);  }
.hg-informer-dot--grey   { background: var(--bs-secondary-bg);      color: var(--bs-secondary-color);       }
```

### Step 7 — Write view tests

File: `tests/integration/test_projects_detail_variables_tab.py` (new):

- `test_project_detail_has_variables_tab`: GET `?tab=vitals`; assert `data-testid="project-tab-variables"` in body.
- `test_variables_tab_renders`: GET `?tab=variables`; assert status 200; assert `data-testid="project-pane-variables"` implied by period buttons.
- `test_variables_period_buttons_present`: GET `?tab=variables`; assert "Today" and "This week" in body.
- `test_informer_bar_present_on_vitals`: GET `?tab=vitals`; assert `data-testid="project-informer-bar"` in body.
- `test_informer_bar_empty_state_no_playbook`: GET for project with no Playbook; assert "No Playbook assigned" in body.
- `test_informer_bar_dots_for_assigned_playbook`: assign a Playbook with 2 variables; GET vitals; assert 2 `hg-informer-dot` spans in body.
- `test_variables_tab_default_period`: GET `?tab=variables` without period param; assert `btn-primary` on "This week" button.

### Step 8 — Checkpoint

```bash
pytest tests/integration/test_projects_detail_variables_tab.py -x
```

### Step 9 — Full suite

```bash
pytest tests/ -x
```

### Step 10 — Commit

```
feat(projects): add Variables tab and informer bar to Project detail

Adds a Variables tab with period filter (today/yesterday/this week/
last week/30 days) and a diagram grid placeholder per PlaybookVariable.
Adds an informer bar on the Vitals tab showing one colored dot per
Variable.  Dots use grey until SitRep AI integration delivers values.
```

---

## Acceptance Criteria

- [ ] `pytest tests/integration/test_projects_detail_variables_tab.py -x` passes
- [ ] No regressions: `pytest tests/ -x` passes
- [ ] GET `?tab=vitals` shows three tabs: Vitals, Variables, Increments
- [ ] GET `?tab=vitals` shows the informer bar with `data-testid="project-informer-bar"`
- [ ] GET `?tab=variables` shows period buttons for all 5 periods; shows one diagram card per PlaybookVariable (or empty state if no Playbook assigned)
- [ ] Project with no Playbook shows "No Playbook assigned" in informer bar
