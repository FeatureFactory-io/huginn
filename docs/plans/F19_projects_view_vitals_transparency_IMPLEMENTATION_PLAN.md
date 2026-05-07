# F19 — PROJECTS-VIEW_VITALS Vitals Transparency widget (BPE)

**Feature:** `docs/features/act-2-projects/projects-view-vitals-tab.feature`
**Milestone:** [Datasources & Projects](https://gitlab.com/dp2580/huginn/-/milestones/7416198) (active)
**Depends on:** F17 (tabs), F18 (Increments tab + `IncrementsService` pattern), F13 (`Increment` model)

**GitLab issues** (both on milestone *Datasources & Projects*):

- **F19a** — Implementation: service, template, `humanize`, a11y — [huginn#32](https://gitlab.com/dp2580/huginn/-/issues/32)
- **F19b** — Integration tests: BDD scenarios 01–07 — [huginn#33](https://gitlab.com/dp2580/huginn/-/issues/33) (linked to #32)

## Clarifications (batch — resolve before merge)

1. **Empty-state copy:** Feature file allows "Never" / "—" / "No commits yet" (TBD). Pick final strings in template and update Gherkin if needed.
2. **Failed sync + `last_sync_at`:** Sync engine sets `last_sync_at` on error paths too (`SyncEngine.run_for_project`). Transparency "Last sync" therefore means "last sync *attempt* finished at" unless product defines otherwise — document in template `title` tooltip if helpful.
3. **Sync section redundancy:** Today `detail.html` shows raw `last_sync_at` under Sync. Plan: **remove duplicate "Last sync" line from Sync section**; recency lives only in Transparency (relative). Sync keeps schedule + next-run note + badge remains in header.

## Context Map

| File | Lines | Note |
|------|-------|------|
| [ui/views/projects.py](../../ui/views/projects.py) | 172–196 | Follow `ProjectsDetailView.get` pattern: call a `ui/services` read-model, pass extra fields into template context |
| [ui/services/increments_service.py](../../ui/services/increments_service.py) | 76–92 | Pattern: thin read-model service wrapping ORM; no HTTP; no sync side effects |
| [ui/templates/ui/projects/detail.html](../../ui/templates/ui/projects/detail.html) | 69–107 | Add Transparency **card** before Identity stack; reuse Bootstrap card + `hg-vitals-section` spacing |
| [ingestion/models/__init__.py](../../ingestion/models/__init__.py) | 163–224 | `Project.last_sync_at`, `Increment` indexes on `(project, occurred_at)` — use for `Max`/`first()` query |
| [tests/integration/test_projects_view_vitals_tab.py](../../tests/integration/test_projects_view_vitals_tab.py) | — | Extend: deep-link `?tab=vitals`, Transparency testids, coexistence with Identity/Playbook/Sync |
| [huginn/settings/base.py](../../huginn/settings/base.py) | 19–36 | Add `django.contrib.humanize` for `naturaltime` in templates |

## Do Not Do

- Do NOT put ORM queries or freshness rules in `ProjectsDetailView` — delegate to `ui/services` (SAO: `ui/` views do not own business logic).
- Do NOT change sync engine semantics, `IngestionRun`, or Celery tasks for this feature.
- Do NOT add async views or client-side-only freshness (no SPA timers); server renders relative strings at request time.
- Do NOT implement additional Vitals widgets beyond **Transparency** in this milestone slice.
- Do NOT strip or relocate Increments tab behavior — coexistence is scenario 06.
- Do NOT edit `ui/views/mockups/` unless you explicitly bring mockups to parity (out of scope unless requested).

## SAO.md Sections That Apply

- **§1 Application Blocks — `ui/`:** Server-rendered templates; **`ui/` must not contain business logic**; ingestion owns models and sync updates to `last_sync_at` / `Increment` rows.
- **§1 Ingestion sync engine:** Read-only queries only; idempotent upserts remain in sync — this feature only **reads** `Project` / `Increment`.
- **§3 Code Organization:** Templates kebab-case; Python `snake_case`; URLs unchanged.
- **§4 Data Architecture:** Use existing indexes; prefer `order_by('-occurred_at').values_list('occurred_at', flat=True)[:1]` or `.aggregate(Max('occurred_at'))` for latest commit time — avoid loading full rows.
- **§5 Test Strategy:** `pytest` + `pytest-django`; integration tests use real DB + factories (no HTTP mocking for this screen).
- **§7 Error Handling:** Surface sync errors via existing header badge / Sync section; Transparency shows time of last finished sync attempt (see Clarifications).

## Rule references (during implementation)

- `.cursor/rules/*` — follow project-specific rules (e.g. screen IDs / FOB conventions if applicable).
- BPE test-first: red → green → small commits (`feat(ui): …`, `test(ui): …`).

## Implementation plan (scenario order)

### Initial setup

- Branch: `feature/f19-vitals-transparency` (or equivalent).

### Scenarios 03–05, 07 — Transparency widget (core)

1. **Settings:** Add `"django.contrib.humanize"` to `INSTALLED_APPS` in `huginn/settings/base.py`.
2. **Service:** Create `ui/services/project_vitals_service.py` (name flexible) with a small public method, e.g. `latest_increment_occurred_at(project_id: int) -> datetime | None`, implemented as a single indexed ORM query. Keep public method short; extract helpers if needed (BPE: ≤20–30 lines).
3. **View:** In `ProjectsDetailView.get`, call the service when rendering (or always pass `latest_commit_at` / `None`). Do not branch on tab: Vitals context can be computed once per GET (cheap query).
4. **Template:** In `detail.html` at top of vitals column:
   - `{% load humanize %}`.
   - Add card `data-testid="project-widget-transparency"` titled "Transparency".
   - Rows: **Last sync** (`data-testid="project-transparency-last-sync"`) — `project.last_sync_at|naturaltime` or empty-state span; **Last commits** (`data-testid="project-transparency-last-commits"`) — `latest_commit_at|naturaltime` or empty-state.
   - **A11y (07):** use semantic grouping (`<section>`, headings, `<dl>` with `<dt>`/`<dd>`) so labels are explicit; ensure `aria-labelledby` where appropriate.
5. **Dedup Sync section:** Remove the redundant "Last sync: …" paragraph from Sync section; keep schedule + "Next: …" copy.

### Scenarios 01–02, 06 — Tab visibility, deep-link, coexistence

6. **Integration tests** in `test_projects_view_vitals_tab.py`:
   - **01:** Assert Vitals tab control with `project-tab-vitals` and Increments label present (may already hold — tighten to match feature wording).
   - **02:** `GET` detail with `?tab=vitals` → response 200 and vitals pane active indicators (e.g. `nav-link active` on Vitals, `tab-pane active` on vitals pane) — parse HTML or use stable substrings.
   - **06:** With Transparency present, assert `project-source-path`, `project-playbook-section`, `project-sync-schedule` (or equivalent) still in body; assert Increments table markup only when `tab=increments`.

### Scenarios 04–05 — Edge cases

7. **Never synced:** `last_sync_at=None` → Transparency shows chosen empty copy; element with `project-transparency-last-sync` still present.
8. **No increments:** no `Increment` rows → `project-transparency-last-commits` present with empty copy.

## Tests to add or extend

| Test file | What it proves |
|-----------|----------------|
| `tests/unit/test_project_vitals_service.py` (new) | Latest occurred_at is `None` with no rows; returns max `occurred_at` with multiple `Increment` rows (two timestamps). |
| `tests/integration/test_projects_view_vitals_tab.py` (extend) | BDD 01–07: tabs, `?tab=vitals`, Transparency testids + naturaltime substrings for controlled `last_sync_at` / `Increment.occurred_at` in the past (`timedelta`), empty states, coexistence blocks, basic a11y structure (`<dt>` / labels). |

**Checkpoint (full Vitals BDD file target):**

```bash
pytest tests/integration/test_projects_view_vitals_tab.py tests/unit/test_project_vitals_service.py -x -q
```

**Regression:**

```bash
pytest tests/ -x -q
```

## Commit strategy

- Small vertical slices: `feat(settings): enable humanize`, `feat(ui): add ProjectVitalsService`, `feat(ui): Transparency card on project Vitals`, `test(ui): vitals transparency scenarios`, etc. — Angular-style subjects.

## Acceptance criteria (plan-level)

- [ ] All scenarios in `projects-view-vitals-tab.feature` covered by tests or explicitly deferred with user approval.
- [ ] Checkpoint commands pass locally and in CI.
- [ ] GitLab issues F19a + F19b closed with MR link.

## Submit for approval

Per BPE Step 9: do **not** merge implementation until product owner explicitly approves this plan (done in chat / MR description).

## Execution (Red / Green / Refactor)

The micro-plan with one TDD cycle per scenario lives in [`F19_TDD_EXECUTION_PLAN.md`](F19_TDD_EXECUTION_PLAN.md). It covers all seven Gherkin scenarios from `projects-view-vitals-tab.feature` and three unit tests for `ProjectVitalsService`, in commit order.
