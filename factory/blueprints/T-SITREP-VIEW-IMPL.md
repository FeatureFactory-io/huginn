# Blueprint: T-SITREP-VIEW-IMPL — port SITREP-VIEW_SITREP-1 from mockup to production

**Issue:** [#77](https://gitlab.com/dp2580/huginn/-/issues/77) — SITREP-VIEW_SITREP-1
**Task:** [`factory/tasks/pending/T-SITREP-VIEW-IMPL.md`](../tasks/pending/T-SITREP-VIEW-IMPL.md)
**Predecessor:** T-SITREP-VIEW-STEPS

## Goal

Land the production SitRep detail screen by porting
`ui/templates/ui/mockups/sitrep/view.html` to a real Django view + template +
URL. Make every test in `tests/ui/test_sitrep_view_scenarios.py` GREEN.

## Context

- Reference patterns: `ui/views/fragos.py::FragosDetailView` +
  `ui/templates/ui/fragos/detail.html`. Same `LoginRequiredMixin`,
  `get_object_or_404` pattern, breadcrumb structure.
- Read-only screen — no `EditView` companion this milestone (VIEW-28).
- Five sections to render: Situation Assessment, Variables Snapshot
  (placeholder), Decisions (placeholder), FRAGOs Applied, Notable Activity.
- `SitRep.fragos_applied` (M2M) and `SitRep.notable_activity` (JSONField,
  list of `{email, commits}`-ish dicts written by T-SITREP-GEN) are the
  data sources for sections 4 & 5.
- The "Open Chat about this SitRep" link target is the URL named
  `chat-fullscreen` if present in `ui/urls.py`. If not, use `href="#"` plus
  `data-testid="sitrep-open-chat-link"` and document the chat-milestone TODO.

## Files touched

| File | Change |
|------|--------|
| `ui/views/sitrep.py` | extend — add `SitRepDetailView(LoginRequiredMixin, View)`. |
| `ui/templates/ui/sitrep/view.html` | NEW — port from mockup; replace mockup URL names; wire context. |
| `ui/urls.py` | `path("projects/<int:project_pk>/sitreps/<int:pk>/", SitRepDetailView.as_view(), name="sitrep-view")`. Place ABOVE `projects-detail`. |

## Interfaces locked

- URL name: `sitrep-view` → `/projects/<int:project_pk>/sitreps/<int:pk>/`.
- Context variables passed to template:
  - `project` (Project instance)
  - `sitrep` (SitRep instance)
  - `assessed_period` (formatted: `"Mon 09:00 → 13:15"` from
    `localtime(from_dt).strftime("%a %H:%M")` + `" → "` + `localtime(to_dt).strftime("%H:%M")`)
  - `trigger_label` (`"Auto"` or `"Manual"`)
  - `mode_label` (`"Semi-Auto"` or `"Auto"`)
  - `pb_version_label` (`"v{n}"`)
  - `fragos_applied` (queryset / list ordered by title)
  - `notable_activity` (list of dicts; iterate in template)
  - `since_last_label` (computed for the "Generate SitRep for another
    period" dropdown, default-selecting "Since last SitRep" with this SitRep
    as anchor — VIEW-26)
  - `back_url` (reverse of `sitrep-list` for this project — VIEW-29)
  - `chat_url` (reverse of `chat-fullscreen` if registered, else `"#"`)

## Risks

- VIEW-02 timezone: `localtime(from_dt)` requires `USE_TZ=True` and a
  configured `TIME_ZONE`. Confirm settings — both should already be the case
  but verify in the worktree.
- VIEW-04 / VIEW-08: render Manual / Auto badges based on `sitrep.trigger`
  / `sitrep.mode_at_generation` directly — no toggling JS.
- VIEW-13 / VIEW-15: render the literal placeholder strings inside the
  Variables Snapshot / Decisions section bodies.
- VIEW-17 (FRAGO link): `<a href="{% url 'fragos-detail' f.pk %}">` — that
  URL name exists today (`ui/urls.py:69`).
- VIEW-19 / VIEW-23 empty states: literal strings — match what the test
  asserts.
- VIEW-22 vs VIEW-23 (Notable Activity): if `sitrep.notable_activity` is
  empty list / None → render the absent / empty-state copy
  ("No notable activity in this period"). If populated → render
  "<contributor> — N commits" lines per entry.
- VIEW-26 dropdown: same period picker as the LIST screen — extract a
  template partial `_generate_period_dropdown.html` shared by LIST and VIEW
  if convenient (small win for DRY but optional).
- VIEW-28 (read-only): ensure NO element with text "Edit", "Delete",
  "Modify", or testids `sitrep-edit-btn` / `sitrep-delete-btn` ever renders.

## Acceptance

```
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
# expect: 31 passed
.venv/bin/python -m pytest tests/ -x
# full suite green
ruff check . && ruff format --check .
# clean
```
