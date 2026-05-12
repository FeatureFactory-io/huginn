# Iteration orient summary — 2026-05-05 (ITER-2026-W19)

## Input Scope

**Iteration goal**

> Ship Acts 0–2 (inclusive) on real Django code: **AUTH-LOGIN-1**, full **DataSources** management surface (list/create/view/edit/delete), and **Projects** (list, import, view, edit, archive) as **skeleton-first** vertical slices, each with BPE-01 plan + checkpoint test, ready for **dark-factory / Lead Engineer** execution from a GitLab milestone manifest.

**Scenarios (one feature file each — 11 total)**

| F# | Act | Screen ID | Feature spec |
| --- | --- | --- | --- |
| F01 | 0 | `AUTH-LOGIN-1` | `docs/features/act-0-auth/auth-login.feature` |
| F02 | 1 | `DATASOURCES-LIST+FIND-1` | `docs/features/act-1-datasources/datasources-list-find.feature` |
| F03 | 1 | `DATASOURCES-CREATE_DATASOURCE-1` | `docs/features/act-1-datasources/datasources-create.feature` |
| F04 | 1 | `DATASOURCES-VIEW_DATASOURCE-1` | `docs/features/act-1-datasources/datasources-view.feature` |
| F05 | 1 | `DATASOURCES-EDIT_DATASOURCE-1` | `docs/features/act-1-datasources/datasources-edit.feature` |
| F06 | 1 | `DATASOURCES-DELETE_DATASOURCE-1` | `docs/features/act-1-datasources/datasources-delete.feature` |
| F07 | 2 | `PROJECTS-LIST+FIND-1` | `docs/features/act-2-projects/projects-list-find.feature` |
| F08 | 2 | `PROJECTS-IMPORT-1` | `docs/features/act-2-projects/projects-import.feature` |
| F09 | 2 | `PROJECTS-VIEW_PROJECT-1` | `docs/features/act-2-projects/projects-view.feature` |
| F10 | 2 | `PROJECTS-EDIT_PROJECT-1` | `docs/features/act-2-projects/projects-edit.feature` |
| F11 | 2 | `PROJECTS-ARCHIVE_PROJECT-1` | `docs/features/act-2-projects/projects-archive.feature` |

**Deferred / scope cuts for this skeleton iteration** (scenarios remain in `.feature`; a later factory pass may annotate `(deferred)`)

- Heavy GitLab failure-path UX (401/404/network live handling) → stub messaging only until real client hardened.
- Project detail **recent activity** populated rows → empty state unless pipeline exists.
- Token expiry **live** transitions → static badges acceptable for skeleton.

## Velocity Trend

First iteration (`entries:` empty in `docs/lessons_learned/log.yaml`) — no ratio trend.

## Dominant Drift

n/a — no historical entries.

## Footprint Accuracy

n/a — baseline.

## Scope Validation

- **F03 / F08** share a thin **GitLab client** abstraction — sequence footprint so import (F08) commits after client exists (F03).
- **Model landings**: **`DataSource`** with F02 list; **`Project`** introduced when first needed for projects list (**F07**).
- Parallel execution during implementation expect **overlap within Act 1 and Act 2 clusters** until conflict map assigns groups.

## Watch For

- **Footprint creep** across F02–F06 and F07–F11 — keep each **`chore(skeleton): F{NN}`** commit bounded to that feature only.
- **GitLab vs GitHub** in reference docs — milestone/issues use **`glab`** and **GitLab IID** (`gitlab_issue` in manifest YAML).
