# GitLab issues — Act 3 Playbooks

**Project:** `dp2580/huginn`
**Milestone:** Playbooks et al (`7419452`)
**Master plan:** [`ACT3_PLAYBOOKS_IMPLEMENTATION_PLAN.md`](ACT3_PLAYBOOKS_IMPLEMENTATION_PLAN.md)

Create issues in **PB01 → PB08** order (each branch merges to `main` after its checkpoint passes).

| Issue | Title prefix | Body file |
|-------|----------------|-----------|
| PB01 | `PB01: Playbooks domain models + admin` | [`.gitlab-issue-bodies/PB01.md`](.gitlab-issue-bodies/PB01.md) |
| PB02 | `PB02: Seed FeatureFactory Playbook v1` | [`.gitlab-issue-bodies/PB02.md`](.gitlab-issue-bodies/PB02.md) |
| PB03 | `PB03: PLAYBOOKS-LIST+FIND-1 operational` | [`.gitlab-issue-bodies/PB03.md`](.gitlab-issue-bodies/PB03.md) |
| PB04 | `PB04: PLAYBOOKS-CREATE_PLAYBOOK-1` | [`.gitlab-issue-bodies/PB04.md`](.gitlab-issue-bodies/PB04.md) |
| PB05 | `PB05: PLAYBOOKS-VIEW_PLAYBOOK-1` | [`.gitlab-issue-bodies/PB05.md`](.gitlab-issue-bodies/PB05.md) |
| PB06 | `PB06: PLAYBOOKS-EDIT_PLAYBOOK-1` | [`.gitlab-issue-bodies/PB06.md`](.gitlab-issue-bodies/PB06.md) |
| PB07 | `PB07: PLAYBOOKS-DELETE_PLAYBOOK-1` | [`.gitlab-issue-bodies/PB07.md`](.gitlab-issue-bodies/PB07.md) |
| PB08 | `PB08: Project playbook assignment (FK + UX)` | [`.gitlab-issue-bodies/PB08.md`](.gitlab-issue-bodies/PB08.md) |

### glab one-liners (from repo root)

`glab issue create` expects `-d` / `--description` (not `--description-file`). Example:

```bash
REPO="-R dp2580/huginn"
MS="Playbooks et al"
glab issue create $REPO -t "PB01: Playbooks domain models + admin" -m "$MS" \
  -l Feature -l medium -l act::3-playbooks \
  -d "$(cat docs/plans/.gitlab-issue-bodies/PB01.md)" -y
```

Repeat for PB02–PB08 (PB08 uses `-l hard`).

Run individually if you need labels adjusted (`hard` for PB08).
