---
id: T-68-release
role: release-engineer
depends_on: [T-62-impl, T-63-impl]
attempt: 1
branch: release/2026.05.12
---

# Task T-68-release — AI→SitRep milestone integration + staging deploy

## Objective
Merge the full AI→SitRep feature chain into `main`, tag `v2026.05.12`,
push `release/2026.05.12`, and let CI deploy to staging.

## System context
`docs/architecture/SAO.md` §9–§10 — staging vs prod, release branch gate,
`make verify-release`, `make staging`, `make swap`.

## Step-by-step

1. Fetch all remote branches:
   ```bash
   git fetch --all
   ```

2. Merge the **stacked** UI MRs first (order matters), then the umbrella MR into `main`:
   ```bash
   # T-63: feature/sitrep-view-impl → feature/sitrep-list-impl
   glab mr merge 15 --squash=false --remove-source-branch=false
   # T-62: feature/sitrep-list-impl → feature/sitrep-generate-impl
   glab mr merge 14 --squash=false --remove-source-branch=false
   # Whole stack: feature/sitrep-generate-impl → main (LE pre-opened as !16)
   glab mr merge 16 --squash=false --remove-source-branch=false
   ```
   If GitLab reports conflicts after !15, refresh/rebase the source branch of !14 per GitLab UI, then continue.
   Find other MRs with: `glab mr list --all`

3. Verify all tests pass on `main`:
   ```bash
   git checkout main && git pull
   source .venv/bin/activate && pytest tests/ -x -q
   ```

4. Create and push the release tag:
   ```bash
   git tag 2026.05.12
   git push origin 2026.05.12
   ```

5. Create and push the release branch at that tag:
   ```bash
   git checkout -b release/2026.05.12 2026.05.12
   git push origin release/2026.05.12
   ```
   This triggers the GitLab CI pipeline (validate → lint → test → build → deploy_staging).

6. Monitor the pipeline:
   ```bash
   glab ci status
   ```

## Acceptance criteria
- `git tag | grep v2026.05.12` — tag exists on origin
- `git branch -r | grep release/2026.05.12` — release branch pushed
- GitLab CI pipeline for `release/2026.05.12` reaches `deploy_staging` stage with status `passed`
- `http://<staging-cname>/health/` returns 200 with correct revision

## Do not do
- Do NOT run `make swap` or `promote_production` — that is a manual human step.
- Do NOT squash commits — preserve history.
- Do NOT prefix the tag with `v` — the CI gate expects `x.y.z` not `vx.y.z` (branch `release/x.y.z` strips the prefix to find the tag).

## Allowed tools
`git`, `glab`, `make`, `pytest`

## Result
<!-- Worker fills in after completion -->
- Tag pushed:
- Release branch pushed:
- Pipeline URL:
- Staging URL:
- Notes:
