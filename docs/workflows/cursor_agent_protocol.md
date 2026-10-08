# Cursor agent protocol (Huginn)

Huginn does **not** use `CLAUDE.md`. **Cursor** is the primary agent surface.

## Primary execution model

Use the **dark-factory** Cursor skill (install `dark-factory`, read `SKILL.md` in that skill folder) for milestone-driven delivery: GitLab milestone + issues, ingestion of plans/features/mockups, decomposition, parallel workers when the repo has the `factory/` scaffold, integration to `main`, **BPE-06 / BPE-07**, and semver release per **`docs/architecture/SAO.md` §9–§10**. Follow that skill’s phases and human checkpoints.

## Where truth lives

1. **Manifest** — `<!-- MANIFEST -->` on the GitLab milestone (source: `docs/plans/iterations/ITER-*.yaml` or published equivalent).
2. **Per-scenario blocks** — machine-readable blocks in GitLab issue bodies (e.g. `<!-- SCENARIO -->`).
3. **Architecture & CI/CD** — [`docs/architecture/SAO.md`](../architecture/SAO.md) (especially §9–§10).
4. **Implementation playbooks** — [`.cursor/workflows/BPE/`](../../.cursor/workflows/BPE/) (plan, implement, definition of done, finalize) and **`docs/features/**`**.

## Worker code quality (Dr. Dobbs)

Implementation and review should align with the cautious-developer bar in **[`.cursor/agents/dr-dobbs-v2.md`](../../.cursor/agents/dr-dobbs-v2.md)** (defensive programming, testability, observability, SOLID). The dark-factory **Lead Engineer** uses it when judging worker output and MR diffs; feature workers may treat it as optional depth where it conflicts with an explicit task scope.

## GitLab commands

Use **`glab`**, not `gh`. Example: `glab issue list -R dp2580/huginn` (adjust for your remote).

## Working conventions

**What dark-factory actually uses:** The skill coordinates through **GitLab** (milestone, issues, `glab`) and the **`factory/`** tree (`blackboard.md`, blueprints, `tasks/**` with per-task **`depends_on`**). Preflight and `factory.sh` do **not** read `ITER-*.yaml`; that matches **`SKILL.md`** (Phases 1–3), which never names `parallel_groups` or `drift_thresholds`.

**Optional Huginn planning mirror:** Some milestones also publish **`docs/plans/iterations/ITER-*.yaml`** and/or a `<!-- MANIFEST -->` block on GitLab (see **Where truth lives** above). Treat that YAML as **Lead Engineer / human guidance** when it exists—legacy PIT/MIT playbooks are gone; these keys are just structured iteration notes:

- **`parallel_groups`** and any dependency hints → fold into **task decomposition** and task-level **`depends_on`** (same idea as SKILL Phase 2, not a separate automation layer).
- **`drift_thresholds`** and per-issue “do not do” lists → inform review and remediation; **not** CI-enforced gates unless you add tooling.
- **`doctrine_version`** (if present) → keep aligned with team notes in MRs or milestone text when conventions change.

**Always:**

- Run scenario checkpoints from the issue **before** claiming a slice is done.
- GitLab labels may use **`::`** (e.g. `status::queued`).

## Session resume

With **`glab`**: if issues are **`status::in-progress`**, re-run their scenario checkpoint, then continue from the last committed state.

## Authority

- **Irreversible or external**: production promotion (`promote_production` / `make swap`), closing milestones, destructive infra — **explicit human approval** unless pre-authorized in writing.
- **Lead Engineer** (per dark-factory): scoped edits to `factory/**`, `docs/sprints/**`, merge/integration work, and release steps that match **SAO** + **Makefile**; workers stay inside task files.

## Release & CI/CD (Huginn)

Shipping to **staging** and **production** is **canonical in [`docs/architecture/SAO.md`](../architecture/SAO.md) §9–§10**: `Makefile` + `scripts/` own commands; GitLab `.gitlab-ci.yml` runs `make` targets (or the same shell scripts on Kaniko / `release-cli` images); pipelines run on **`release/x.y.z`** only after a matching Git tag; **inactive** Elastic Beanstalk = staging; **`promote_production`** / **`make swap`** moves **whatever revision is already on staging** to prod — **not** auto-swap after staging smoke, and **not** by picking a new ref at promote time (deploy staging → test → bugfix/redeploy → regression → then promote).

If the **dark-factory** skill and **SAO** disagree, **SAO + the repo Makefile** take precedence.
