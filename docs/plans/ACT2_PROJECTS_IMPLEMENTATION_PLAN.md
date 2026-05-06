# Act 2 — Projects (BPE Plan Feature)

## BPE-01 (Plan) vs later steps

**BPE-01 — Plan** (this document) should be the agreed roadmap plus **GitLab tracking issues** (drafts below). Coding and merge requests follow your BPE/MIT cadence after sign-off.

If your team already merged implementation work against this plan, treat the **Implementation record** section as a sync point with the repo; the phased checklist and issue list remain valid for backlog hygiene and audits.

## Scope reality check

The feature files describe **85+ scenarios** across import, list, view, edit, and archive. As of implementation, the codebase includes:

- **GitLab catalog**: [`ingestion/integrations/gitlab_client.py`](../../ingestion/integrations/gitlab_client.py) `list_visible_projects()` (paginated `membership=true`, max pages cap); [`ui/services/projects_service.py`](../../ui/services/projects_service.py) builds catalog entries keyed by GitLab project `id` (string `key`).
- **Import UI**: [`ui/templates/ui/projects/import.html`](../../ui/templates/ui/projects/import.html) — table, bulk bar, client-side find, already-imported badges, connected-GitLab datasource filter, catalog error messaging.
- **`Project` model**: `sync_state`, `source_url`, `imported_by`, `gitlab_project_id`, `sync_schedule`; unique `(datasource, gitlab_project_id)` when id present — [`ingestion/models/__init__.py`](../../ingestion/models/__init__.py), migration `0004_project_act2_fields`.
- **Placeholder sync**: [`ingestion/tasks.py`](../../ingestion/tasks.py) `sync_project_placeholder` + eager tests via import and sync-now flows.
- **Deferred**: Playbook-heavy edit scenarios **PROJECTS-EDIT-05..08**, **PROJECTS-VIEW_PROJECT-12** (SitReps), **PROJECTS-ARCHIVE_PROJECT-05** (dashboard), full playbook list filter **PROJECTS-LIST+FIND-14** until those substrates exist.

The phased plan below is the agreed BPE order; see **Implementation record** at the end for shipped vs checklist mapping.

---

## Mockup-to-operational transfer

Mockups live in `ui/templates/ui/mockups/projects/` and are **reference-only** (never edited for operational behaviour). The five operational templates in `ui/templates/ui/projects/` must adopt the following patterns from the mockups. This list is the delta between what was initially written and what the mockups require.

### Global convention (all five templates)

- Use `<section class="hg-page-header rounded-2 mb-3">` + `<h1 class="hg-page-title …">` — the established pattern in every datasource operational template ([`ui/templates/ui/datasources/`](../../ui/templates/ui/datasources/)). The project templates currently use ad-hoc `<h1 class="h3">` and must be aligned.
- Screen anchors (`data-testid="*-loaded"`) exist in mockups only; operational templates do **not** need them.

### `import.html` (Phase B)

- Bulk bar: add `sticky-top` class with `style="top:76px"` so it stays visible while scrolling a long catalog table.
- Import Selected button: add `<i class="fa-solid fa-download me-1"></i>` icon (matches mockup PROJECTS-IMPORT-1).

### `list.html` (Phase C)

- Add **Playbook** column after DataSource — show `"—"` until Playbook FK exists.
- Add **Last sync** column — render `project.last_sync_at|default:"—"`.
- Replace the single "Open" button with a **View / Edit / Archive icon btn-group** (`btn-group btn-group-sm`) matching mockup `data-testid` keys:
  - `data-testid="projects-row-view-{pk}"` → eye icon → `projects-detail`
  - `data-testid="projects-row-edit-{pk}"` → pen icon → `projects-edit`
  - `data-testid="projects-row-archive-{pk}"` → box-archive icon (warning) → `projects-archive`
- Import Projects header button: change to `btn-primary` with `<i class="fa-solid fa-download me-1"></i>` icon, `data-testid="projects-import-btn"`.

### `detail.html` (Phase F)

- Replace the flat `<dl>` list with a **two-column card layout** (mockup `PROJECTS-VIEW_PROJECT-1`):
  - **Identity card** — `source_path`, `created_at` labelled "Imported on".
  - **Playbook card** — placeholder "No playbook assigned" until Playbook MVP; `data-testid="projects-view-playbook-section"`.
  - **Sync card** — `last_sync_at` (last sync) + next scheduled stub (show schedule label or "—").
  - **Recent activity card** — V0.1 placeholder `data-testid="projects-placeholder-activity"`.
- `hg-page-header` section: `sync_state` badge + project name + `datasource.name · source_path` subtitle.
- Action buttons rendered **above** the cards (not in a sidebar card), matching mockup button order: Edit, Sync Now, Archive, Open SitReps (disabled).

### `edit.html` (Phase H)

- Wrap form in a card (`col-lg-8 col-xl-6`) — matching datasource and mockup pattern.
- Sync schedule options must be **Hourly / Every 6h / Daily** (mockup PROJECTS-EDIT_PROJECT-1). Remove `MANUAL = "manual"` and add `EVERY_6H = "every_6h"` to `SyncSchedule` TextChoices. Requires **migration `0005`**.

### `archive.html` (Phase G)

- Modal body copy must match the **feature file exactly** (ARCHIVE-02):
  > "Syncs will stop. Ingested history is retained and can be browsed. Project will not appear on the Projects Dashboard."
  Current copy in `archive.html` diverges from this and must be updated.

---

## Context Map

| File | Note |
|------|------|
| [`ui/services/projects_service.py`](../../ui/services/projects_service.py) | Catalog snapshot, import persistence, sync enqueue, configuration updates |
| [`ui/views/projects.py`](../../ui/views/projects.py) | List filters, import flow, messages, connected datasource filter |
| [`ingestion/integrations/gitlab_client.py`](../../ingestion/integrations/gitlab_client.py) | `list_visible_projects`, token auth |
| [`ingestion/models/__init__.py`](../../ingestion/models/__init__.py) | `Project` fields and constraints |
| [`tests/integration/test_projects_import.py`](../../tests/integration/test_projects_import.py) | Import + catalog errors + CSRF |

---

## Do Not Do

- **Do NOT** expose a public REST API for these flows — SAO §2 (*Django views + HTMX only for v1 UI*).
- **Do NOT** put GitLab parsing, slug collision rules, or “already imported” logic in views — keep in [`ProjectsService`](../../ui/services/projects_service.py) (SAO §1: UI consumes services; [`user_journey.md`](../features/user_journey.md) import-only lifecycle).
- **Do NOT** add a new Django app for Act 2 phases A–G; new models stay under **`ingestion`** (existing `Project`) unless you explicitly greenfield **Playbooks** (separate decision).
- **Do NOT** call live GitLab in CI/tests — SAO §5 allows **`urllib` patch** / stubbing for GitLab (align with existing datasource tests).
- **Do NOT** edit [`ui/templates/ui/mockups/`](../../ui/templates/ui/mockups/) or [`ui/views/mockups/`](../../ui/views/mockups/) for operational behavior — mockups stay reference-only.

---

## SAO.md Sections That Apply

- **§1 Application Blocks** — `ui/` views/templates only; domain in services + ORM.
- **§2 Integration & API Design** — No REST for UI; GitLab via **`ingestion.integrations`** client (urllib pattern).
- **§4 Data Architecture** — Migrations for `Project` extensions; expand-contract as needed.
- **§5 Test Strategy** — `pytest` + `pytest-django`; stub GitLab HTTP per SAO; integration tests for views.
- **§7 Error Handling & Resilience** — Surface API/network failures on import catalog refresh (**PROJECTS-IMPORT-15**); avoid silent empty catalogs when GitLab errors.

