<!-- SCENARIO -->
id: SITREP-LIST+FIND-1
checkpoint:
  command: "pytest tests/views/test_sitrep_list_view.py tests/bdd/test_sitrep_list_find_feature.py -x"
  expected_exit_code: 0
sao_sections:
  - "§3 Code Organization"
  - "§17.1 Component Layers"
do_not_do:
  - "Do NOT delete or modify the mockup at ui/templates/ui/mockups/sitrep/list.html (parity reference)"
  - "Do NOT add Variable / Decision rendering — Status column is the grey 'No Variables' badge for narrative phase"
  - "Do NOT add bulk actions (no use case for SitReps)"
  - "Do NOT inline DB queries in the template — use a service or view helper"
<!-- /SCENARIO -->

## Summary

Production implementation of `SITREP-LIST+FIND-1` per `docs/features/act-5-sitrep/sitrep-list-find.feature`. Replaces `/mockups/sitrep/` with real DB-backed views at `/sitrep/<project_slug>/`, parity with the canonical mockup at `ui/templates/ui/mockups/sitrep/list.html`.

**UX note (2026-05):** The mock and feature file are **table-first** — there is **no** separate pinned “latest SitRep” card above the history table. The newest SitRep is the **first row** of the history table. Filters + **Generate SitRep ▾** toolbar match the mock; last column before actions is **Playbook version** (header text must match the mock).

**Depends on:** `[FOUNDATION]` (SitRep model) + `[SITREP-GENERATE-1]` (generate POST endpoint).

## Context Map

| File | Lines | Note |
|---|---|---|
| `docs/features/act-5-sitrep/sitrep-list-find.feature` | 1–end | Authoritative acceptance criteria (scenario IDs include a gap at 03–05 where pinned-card scenarios were removed). |
| `ui/templates/ui/mockups/sitrep/list.html` | 1–end | **Canonical mockup** — match markup, classes, and `data-testid`s exactly. Do NOT delete; keep as parity reference. |
| `ui/templates/ui/fragos/list.html` | 1–end | Production implementation pattern for filter row + table card + kebab; copy structure, not content. |
| `ui/views/fragos.py` | — | Production view pattern: filter param parsing, project_slug routing, `row_count` for subtitle. Mirror approach. |
| `docs/ux/IA_guidelines.md` | §3.5, §5.2 | LIST page header (entity icon + subtitle) and LIST+FIND data table shell. Do NOT improvise. |

## Do Not Do

- Do NOT delete or modify the mockup at `ui/templates/ui/mockups/sitrep/list.html` — it remains as the parity source per `fragos/list.html` precedent.
- Do NOT render any Variable computation or Decision card data — Status column is the grey `bg-secondary` "No Variables" badge for every row in narrative phase.
- Do NOT add bulk actions (no destructive op exists for SitReps; they are immutable once finalized).
- Do NOT inline DB queries in the template — push everything through a thin view helper or a `sitrep/services/sitrep_query.py` module.
- Do NOT use `table-striped` — IA guidelines require `table-hover` only on LIST+FIND.
- Do NOT add an "Apply" / "Clear filters" button — IA §5.2 mandates immediate-apply filters.
- Do NOT reintroduce a pinned “latest SitRep” summary card — not in mock or `sitrep-list-find.feature`.

## SAO.md Sections That Apply

- **§3 Code Organization** — `ui/views/sitrep.py` is the production view module; `ui/templates/ui/sitrep/list.html` is the production template; URL is wired in `ui/urls.py`.
- **§17.1 Component Layers** — UI reads from `sitrep/` (SitRep ORM); UI never touches `gjallarhorn/` directly except via the manual generate POST endpoint exposed in `[SITREP-GENERATE-1]`.

## Implementation Plan

### A. Branch
- Branch from `features/gjallarhorn`: `feature/sitrep-list-find`.

### B. URL routes — `ui/urls.py`

```
path("sitrep/<slug:project_slug>/",                       sitrep_list,           name="sitrep-list"),
path("sitrep/<slug:project_slug>/generate/",              sitrep_generate,       name="sitrep-generate"),  # exposed in SITREP-GENERATE-1
```

(SITREP-VIEW URL is added in the next issue.)

### C. View — `ui/views/sitrep.py` `sitrep_list`

Responsibilities:
1. Resolve Project by `project_slug` or 404.
2. Parse query params: `trigger` (`automatic|manual|""`), `pb_version` (PK or `""`), `generated` (`"1"` shows toast).
3. Build filtered queryset: `SitRep.objects.filter(project=…)` + filters; order `-generated_at`.
4. Pass **`rows`** as the full ordered queryset (or list) for the **single** history table — newest first. **No** `pinned` / remainder split.
5. Resolve `trigger_choices` (static), `pb_version_choices` (`PlaybookVersion.objects.filter(playbook__projects=project).distinct()`).
6. Compute `row_count` for subtitle.
7. Resolve `next_period_label_since_last` for the dropdown's "Since last SitRep" entry — if **any** SitRep exists for the project, render relative time from latest `generated_at`; else mark disabled with the same tooltip text the mockup uses.

