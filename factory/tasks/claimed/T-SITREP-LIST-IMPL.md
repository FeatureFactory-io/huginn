---
id: T-SITREP-LIST-IMPL
role: feature-builder
attempt: 1
depends_on: [T-SITREP-LIST-STEPS]
gitlab_issue: 76
branch: factory/T-SITREP-LIST-IMPL-list-screen
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - ui/views/sitrep.py
  - ui/templates/ui/sitrep/list.html
  - ui/templates/ui/sitrep/_list_row.html
  - ui/urls.py
  - ui/services/sitrep_service.py
  - ui/templates/ui/projects/detail.html  # ONE-line href fix on line 39 (SITREP-LIST+FIND-02)
---

## LE-note (2026-05-14, T-SITREP-LIST-STEPS integration)

The step-def-writer landed **19 RED tests** (not 22 — feature file numbers
01,02,06–22 with gaps at 03/04/05). Acceptance is therefore **19 passed**, not
22. Three integration flags from the step-def-writer's MR !31 result block:

1. **SITREP-LIST+FIND-02 — `ui/templates/ui/projects/detail.html` line 39**
   currently has placeholder `<a href="#" data-testid="project-open-sitreps">`
   with TODO comment. Test 02 asserts `f'href="{reverse("sitrep-list", ...)}"'`.
   Update line 39 to `href="{% url 'sitrep-list' project.pk %}"` and remove the
   TODO. (`ui/templates/ui/projects/detail.html` added to `files_in_scope`.)

2. **SITREP-LIST+FIND-19 — Custom-period datetime picker missing in mockup**.
   Mockup at `ui/templates/ui/mockups/sitrep/list.html` exposes
   `data-testid="sitrep-period-custom"` link but no From/To `<input>` fields.
   Test 19 asserts `'name="from_dt"' in body OR 'data-testid="sitrep-custom-from"' in body`
   (and same for `to_dt`). **In your ported template** (`ui/templates/ui/sitrep/list.html`)
   add a hidden-by-default `<div data-testid="sitrep-custom-period-region">` containing
   `<input type="datetime-local" name="from_dt" data-testid="sitrep-custom-from">` +
   `<input type="datetime-local" name="to_dt" data-testid="sitrep-custom-to" value="…now…">`
   inside the existing Generate dropdown. Do **not** edit the mockup — the
   production template is allowed to extend the mockup where the mockup is
   incomplete; the mockup is reference, not contract.

3. **Existing `sitrep_generate_view`** (landed by T-SITREP-GEN) already POSTs to
   `sitrep-generate`. Your scenario 20 test issues
   `client.get(_list_url(project), {"generated": "1", "period": "since_last"})`
   expecting `data-testid="sitrep-generation-toast"` and the toast text in the
   GET-rendered list. Render the toast region when `request.GET.get("generated")`
   is truthy (one extra context flag — `show_toast` — is already in your locked
   interface).

---

# Task T-SITREP-LIST-IMPL — port SITREP-LIST+FIND-1 to production

## Goal

Make every test in `tests/ui/test_sitrep_list_scenarios.py` GREEN by porting
the mockup `ui/templates/ui/mockups/sitrep/list.html` to a real Django view +
template + URL pattern. Do **not** modify the test file.

## Must read first

1. **GitLab issue #76** — `glab issue view 76`.
2. [`factory/blueprints/T-SITREP-LIST-IMPL.md`](../../blueprints/T-SITREP-LIST-IMPL.md) —
   especially "Interfaces locked" (context vars).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. **Source mockup** — `ui/templates/ui/mockups/sitrep/list.html`. **Port,
   do not redesign.** All `data-testid` attributes carry over verbatim.
5. **Reference pattern** — `ui/views/fragos.py` `FragosListView` +
   `ui/templates/ui/fragos/list.html`. Same auth, same filter form pattern,
   same row-action dropdown.
6. **Test contract (do not modify)** —
   `tests/ui/test_sitrep_list_scenarios.py` (landed by T-SITREP-LIST-STEPS).
7. `ui/urls.py` — note the existing `# TODO(sitrep-sprint): …` placeholder
   on line 79 above `projects-detail`.