---

## Phased implementation (atomic order)

### Phase A — Real GitLab catalog + correct persistence

1. **`GitlabClient`**: `list_visible_projects()` with pagination (`X-Next-Page` / short page, `max_pages` cap documented in client docstring).
2. **`ProjectsService.load_remote_projects_snapshot`**: GitLab rows → `entries` with `key` = `str(gitlab_id)`.
3. **`persist_imported_project_selection`**: map keys via catalog; slug from `path_with_namespace`; enqueue placeholder sync.
4. **IMPORT-01**: datasource dropdown = connected + GitLab only (`computed_status == CONNECTED`).
5. **IMPORT-15 / IMPORT-16**: `catalog.error` + empty connected messaging in template.

**Pytest checkpoint:** `pytest tests/integration/test_projects_import.py tests/unit/test_gitlab_client.py -x`

### Phase B — Import UI parity

- Table, bulk bar, find, already-imported, redirect `?imported=1` + success message.
- Apply `hg-page-header` section + sticky bulk bar + icon on Import Selected (see **Mockup-to-operational transfer → `import.html`**).

**Pytest checkpoint:** `pytest tests/integration/test_projects_import.py -x`

### Phase C — Projects list + find

- Table, columns, GET filters `?datasource=&status=&playbook=`, empty state CTA.
- Columns must include **Playbook** and **Last sync**; row actions must be the View/Edit/Archive btn-group; Import btn is `btn-primary` (see **Mockup-to-operational transfer → `list.html`**).

**Pytest checkpoint:** `pytest tests/integration/test_projects_list_find.py -x`

### Phase D — Model: sync lifecycle + import metadata

- Fields + migration; import sets `imported_by`; factories if needed.

**Pytest checkpoint:** `pytest tests/ -x` (includes model usage across integration tests)

### Phase E — Celery: V0.1 initial sync placeholder

- `ingestion.tasks.sync_project_placeholder`; archive excluded in task body.

**Pytest checkpoint:** `pytest tests/integration/test_projects_import.py tests/integration/test_projects_view_vitals_tab.py -x`

### Phase F — Project detail view

- Detail fields, Sync now, deferred SitRep control (`aria-disabled`).
- Template must use 4-card layout (Identity / Playbook / Sync / Recent activity) and `hg-page-header` (see **Mockup-to-operational transfer → `detail.html`**).

**Pytest checkpoint:** `pytest tests/integration/test_projects_view_vitals_tab.py tests/integration/test_projects_view_increments_tab.py -x`

### Phase G — Archive flow polish

- Modal-style confirmation page; **ARCHIVE-05** skipped in tests until dashboard exists.
- Modal body copy must match ARCHIVE-02 scenario text exactly (see **Mockup-to-operational transfer → `archive.html`**).

**Pytest checkpoint:** `pytest tests/integration/test_projects_archive.py -x`

### Phase H — Edit form (partial)

- Display name + sync schedule; defer **PROJECTS-EDIT-05..08**.
- Sync schedule options: `Hourly / Every 6h / Daily` — add `EVERY_6H` choice, drop `MANUAL`, add migration `0005`; card-wrap the form (see **Mockup-to-operational transfer → `edit.html`**).

**Pytest checkpoint:** `pytest tests/integration/test_projects_edit.py -x`

---

## Deferred scenarios (explicit)

| Scenario IDs | Blocked until |
|--------------|----------------|
| **PROJECTS-EDIT-05..08** | Playbook MVP |
| **PROJECTS-VIEW_PROJECT-12** | `SITREP-LIST+FIND-1` |
| **PROJECTS-ARCHIVE_PROJECT-05** | `DASHBOARD-PROJECTS-1` |
| **PROJECTS-LIST+FIND-14** (full playbook filter) | Playbook MVP |

---

## Testing inventory

