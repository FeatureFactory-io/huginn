---
id: T-SITREP-VIEW-IMPL
role: feature-builder
attempt: 1
depends_on: [T-SITREP-VIEW-STEPS]
gitlab_issue: 77
branch: factory/T-SITREP-VIEW-IMPL-detail-screen
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - ui/views/sitrep.py
  - ui/templates/ui/sitrep/view.html
  - ui/templates/ui/sitrep/_generate_period_dropdown.html
  - ui/urls.py
---

## LE-note (2026-05-14, T-SITREP-LIST-IMPL integration)

T-SITREP-LIST-IMPL hardcoded `<a href="/projects/{{ project.pk }}/sitreps/{{ r.id }}/">`
in `ui/templates/ui/sitrep/list.html` (row headline link AND dropdown View item) as a
forward-reference to the URL **this** task will register. Test 08
(`SITREP-LIST+FIND-08 Row View action navigates to SITREP-VIEW_SITREP-1`) only
asserts the substring `f"/sitreps/{sitrep.pk}/"` so it currently passes against
the hardcoded path, but the actual click-through 404s until you register the
real route.

**Constraint locked in:** your `ui/urls.py` entry MUST be exactly:

```python
path(
    "projects/<int:project_pk>/sitreps/<int:pk>/",
    SitRepDetailView.as_view(),
    name="sitrep-view",
),
```

Anything else (different path shape, different kwarg names, view-only without
project scope) breaks the View dropdown click on the list screen. If your
test contract for T-SITREP-VIEW-STEPS uses different kwarg names
(`reverse('sitrep-view', kwargs={...})`), reconcile against this URL pattern —
list-screen integration wins because list-screen is already on `main`.

---

# Task T-SITREP-VIEW-IMPL — port SITREP-VIEW_SITREP-1 to production

## Goal

Make every test in `tests/ui/test_sitrep_view_scenarios.py` GREEN by porting
the mockup `ui/templates/ui/mockups/sitrep/view.html` to a real Django view +
template + URL pattern. Do **not** modify the test file.

## Must read first

1. **GitLab issue #77** — `glab issue view 77`.
2. [`factory/blueprints/T-SITREP-VIEW-IMPL.md`](../../blueprints/T-SITREP-VIEW-IMPL.md) —
   especially "Interfaces locked" (context vars).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. **Source mockup** — `ui/templates/ui/mockups/sitrep/view.html`. **Port,
   do not redesign.**
5. **Reference pattern** — `ui/views/fragos.py::FragosDetailView` +
   `ui/templates/ui/fragos/detail.html`.
6. **Test contract (do not modify)** —
   `tests/ui/test_sitrep_view_scenarios.py` (landed by T-SITREP-VIEW-STEPS).
7. `ui/views/sitrep.py` — has `sitrep_generate_view` (T-SITREP-GEN) and
   `SitRepListView` (T-SITREP-LIST-IMPL); **extend, do not replace**.

## Acceptance criteria

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
# expect: 31 passed
ruff check . && ruff format --check .
# clean
# Acceptance is THIS test file ONLY. Confirm no previously-GREEN test regresses,
# but do NOT chase the rest of the suite green. Anything outside the
# files-in-scope list below will be auto-rejected.
```

## Files in scope

- `ui/views/sitrep.py` — `SitRepDetailView(LoginRequiredMixin, View)` GET
  handler. `get_object_or_404(SitRep, pk=pk, project_id=project_pk)` to
  prevent cross-project URL guessing.
- `ui/templates/ui/sitrep/view.html` (NEW) — port from
  `ui/templates/ui/mockups/sitrep/view.html`. Replace mockup URLs:
  - `{% url 'mockup-sitrep-list' %}` → `{% url 'sitrep-list' project.pk %}`
  - `{% url 'mockup-fragos-view' f.id %}` → `{% url 'fragos-detail' f.pk %}`
  - Wire chat link to `{% url 'chat-fullscreen' %}` if registered, else
    `href="#"` (chat milestone wires the route — leave a TODO).
- `ui/templates/ui/sitrep/_generate_period_dropdown.html` (optional) —
  partial shared with the list screen.
- `ui/urls.py` — add
  `path("projects/<int:project_pk>/sitreps/<int:pk>/", SitRepDetailView.as_view(), name="sitrep-view")`.
  Place ABOVE `projects-detail` to avoid URL shadowing.

## Context variables (locked — tests assert these)

See blueprint "Interfaces locked". Summary: `project`, `sitrep`,
`assessed_period`, `trigger_label`, `mode_label`, `pb_version_label`,
`fragos_applied`, `notable_activity`, `since_last_label`, `back_url`,
`chat_url`.

## Do not touch

- `tests/ui/test_sitrep_view_scenarios.py` — frozen contract.
- `tests/ui/conftest.py` — frozen.
- `gjallarhorn/`, `sitrep/models/`, `ingestion/models/`, `playbooks/` —
  model surface frozen.
- `sitrep_generate_view` body — owned by T-SITREP-GEN; extend the module,
  don't rewrite.
- `SitRepListView` body — owned by T-SITREP-LIST-IMPL.
- `ui/templates/ui/mockups/sitrep/*` — mockups are reference, not target.
- `ui/templates/ui/sitrep/list.html` — owned by T-SITREP-LIST-IMPL.
- **No `FOB-*` Screen IDs** (`.cursor/rules/no-fob-screen-ids.mdc`).

## Branch & MR

```bash
cd .worktrees/feature-builder
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-SITREP-VIEW-IMPL-detail-screen

# … port mockup, wire view, register URL …

.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
.venv/bin/python -m pytest tests/ -x
ruff check . && ruff format --check .

git add -A
git commit -m "feat(ui): SitRep detail screen (port from mockup, SITREP-VIEW_SITREP-1)"
git push -u origin factory/T-SITREP-VIEW-IMPL-detail-screen

glab mr create \
  --source-branch factory/T-SITREP-VIEW-IMPL-detail-screen \
  --target-branch main \
  --title "feat(ui): SitRep detail screen (SITREP-VIEW_SITREP-1)" \
  --description "Implements SITREP-VIEW_SITREP-1 (#77). 31 RED tests in tests/ui/test_sitrep_view_scenarios.py go GREEN. Ports ui/templates/ui/mockups/sitrep/view.html.

Closes #77 (paired with T-SITREP-VIEW-STEPS)" \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
# expect: 31 passed
```

## Do not

- Do NOT redesign — port from mockup.
- Do NOT modify the test file.
- Do NOT add new `data-testid`s the mockup doesn't have.
- Do NOT introduce edit/delete controls on this screen (VIEW-28).
- Do NOT introduce `FOB-*` Screen IDs.

# Result

status:
branch:
mr:
commit_sha:
