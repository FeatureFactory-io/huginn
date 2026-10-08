# Act 3 — Playbooks (BPE-01 Plan Feature)

**Activity:** BPE-01-Plan_Feature
**Specs:** `docs/features/act-3-playbooks/*.feature`, `docs/features/user_journey.md` (Act 3)
**Reference UI:** `ui/templates/ui/mockups/playbooks/` + `ui/views/mockups/playbooks.py` (reference-only; operational UI goes under `ui/templates/ui/playbooks/` and `ui/views/`).

## Milestone (GitLab)

**Playbooks et al** — groups PB01–PB08 below.

---

## Scope overview

Deliver **CRUDLF** for **versioned Playbooks** (metadata + Workflow markdown + ordered Variables + ordered Tables), **seed FeatureFactory Playbook**, **catalog drift validation** (diagnostic), **Project assignment** (FK / pin semantics replacing string `playbook_slug` where applicable). Work is sliced so each GitLab issue merges independently to `main` behind passing pytest checkpoints.

---

## Mockup → operational transfer

Operational templates **must not** edit mockups. Copy layout and `data-testid` naming from mockups where scenarios require discoverability.

| Mockup path | Operational target |
|-------------|-------------------|
| `ui/templates/ui/mockups/playbooks/list.html` | `ui/templates/ui/playbooks/list.html` |
| `ui/templates/ui/mockups/playbooks/create.html`, `_playbook_editor_body.html` | `ui/templates/ui/playbooks/create.html`, shared `_editor_body.html` |
| `ui/templates/ui/mockups/playbooks/edit.html` | `ui/templates/ui/playbooks/edit.html` |
| `ui/templates/ui/mockups/playbooks/view.html` | `ui/templates/ui/playbooks/view.html` |
| `ui/templates/ui/mockups/playbooks/delete.html` | `ui/templates/ui/playbooks/delete.html` |

Reuse patterns from Act 2: `hg-page-header`, LIST+FIND table + row overflow menu (IA §5.2), detail header toolbar (IA §3.4), Workflow markdown preview (already wired in mock via `markdown`).

---

## Context Map

| File | Lines | Note |
|------|-------|------|
| `ingestion/models/__init__.py` | `Project` | Today: `playbook_slug`; PB08 adds real FK / tracking fields — follow existing constraints style |
| `ui/views/projects.py` | 49–79 | List filters — extend playbook filter when FK exists |
| `ui/views/datasources.py` | (list/detail patterns) | Operational CBV + `login_required` pattern to mirror |
| `ui/templates/ui/projects/list.html` | — | Row overflow + `hg-list-name-link` reference |
| `tests/integration/test_projects_list_find.py` | — | Integration style: `client`, `pytest.mark.django_db`, `reverse()` |

---

## Do Not Do

- **Do NOT** add a public REST API for Playbooks UI flows — SAO §2 (*Django views + HTMX for v1 UI*).
- **Do NOT** put versioning rules or catalog validation in templates — services + forms (`ui/services/playbooks/` as needed).
- **Do NOT** modify `ui/templates/ui/mockups/` or `ui/views/mockups/` for operational behaviour — mockups stay reference-only.
- **Do NOT** implement **Import from Mimir** beyond disabled stub / tooltip — out of MVP (`playbooks-create.feature` PLAYBOOKS-CREATE_PLAYBOOK-07).
- **Do NOT** claim AI-driven **Validate Playbook** — drift scan vs in-code entity/slicer catalog only (`playbooks-view.feature`).
- **Do NOT** add Celery/async to CRUD paths unless SAO explicitly requires it for Playbooks (it does not for MVP).

---

## SAO.md Sections That Apply

- **§1 Application Blocks** — New domain app `playbooks/` acceptable for bounded context; `ui/` owns HTTP + templates; thin views.
- **§2 Integration & API Design** — No REST for UI consumers.
- **§3 Code Organization** — kebab-case templates; snake_case Python; `data-testid` on interactive controls.
- **§4 Data Architecture** — Django migrations; expand-contract if changing `Project` playbook linkage.
- **§5 Test Strategy** — `pytest` + `pytest-django`; integration tests without mocking core ORM; Makefile `make test`.

---

## Phased issues (merge order)

| ID | Focus | Checkpoint (minimal) |
|----|--------|----------------------|
| **PB01** | `playbooks` app — `Playbook`, `PlaybookVersion`, `PlaybookVariable`, `PlaybookTable`, admin, factories | `pytest tests/unit/test_playbook_models.py -x -q` |
| **PB02** | Data migration or seed command: FeatureFactory Playbook v1 (+ starter rows matching seed doc / mock) | `pytest tests/…/test_playbooks_seed.py -x -q` (added with PB02) |
| **PB03** | `PLAYBOOKS-LIST+FIND-1` operational — `/playbooks/` URLs, list + filters + row menu | `pytest tests/integration/test_playbooks_list_find.py -x -q` |
| **PB04** | `PLAYBOOKS-CREATE_PLAYBOOK-1` — GET/POST v1, clone-from-seed query | `pytest tests/integration/test_playbooks_create.py -x -q` |
| **PB05** | `PLAYBOOKS-VIEW_PLAYBOOK-1` — tabs, markdown workflow, Validate drift panel | `pytest tests/integration/test_playbooks_view.py -x -q` |
| **PB06** | `PLAYBOOKS-EDIT_PLAYBOOK-1` — immutable versions + change summary | `pytest tests/integration/test_playbooks_edit.py -x -q` |
| **PB07** | `PLAYBOOKS-DELETE_PLAYBOOK-1` — guard when projects attached | `pytest tests/integration/test_playbooks_delete.py -x -q` |
| **PB08** | `Project` assignment — FK + pin/auto-track UX in edit/detail/list | `pytest tests/integration/test_projects_edit.py tests/integration/test_projects_list_find.py -x -q` (+ playbook-specific additions) |

Each issue body in GitLab repeats **Context Map**, **Do Not Do**, **SAO Sections**, and a **scenario-local implementation plan** inline (BPE-01 Step 10).

---

## Clarifications (batch)

1. **PB02 seed source of truth:** align starter Variables/Tables with `docs/features/user_journey.md` seed bullet list + mock `playbooks.py` fixture text unless product revises.
2. **Slicer registry:** PB04/PB05 must reuse or introduce single module enumerating valid `(entity, slicer)` pairs for authoring validation (increment-only MVP is acceptable if scenarios already assume it).
3. **Navigation:** add authenticated nav entry **Playbooks** pointing at operational list (mirror mock `base_mockups.html`), without breaking Act 0 login flows.

---

## Success criteria (Act 3 exit)

- All scenarios in `docs/features/act-3-playbooks/*.feature` mapped to passing integration tests or explicitly deferred with ADR/issue link.
- `pytest tests/ -x` passes on `main` after each PB merge.
- No operational dependency on `/mockups/playbooks/` URLs.

---

## Artifacts

- This plan: `docs/plans/ACT3_PLAYBOOKS_IMPLEMENTATION_PLAN.md`
- Per-issue bodies: `docs/plans/GITLAB_ISSUES_ACT3_PLAYBOOKS.md` + `docs/plans/.gitlab-issue-bodies/PB*.md`