- **Unit**: `GitlabClient` list parsing; pagination.
- **Integration**: import, list filters, view, archive, edit, datasource tests (patch `ingestion.integrations.gitlab_client.urlopen`).
- **Regression**: `pytest tests/`

---

## GitLab issues (BPE-01 — create one issue per phase)

Paste the **Title** and **Description** into your GitLab project. Suggested labels: `act2-projects`, `planning` (and add `backend` / `frontend` when execution starts).

Adjust milestone and assignee per your process.

---

### Issue draft — Phase A

**Title:** `Act 2 Projects — Phase A: GitLab catalog + import persistence`

**Description:**

```markdown
## Goal
Real GitLab project list (`GET /api/v4/projects`, `membership=true`, paginated), `ProjectsService` catalog + persistence keyed by GitLab project id; import dropdown limited to **connected** GitLab datasources; surface catalog API errors (IMPORT-15/16 patterns).

## Context Map
| Area | Location |
|------|----------|
| Service | `ui/services/projects_service.py` |
| Views | `ui/views/projects.py` |
| GitLab HTTP | `ingestion/integrations/gitlab_client.py` |
| Tests | `tests/integration/test_projects_import.py`, `tests/unit/test_gitlab_client.py` |

## Do Not Do
- No public REST API for these UI flows (SAO §2).
- No GitLab parsing / slug / “already imported” logic in views — keep in `ProjectsService`.
- No live GitLab in CI — stub `ingestion.integrations.gitlab_client.urlopen` in tests.

## SAO sections that apply
§1 UI vs domain, §2 integration design, §4 migrations as needed, §5 pytest + stubs, §7 surface API failures on catalog refresh.

## Pytest checkpoint
`pytest tests/integration/test_projects_import.py tests/unit/test_gitlab_client.py -x`
```

---

### Issue draft — Phase B

**Title:** `Act 2 Projects — Phase B: Import UI parity`

**Description:**

```markdown
## Goal
Import screen: table, bulk selection bar, client-side “find project”, already-imported indicators; post-import redirect with query flag + banner/message (IMPORT-07).

## Context Map
- Template: `ui/templates/ui/projects/import.html`
- JS: `static/js/projects_import.js` (if used)
- Feature reference: `docs/features/act-2-projects/projects-import.feature`

## Do Not Do
- Mockups under `ui/templates/ui/mockups/` are reference-only.
- Domain rules stay in `ProjectsService`, not templates.

## SAO sections that apply
§1, §2, §5 (integration tests + stable `data-testid`).

## Pytest checkpoint
`pytest tests/integration/test_projects_import.py -x`
```

---

### Issue draft — Phase C

**Title:** `Act 2 Projects — Phase C: Projects list + find`

**Description:**

```markdown
## Goal
Projects list table with sync/row status columns; GET filters `?datasource=&status=&playbook=` (playbook stub: `playbook_slug` contains); empty state with CTA.

## Context Map
- `ui/templates/ui/projects/list.html`, `ui/views/projects.py`
- Tests: `tests/integration/test_projects_list_find.py`

## Do Not Do
- Full playbook FK filter deferred until Playbook MVP (LIST+FIND-14).

## SAO sections that apply
§1, §4, §5.

## Pytest checkpoint
`pytest tests/integration/test_projects_list_find.py -x`
```

---

### Issue draft — Phase D

**Title:** `Act 2 Projects — Phase D: Project model — sync + import metadata`

**Description:**

```markdown
## Goal
Extend `Project`: `sync_state`, `source_url`, `imported_by`, `gitlab_project_id`, constraints as needed; migrations under `ingestion/migrations/`; wire import to set `imported_by` + initial sync state.

## Context Map
- `ingestion/models/__init__.py`, factories `tests/factories.py`

## Do Not Do
- New Django app for this; keep models in `ingestion`.

## SAO sections that apply
§4 data architecture, §5 unit + integration coverage.

## Pytest checkpoint
`pytest tests/ -x` (or narrow to projects + ingestion tests once stable)
```

---

### Issue draft — Phase E

**Title:** `Act 2 Projects — Phase E: Celery initial sync placeholder`

**Description:**

```markdown
## Goal
Celery task (e.g. `ingestion.tasks`) that completes “initial sync” placeholder: set `sync_state=active`, update timestamps as specified; enqueue from import and sync-now; exclude archived projects from background transition where applicable (ARCHIVE-04 direction).

## Context Map
- `ingestion/tasks.py`, `huginn/celery.py`, `ui/services/projects_service.py`

## Do Not Do
- No live GitLab pull required for V0.1 unless product expands scope.

## SAO sections that apply
§5 eager tests in `huginn.settings.test`.

## Pytest checkpoint
`pytest tests/integration/test_projects_import.py tests/integration/test_projects_view_vitals_tab.py -x`
```

---

### Issue draft — Phase F

**Title:** `Act 2 Projects — Phase F: Project detail + sync UX`

**Description:**

```markdown
## Goal
Detail template with datasource, path, URLs, sync state, schedule, importer; Sync Now dispatches task; **defer** SitRep link until `SITREP-LIST+FIND-1` (VIEW-12).

## Context Map
- `ui/templates/ui/projects/detail.html`, `ui/views/projects.py`

## Do Not Do
- Do not claim SitRep navigation works until route exists — use disabled control + clear `data-testid`.

## SAO sections that apply
§1, §5.

## Pytest checkpoint
`pytest tests/integration/test_projects_view_vitals_tab.py tests/integration/test_projects_view_increments_tab.py -x`
```

---

### Issue draft — Phase G

**Title:** `Act 2 Projects — Phase G: Archive flow polish`

**Description:**

```markdown
## Goal
Archive confirmation aligned to feature (modal-style page, focus, copy); **defer** dashboard removal assertion (ARCHIVE-05) until `DASHBOARD-PROJECTS-1`.

## Context Map
- `ui/templates/ui/projects/archive.html`, `tests/integration/test_projects_archive.py`

## Do Not Do
- No dashboard assertions until dashboard feature exists.

## SAO sections that apply
§1, §5, §7 user-visible consequences copy.

## Pytest checkpoint
`pytest tests/integration/test_projects_archive.py -x`
```

---

### Issue draft — Phase H

**Title:** `Act 2 Projects — Phase H: Edit display name + sync schedule (partial)`

**Description:**

```markdown
## Goal
Edit display name + sync schedule; **defer** PROJECTS-EDIT-05..08 until Playbook domain exists.

## Context Map
- `ui/templates/ui/projects/edit.html`, `ui/views/projects.py`, `ui/services/projects_service.py`

## Do Not Do
- No Playbook assignment UI in this phase.

## SAO sections that apply
§1, §5.

## Pytest checkpoint
`pytest tests/integration/test_projects_edit.py -x`
```

---

## GitLab automation note

The Cursor GitLab MCP in this workspace currently exposes authentication only (`mcp_auth`); **issue creation must be done in GitLab UI or API** using the drafts above. If you enable a broader GitLab MCP toolset later, re-use these bodies for bulk create.

---

## Implementation record

Optional sync with the repo (may pre-date strict BPE-01 sign-off in your process):

- **2026-05-06**: Substantial Act 2 projects code landed in tree (GitLab catalog, import UI, list/detail/edit/archive, model migration `0004`, Celery placeholder, tests). Treat as **execution progress**; GitLab issues above still anchor phase boundaries for review and traceability.

---

## Rule reminders during implementation

- Re-read **SAO** §§1–2, 4–5, 7 before merging each phase.
- Follow repo **Ruff** / **pre-commit**; keep `data-testid` conventions consistent with Act 1 datasources work.
- Do not invent FOB screen IDs (see `.cursor/rules/no-fob-screen-ids.mdc`).
