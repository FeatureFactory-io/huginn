# Cursor — MIT iteration protocol (Huginn)

Huginn does **not** use `CLAUDE.md`. **Cursor** is the agent surface; treat this file as the **PIT‑04 / MIT‑01 substitute** for “iteration protocol + resume + authority” when checklists still mention Claude Code.

## Where truth lives

1. **Manifest** — `<!-- MANIFEST -->` on the GitLab milestone (copy of `docs/plans/iterations/ITER-*.yaml`).
2. **Per-scenario machine block** — `<!-- SCENARIO -->` in each GitLab issue body.
3. **Execute loop** — [MIT-reference-02-Execute_Loop.md](../../.cursor/workflows/MIT-reference/MIT-reference-02-Execute_Loop.md).
4. **Activate** — [MIT-reference-01-Activate_Iteration.md](../../.cursor/workflows/MIT-reference/MIT-reference-01-Activate_Iteration.md) (translate `gh` → **`glab`**, `github_issue` → **`gitlab_issue` / IID from manifest).

## Iteration protocol (concise)

- Read the milestone manifest and pick the next eligible **`status::queued`** issue (respect **dependencies** and **parallel_groups** in YAML).
- Run the scenario checkpoint from the issue / manifest **before** claiming done.
- Fill skeletons per the issue’s inline implementation plan and `.feature` acceptance list; follow **BPE / MIT** steps in the workflow references above.

## Drift handling

Use **`drift_thresholds`** (and per-issue “Do not do”) in `ITER-*.yaml` and the MIT drift steps. Naming in GitLab labels may use **`::`** (e.g. `status::queued`); mentally map GitHub‑shaped **`status-*`** in reference docs.

## Session resume

- With **`glab`**: resolve **`status::in-progress`** (if any), **re-run the scenario checkpoint**, then continue per MIT‑01 resume rules.
- Do **not** assume `gh issue list`; use **`glab issue list -R dp2580/huginn`** (or your canonical remote).

## Doctrine / version field

If the reference manifest schema expects **`doctrine_version`**, either add it to **`ITER-*.yaml`** when you tighten the manifest, or record the active doctrine revision in merge request / milestone notes. This file does **not** pin a numeric doctrine by itself.

## Authority

Defer to **[MIT‑01 Authority Model](../../.cursor/workflows/MIT-reference/MIT-reference-01-Activate_Iteration.md#authority-model)** for escalate vs autonomous decisions.
