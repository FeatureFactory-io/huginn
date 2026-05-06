# F12 — Sync specification (BPE Plan Feature)

**gitlab_iid:** 25
**Depends on:** none

## Context Map

| File | Lines | Note |
|------|-------|------|
| [docs/features/act-2-projects/projects-view-increments-tab.feature](../features/act-2-projects/projects-view-increments-tab.feature) | full | Increments tab Gherkin — drives F18 tests |
| [docs/features/act-2-projects/projects-sync-engine.feature](../features/act-2-projects/projects-sync-engine.feature) | full | Sync engine Gherkin — drives F14–F16 tests |
| [docs/architecture/SAO.md](../architecture/SAO.md) | §1, §4, §7 | Ingestion sync engine + models + failure surfacing |
| [docs/features/user_journey.md](../features/user_journey.md) | Act 2 PROJECTS-VIEW | Tabbed view narrative |

## Do Not Do

- Do NOT implement code in F12 — documentation and scenario files only
- Do NOT add `FOB-*` screen IDs — use Huginn `PROJECTS-*` scheme
- Do NOT scope Playbooks, SitReps, or Master Variable computation in this phase

## SAO.md Sections That Apply

- §1 Application Blocks — ingestion ownership; sync engine sub-section
- §3 Code Organization — where `domain/`, `adapters/`, `services/` live
- §4 Data Architecture — Contributor, Increment, IngestionRun sketches
- §7 Error Handling & Resilience — idempotency, sync failure surfacing

## Implementation Steps

1. Add `projects-view-increments-tab.feature` and `projects-sync-engine.feature`.
2. Update `projects-view.feature`: Vitals tab Background; replace PROJECTS-VIEW_PROJECT-08.
3. Extend SAO.md §1 (sync engine), §4 (models), §7 (sync failures, concurrency).
4. Update `user_journey.md` Act 2 PROJECTS-VIEW_PROJECT-1 for tabs + deep-link.
5. Add `INCREMENTS_INGESTION_FULL_PLAN.md`, F13–F18 plan stubs, `GITLAB_ISSUES_INCREMENTS_INGESTION.md`, `.gitlab-issue-bodies/*.md`.
6. Branch `feature/F12-sync-specification-huginn-{IID}`; commit `docs(...): ... (huginn#{IID})`; MR.

## Tests

None (docs-only MR).

## Acceptance Criteria

- [ ] All feature files parse valid Gherkin
- [ ] SAO.md and user_journey.md consistent with scenarios
- [ ] GitLab issue bodies ready for `glab issue create --description-file`
