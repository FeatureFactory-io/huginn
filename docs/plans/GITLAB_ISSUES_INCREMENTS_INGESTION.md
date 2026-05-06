# GitLab issues — Increments ingestion (Phases I–O)

Create issues on `dp2580/huginn`, milestone **Datasources & Projects**, labels: `Feature,act::2-projects,status::queued` plus difficulty where noted.

```bash
# From repo root — example F13:
glab issue create -R dp2580/huginn \
  --title "Act 2 Projects — Phase J (F13): Increment / Contributor / IngestionRun models + DTOs" \
  --milestone "Datasources & Projects" \
  --label "Feature,act::2-projects,status::queued,medium" \
  --description-file docs/plans/.gitlab-issue-bodies/F13.md
```

**Order:** F12 (I) → F13 (J) → … → F18 (O). Add `Depends on: huginn#PREV_IID` at top of each body after creation.

**Bodies:** [`.gitlab-issue-bodies/F12.md`](.gitlab-issue-bodies/F12.md) through [`F18.md`](.gitlab-issue-bodies/F18.md).

**Plans:** [F12_sync_specification_IMPLEMENTATION_PLAN.md](F12_sync_specification_IMPLEMENTATION_PLAN.md) … [F18_projects_increments_tab_IMPLEMENTATION_PLAN.md](F18_projects_increments_tab_IMPLEMENTATION_PLAN.md)
