# Blueprint: T-SITREP-LIST-IMPL — port SITREP-LIST+FIND-1 from mockup to production

**Issue:** [#76](https://gitlab.com/dp2580/huginn/-/issues/76) — SITREP-LIST+FIND-1
**Task:** [`factory/tasks/pending/T-SITREP-LIST-IMPL.md`](../tasks/pending/T-SITREP-LIST-IMPL.md)
**Predecessor:** T-SITREP-LIST-STEPS (defines the test contract)

## Goal

Land the production SitRep list screen by porting the mockup at
`ui/templates/ui/mockups/sitrep/list.html` to a real Django view +
template + URL. Make every test in
`tests/ui/test_sitrep_list_scenarios.py` (RED on `main` after T-SITREP-LIST-STEPS
merges) go GREEN — without modifying that test file.

## Context

- Existing wiring patterns to mirror: `ui/views/fragos.py` (`FragosListView`)
  + `ui/templates/ui/fragos/list.html`. Same auth (`@login_required` /
  `LoginRequiredMixin`), same filter-form pattern (`?trigger=…&pb_version=…`),
  same row-action dropdown.
- The view receives `project_pk` from the URL (Project lookup via
  `get_object_or_404(Project, pk=project_pk)`). Renders a list of `SitRep`
  rows for that project, paginated by 50 (sufficient — there is no Gherkin
  scenario asserting pagination this milestone, but keep the pattern
  consistent with `FragosListView`).
- Filters: `trigger` (`""|automatic|manual`), `pb_version` (int), and a
  date-range `(from, to)` matching `generated_at` (LIST-FIND-13). Date filter
  is keyed on the **date** part of `generated_at` (use `__date__gte` / `__date__lte`).
- "Since last SitRep" computed label is **server-rendered** in the template
  context (`since_last_label`, `since_last_disabled`). The test asserts
  presence of the testid + the disabled state when no prior SitRep exists.
- Period dropdown buttons each link to `?generated=1&period=<key>` for the
  GET-style fallback OR (preferred) submit a hidden form to
  `sitrep-generate` (T-SITREP-GEN's POST endpoint) with `period=<key>`.
  Either is acceptable as long as the markup matches the mockup testids.

## Files touched

| File | Change |
|------|--------|
| `ui/views/sitrep.py` | extend (T-SITREP-GEN created the file with `sitrep_generate_view`). Add `SitRepListView(LoginRequiredMixin, View)` with GET handler. |
| `ui/templates/ui/sitrep/list.html` | NEW — port from mockup, replace `mockup-sitrep-*` URL names with real ones (`sitrep-list`, `sitrep-view`, `sitrep-generate`), wire real context vars. |
| `ui/templates/ui/sitrep/_list_row.html` (optional) | extracted partial if the row markup is reused. |
| `ui/urls.py` | `path("projects/<int:project_pk>/sitreps/", SitRepListView.as_view(), name="sitrep-list")`. Replace the existing `# TODO(sitrep-sprint): …` line. |
| `ui/services/sitrep_service.py` (NEW, optional) | `sitrep_list_queryset(project, filters)` mirrors the fragos service pattern if the view becomes >150 LoC. |

## Interfaces locked

- URL name: `sitrep-list` → `/projects/<int:project_pk>/sitreps/`.
- Context variables passed to template:
  - `project` (Project instance)
  - `rows` (list of SitRep rows ordered `-generated_at`, sliced to page)
  - `trigger_choices` (list of `(value, label)` tuples — `automatic→"Auto"`,
    `manual→"Manual"`)
  - `pb_version_choices` (distinct version ints from this project's SitReps)
  - `filter_trigger`, `filter_pb_version`, `filter_from`, `filter_to`
  - `since_last_label` (`"Since last SitRep"` or `"Since last SitRep (3h 20m ago)"`)
  - `since_last_disabled` (bool — True when no prior SitRep for this project)
  - `show_toast` (bool — True when `?generated=1` is present)
- The row dict uses the same keys the mockup reads: `id`, `generated_at`
  (formatted), `assessed_period` (formatted), `trigger`, `trigger_label`,
  `headline`, `decisions_proposed` (always 0 this milestone),
  `decisions_accepted` (always 0), `pb_version` (int).
- Empty state: rendered by `{% empty %}` block with the same testids as the
  mockup (`sitrep-empty-state`, `empty-state-cta`).

## Risks

- **URL collision** — `ui/urls.py` already has `path("projects/<int:pk>/", …,
  name="projects-detail")`. Putting `projects/<int:project_pk>/sitreps/`
  AFTER `projects-detail` is fine — Django picks the longer match. But
  rename the parameter (`project_pk` not `pk`) to avoid confusion.
- The mockup uses `{% url 'mockup-sitrep-list' %}` for the filter form's
  GET action — port to `{% url 'sitrep-list' project.pk %}`. The mockup uses
  `{% url 'mockup-sitrep-view' r.id %}` for row links — port to
  `{% url 'sitrep-view' project.pk r.id %}` (depends on T-SITREP-VIEW-IMPL
  having registered the route — note the cross-task dependency).
- LIST-FIND-08 asserts the row View `<a>` `href` only; if T-SITREP-VIEW-IMPL
  hasn't merged when this task runs, use a placeholder URL pattern that
  resolves to `#` and **flag** in the result block. Cleaner: defer this
  task's MR merge until T-SITREP-VIEW-IMPL is queued (factory dependency
  ordering handles it via `depends_on: [T-SITREP-LIST-STEPS]` plus the
  manual ordering hint in the blackboard).
- LIST-FIND-13 date filter: tests use literal datetimes `2026-05-09 09:00`
  vs `2026-05-11 13:15`. Filter inputs are `from=2026-05-11&to=2026-05-11`.
  Use `__date__gte` / `__date__lte` so a single-day range matches anything
  that day.
- LIST-FIND-15..20 (Generate dropdown): the dropdown markup must include
  `data-testid="generate-sitrep-btn"` AND `aria-label="Generate SitRep"` on
  the button (LIST-FIND-22 asserts both). Each preset `<a>`/`<li>` carries
  its own testid (`sitrep-period-since-last`, `sitrep-period-2h`,
  `sitrep-period-4h`, `sitrep-period-today`, `sitrep-period-yesterday`,
  `sitrep-period-custom`). Custom period: open a `<form>` with
  `name="period" value="custom"` + `from`/`to` datetime inputs; the form
  posts to `sitrep-generate`.

## Acceptance

```
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
# expect: 22 passed
.venv/bin/python -m pytest tests/ -x
# expect: full suite green
ruff check . && ruff format --check .
# clean
```