Render `ui/sitrep/list.html`.

### D. Template — `ui/templates/ui/sitrep/list.html`

- `{% extends "base.html" %}` (production base, not `base_mockups.html`).
- Include `{% include "ui/mockups/_screen_anchor.html" with screen_id="SITREP-LIST+FIND-1" screen_testid="sitrep-list-find-loaded" %}` (anchor partial is shared per existing fragos/playbooks production templates).
- Markup is a **direct port** of the mockup `list.html` with these substitutions:
  - URL names: `mockup-sitrep-view` → `sitrep-view`; `mockup-sitrep-list` → `sitrep-list`; period picker hrefs → POST form to `sitrep-generate` (use a single hidden form per dropdown item, or convert items to `<button>` inside one `<form method="post">`).
  - CSRF token in the generate form.
  - All `data-testid`s preserved exactly.
  - **`rows`** only — iterate all SitReps in one `<tbody>` (no pinned card block).
- Row's "Status" column is always `<span class="badge bg-secondary">No Variables</span>` (narrative phase).
- Table header **Playbook version** must match mock spelling.
- Empty state CTA dropdown items also POST to `sitrep-generate` with the appropriate `period`.

### E. Generate POST endpoint reuse

The endpoint is implemented in `[SITREP-GENERATE-1]` issue (#E section). This issue's template uses it via:
```html
<form method="post" action="{% url 'sitrep-generate' project_slug=project.slug %}">
  {% csrf_token %}
  <input type="hidden" name="period" value="today">
  <button type="submit" class="dropdown-item" data-testid="sitrep-period-today">Today</button>
</form>
```
On success the view 302s to `sitrep-list?generated=1` → toast renders.

### F. Navbar entry — `templates/base.html`

Add `<a class="nav-link" href="{% url 'sitrep-list' project_slug=current_project.slug %}">SitReps</a>` to navbar, **only when a project is in scope** (matches IA §4.1 — SitReps are project-scoped, no all-projects route in MVP). If determining `current_project` from request context is non-trivial, expose a context processor; otherwise keep SitRep access via the Project view's existing tab strip and skip the navbar item this round.

### G. Tests

**View tests** — `tests/views/test_sitrep_list_view.py`:
- Anonymous → 302 to login (existing auth pattern).
- Authenticated, no SitReps → empty state rendered, dropdown CTA visible.
- With 3 SitReps → **all three** appear in the **history table**, newest first in row 1 (no separate pinned region).
- Filter `?trigger=automatic` → only auto rows.
- Filter `?pb_version=<id>` → only matching version.
- `?generated=1` → toast element with `data-testid="sitrep-generation-toast"` present.
- Status column always shows `bg-secondary` "No Variables" badge regardless of underlying data.
- All `data-testid`s required by `sitrep-list-find.feature` are present in the rendered HTML.
- 404 for unknown `project_slug`.

**BDD step definitions** — `tests/bdd/test_sitrep_list_find_feature.py`:
- Bind to `docs/features/act-5-sitrep/sitrep-list-find.feature`.
- Implement steps for scenarios **SITREP-LIST+FIND-01, 02, 06–22** (and any renumbered additions) reusing fixtures from the FOUNDATION issue.

**Accessibility smoke** — same tests assert:
- `<h1>` present, page-title icon has `aria-hidden="true"`.
- Filter row has `role="search"`.
- Generate dropdown button has `aria-label="Generate SitRep"`.

### H. Drop mockup-only references

After production templates work, leave the mockup intact (parity precedent) but add a comment header to both production and mockup files cross-referencing each other (see `ui/templates/ui/fragos/list.html` line 2 for the convention).

### I. Commit Strategy

- `feat(ui): production SitRep list view + URL routing`
- `feat(ui): SitRep list+find template (parity with mockup)`
- `test(ui): view + BDD coverage for sitrep-list-find.feature`

## Acceptance Criteria

- [ ] `pytest tests/views/test_sitrep_list_view.py tests/bdd/test_sitrep_list_find_feature.py -x` passes
- [ ] All scenarios in `docs/features/act-5-sitrep/sitrep-list-find.feature` pass via BDD
- [ ] `pytest tests/ -x` passes (no regressions)
- [ ] Production template's markup diff vs mockup is limited to URL-name substitutions, CSRF tokens, and Django ORM iteration — no structural divergence (**no pinned card**)
- [ ] Mockup at `ui/templates/ui/mockups/sitrep/list.html` is unchanged
- [ ] Status column never renders RYG colors (only grey `bg-secondary` "No Variables")
