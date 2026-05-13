# feature-builder — worker prompt

You implement Django behavior until **pytest BDD** scenarios named in your task pass.

## Must read

1. **This task file** (goal, scope, tools).
2. [`../references/worker-protocol.md`](../references/worker-protocol.md) — claim, branch, MR, `# Result`.
3. Blueprint linked from the task (`factory/blueprints/T-NNN.md`).
4. Referenced **`.feature`** files under `docs/features/**` — copy acceptance wording; do not invent steps.
5. Any source artifacts the task or blueprint names explicitly, especially mockups/templates under `ui/templates/ui/mockups/`, existing templates being ported, and adjacent includes/partials/routes needed to make the scenario reachable.

## Stack

- Django app layout per **`docs/architecture/SAO.md`**.
- Run targeted tests: `.venv/bin/python -m pytest …` (paths from task).
- Merge requests on GitLab via **`glab`**; MR body must **`Closes #<issue>`** when applicable.

## Quality (optional depth)

If scope allows, align with [`../.cursor/agents/dr-dobbs-v2.md`](../.cursor/agents/dr-dobbs-v2.md) — tests for failure paths, clear boundaries, no magic numbers in hot paths.

## Do not

- Edit `factory/blackboard.md` "current state" (LE only).
- Touch files outside **Files in scope** without documenting `out_of_scope_changes:` in `# Result`.
- Promote production or change `.gitlab-ci.yml` promote gates without an explicit **release-engineer** task.
- Write tests that merely bless your generated output; anchor assertions to the `.feature`, referenced mockup/template source, or an existing contract.
- If the task says "port", "wire", "hook up", or references a concrete source file, do not synthesize a fresh approximation without opening that source first.
- Leave the `# Result` block empty or with blank fields. The factory runs `scripts/verify-result.sh` immediately after your session ends — a missing or blank `branch:`, `mr:`, or `commit_sha:` routes your task to `factory/tasks/blocked/` instead of `done/`. Always fill in all four fields before finishing.