## Acceptance criteria

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
# expect: 19 passed   (feature file has 19 scenarios: 01,02,06–22 — gaps at 03/04/05)
ruff check . && ruff format --check .
# clean
# Acceptance is THIS test file ONLY. Confirm no previously-GREEN test regresses,
# but do NOT chase the rest of the suite green — T-SITREP-VIEW-* tests are
# intentionally RED and belong to a downstream task. Anything outside the
# files-in-scope list below will be auto-rejected.
```

## Files in scope

- `ui/views/sitrep.py` — `SitRepListView(LoginRequiredMixin, View)` with
  GET handler. T-SITREP-GEN already created this file with
  `sitrep_generate_view`; **extend, do not replace**.
- `ui/templates/ui/sitrep/list.html` (NEW) — port from
  `ui/templates/ui/mockups/sitrep/list.html`. Replace mockup URL names:
  - `{% url 'mockup-sitrep-list' %}` → `{% url 'sitrep-list' project.pk %}`
  - `{% url 'mockup-sitrep-view' r.id %}` → `{% url 'sitrep-view' project.pk r.id %}`
    (relies on T-SITREP-VIEW-IMPL — see "Risks" in blueprint; if that route
    hasn't landed at integration time, the LE will sequence merges).
  - Wire the Generate POST through `{% url 'sitrep-generate' project.pk %}`
    forms, hidden `period` input.
- `ui/templates/ui/sitrep/_list_row.html` (optional) — extract row markup if
  the page exceeds ~250 lines.
- `ui/urls.py` — replace the `# TODO(sitrep-sprint): …` line with
  `path("projects/<int:project_pk>/sitreps/", SitRepListView.as_view(),
  name="sitrep-list")`. Keep the line ABOVE `projects-detail` to avoid URL
  shadowing surprise.
- `ui/services/sitrep_service.py` (NEW, optional) —
  `sitrep_list_queryset(project, filters: dict) -> QuerySet[SitRep]` that
  applies trigger / pb_version / date filters. Use only if the view body
  exceeds ~80 LoC.

## Context variables (locked — tests assert these)

See blueprint "Interfaces locked". Summary: `project`, `rows` (list of
dicts), `trigger_choices`, `pb_version_choices`, `filter_trigger`,
`filter_pb_version`, `filter_from`, `filter_to`, `since_last_label`,
`since_last_disabled`, `show_toast`.

`row` dict keys: `id`, `generated_at` (e.g. `"2026-05-11 13:15"`),
`assessed_period` (e.g. `"Mon 09:00 → 13:15"`), `trigger`
(`"automatic"|"manual"`), `trigger_label` (`"Auto"|"Manual"`), `headline`,
`decisions_proposed` (always 0 this milestone), `decisions_accepted` (always
0), `pb_version` (int).

## Do not touch

- `tests/ui/test_sitrep_list_scenarios.py` — frozen contract.
- `tests/ui/conftest.py` — frozen.
- `gjallarhorn/`, `sitrep/models/`, `ingestion/models/` — model surface frozen.
- `ui/views/sitrep.py::sitrep_generate_view` body — owned by T-SITREP-GEN;
  extend the **module**, do not rewrite the existing function.
- `ui/templates/ui/mockups/sitrep/*` — mockups are reference, not target.
- **No `FOB-*` Screen IDs** (`.cursor/rules/no-fob-screen-ids.mdc`).

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-SITREP-LIST-IMPL-list-screen

# … port mockup, wire view, register URL …

.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(ui): SitRep list screen (port from mockup, SITREP-LIST+FIND-1)"
git push -u origin factory/T-SITREP-LIST-IMPL-list-screen

glab mr create \
  --source-branch factory/T-SITREP-LIST-IMPL-list-screen \
  --target-branch main \
  --title "feat(ui): SitRep list screen (SITREP-LIST+FIND-1)" \
  --description "Implements SITREP-LIST+FIND-1 (#76). 19 RED tests in tests/ui/test_sitrep_list_scenarios.py go GREEN. Ports ui/templates/ui/mockups/sitrep/list.html.

Closes #76 (paired with T-SITREP-LIST-STEPS)" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
# expect: 19 passed
```

## Do not

- Do NOT redesign markup — port from mockup, change only URL names + context
  variable references.
- Do NOT modify the test file.
- Do NOT add new `data-testid` attributes the mockup doesn't have.
- Do NOT POST in this view — the form posts to `sitrep-generate` (T-SITREP-GEN).
- Do NOT introduce `FOB-*` Screen IDs.

# Result

status:
branch:
mr:
commit_sha:
