# BPE-01 Plan — Act 6 (FRAGO) + Act 12 (Situational Awareness)

Companion to FeatureFactory **BPE-reference-01-Plan_Feature**. Sources:

- `docs/features/act-6-fragos/*.feature`
- `docs/features/act-12-situational-awareness/*.feature`
- `docs/features/user_journey.md` (FRAGO + Act 12 sections)
- `docs/architecture/SAO.md` (`sitrep/` owns FRAGO store + SA snapshots)

## Shared orientation — reuse HTML mockups

Operational UI should **mirror layout, labels, and `data-testid` patterns** from:

| Area | Prototype templates | Operational shells (parity copies — extend here, **never edit mocks**) |
|------|---------------------|---------------------------------------------------------------------------|
| FRAGO | `ui/templates/ui/mockups/fragos/` (`list`, `create`, `view`, `edit`, `revoke`) | `ui/templates/ui/fragos/` (+ routes `fragos-*` in `ui/urls.py`, views `ui/views/fragos.py`) |
| SA | `ui/templates/ui/mockups/sitawareness/` (`view`, `edit`) | `ui/templates/ui/situational_awareness/` (+ `sitawareness-*`, `ui/views/situational_awareness.py`) |
| Mock URL wiring | — | `ui/urls_mockups.py` (`mockup-fragos-*`, `mockup-sitawareness-*`) |

Production URLs live under **non-mock** `ui/` routes and `huginn.urls` — copy patterns from Playbooks delivery (`ui/views/playbooks.py`, `ui/templates/ui/playbooks/`, tests under `tests/`).

## Context Map (shared)

| File | Lines | Note |
|------|-------|------|
| `docs/architecture/SAO.md` | §1 Application Blocks | `sitrep/` owns SitRep generation, **FRAGO store**, **SA snapshots** — put new domain models here, not in `playbooks/`. |
| `playbooks/models.py` | 31–55 | Follow **version snapshot** pattern (`PlaybookVersion`: immutable row + `version_number` + `created_by`) for SA versions. |
| `playbooks/markdown_utils.py` | 8–17 | Reuse `workflow_md_to_html()` for **read-only** FRAGO body + SA rendered sections. |
| `ingestion/models/__init__.py` | `Project` | FRAGO and SA are **per-Project** — FK targets live here. |
| `ui/views/playbooks.py` + `ui/templates/ui/playbooks/` | — | Reference CRUDLF + list/detail patterns for production (auth, messages, tests). |

## Do Not Do

- Do NOT add FRAGO or SA **persistent** models under `playbooks/` — SAO places them under **`sitrep/`**.
- Do NOT duplicate markdown rendering logic — use **`playbooks.markdown_utils.workflow_md_to_html`** (or thin wrapper).
- Do NOT put domain rules only in templates — validate **revoked / enabled / effective window** in services or model clean/save as appropriate.
- Do NOT wire SitRep **generation** consumption of FRAGO/SA in these issues unless explicitly in scope (may be a later milestone); focus on **authoring CRUDLF + VIEW/EDIT** per feature files.
- Do NOT reintroduce **day-of-week** or **Sprint/Milestone** scope UI unless product reverses decision — mocks and journey now use **effective from/to dates only**.

## SAO.md Sections That Apply

- **§1 Application Blocks** — Django apps boundaries; `sitrep/` responsibility for FRAGO + SA persistence.
- **§2 Integration & API Design** — Web UI via Django views + templates (+ HTMX where listed elsewhere).

## Issue breakdown (GitLab)

Tracked under GitLab milestone [**Playbooks + FRAGOs + Awareness**](https://gitlab.com/dp2580/huginn/-/milestones/6) (`7419452`). Milestone description source: `docs/plans/iterations/gitlab-milestone-playbooks-fragos-awareness-description.txt`.

| IID | Title | Scope |
|-----|-------|--------|
| [#42](https://gitlab.com/dp2580/huginn/-/work_items/42) | ACT6-FRAGO-01 — sitrep `Frago` model + admin + unit tests | Schema, migrations, admin |
| [#43](https://gitlab.com/dp2580/huginn/-/work_items/43) | ACT6-FRAGO-02 — FRAGO LIST+FIND production UI | List filters, table, project scope |
| [#44](https://gitlab.com/dp2580/huginn/-/work_items/44) | ACT6-FRAGO-03 — FRAGO CREATE + EDIT | Forms, validation, effective dates |
| [#45](https://gitlab.com/dp2580/huginn/-/work_items/45) | ACT6-FRAGO-04 — FRAGO VIEW + REVOKE + enable semantics | Detail, revoke modal flow, read-only toggle |
| [#46](https://gitlab.com/dp2580/huginn/-/work_items/46) | ACT12-SA-01 — sitrep SA + version models + admin + tests | One SA per project, version rows |
| [#47](https://gitlab.com/dp2580/huginn/-/work_items/47) | ACT12-SA-02 — SA VIEW (Document \| Versions tabs) | Read-only tabs parity mock |
| [#48](https://gitlab.com/dp2580/huginn/-/work_items/48) | ACT12-SA-03 — SA EDIT (Save Version, change summary) | Edit tab + version head |

Issue bodies: `docs/plans/.gitlab-issue-bodies/FG01.md` … `FG04.md`, `SA01.md` … `SA03.md`.
