# Orient Summary — 2026-05-07 (Playbooks + FRAGOs + Awareness)

## Input Scope

**Iteration goal**

> Ship **Act 6 — FRAGO** and **Act 12 — Situational Awareness** as production Django slices behind pytest checkpoints, mirroring `ui/templates/ui/mockups/fragos/` and `ui/templates/ui/mockups/sitawareness/`, with domain persistence under **`sitrep/`** per `docs/architecture/SAO.md`. Work rolls up to GitLab milestone **[Playbooks + FRAGOs + Awareness](https://gitlab.com/dp2580/huginn/-/milestones/6)** alongside existing Playbooks issues PB01–PB08.

**Doctrine milestone (GitLab)**

- **Title:** Playbooks + FRAGOs + Awareness
- **ID:** `7419452` · **IID:** 6
- **Description source (repo):** `docs/plans/iterations/gitlab-milestone-playbooks-fragos-awareness-description.txt`

**Scenarios (GitLab IID — Act 6 / 12 only)**

| Code | IID | Title |
| --- | --- | --- |
| FG01 | [#42](https://gitlab.com/dp2580/huginn/-/work_items/42) | ACT6-FRAGO-01: sitrep Frago model + admin + unit tests |
| FG02 | [#43](https://gitlab.com/dp2580/huginn/-/work_items/43) | ACT6-FRAGO-02: FRAGO LIST+FIND production UI |
| FG03 | [#44](https://gitlab.com/dp2580/huginn/-/work_items/44) | ACT6-FRAGO-03: FRAGO CREATE + EDIT |
| FG04 | [#45](https://gitlab.com/dp2580/huginn/-/work_items/45) | ACT6-FRAGO-04: FRAGO VIEW + REVOKE + enable/disable |
| SA01 | [#46](https://gitlab.com/dp2580/huginn/-/work_items/46) | ACT12-SA-01: sitrep SA + version models + admin + tests |
| SA02 | [#47](https://gitlab.com/dp2580/huginn/-/work_items/47) | ACT12-SA-02: SA VIEW (Document \| Versions tabs) |
| SA03 | [#48](https://gitlab.com/dp2580/huginn/-/work_items/48) | ACT12-SA-03: SA EDIT (Save Version) |

**Plans & bodies**

- Shared BPE map: `docs/plans/ACT6_ACT12_BPE01_IMPLEMENTATION_PLAN.md`
- Issue descriptions: `docs/plans/.gitlab-issue-bodies/FG01.md` … `FG04.md`, `SA01.md` … `SA03.md`
- Execution manifest (checkpoint + deps stub): `docs/plans/iterations/ITER-20260507-playbooks-fragos-awareness.yaml`

## Velocity Trend

Only **one** prior entry in `docs/lessons_learned/log.yaml` (ITER-2026-W19). Treat velocity trend as **baseline / insufficient history** (no multi-point ratio slope).

## Dominant Drift

Latest logged signal: **checkpoint wording / YAML drift** (`dominant_drift` on 2026-05-05 entry). Watch scenario SCENARIO blocks in GitLab bodies vs repo copies.

## Footprint Accuracy

Latest **`footprint_accuracy`**: **0.92** — treat as **stable** until this iteration closes with a new log entry.

## Scope Validation

- **FG01** then **SA01** likely share **`sitrep/` package surface** (models/admin/migrations). Prefer **merge FG01 before SA01** or split modules early to reduce churn (see manifest conflict map).
- **FG02–FG04** share operational FRAGO UI footprint (`ui/urls.py`, views, templates). Prefer **FG02 → FG03 → FG04** ordering unless PIT-02 footprints prove disjoint files.
- **PB08** (project playbook FK) intersects FG03 variable picklists — confirm **`assigned_playbook` / active version** semantics before FRAGO “Affected Variable” QA depth.

## Watch For

- **Footprint creep** outside issue bodies + SAO do-not-do lists (`footprint_violation` in PIT drift thresholds).
- **Milestone naming drift**: canonical title on GitLab is **Playbooks + FRAGOs + Awareness**; local docs must not resurrect **Playbooks et al** as the milestone label.
