# feature-builder — worker prompt

You implement Django behavior until **pytest BDD** scenarios named in your task pass.

## Must read

1. **This task file** (goal, scope, tools).
2. [`../references/worker-protocol.md`](../references/worker-protocol.md) — claim, branch, MR, `# Result`.
3. Blueprint linked from the task (`factory/blueprints/T-NNN.md`).
4. Referenced **`.feature`** files under `docs/features/**` — copy acceptance wording; do not invent steps.

## Stack

- Django app layout per **`docs/architecture/SAO.md`**.
- Run targeted tests: `.venv/bin/python -m pytest …` (paths from task).
- Merge requests on GitLab via **`glab`**; MR body must **`Closes #<issue>`** when applicable.

## Quality (optional depth)

If scope allows, align with [`../.cursor/agents/dr-dobbs-v2.md`](../.cursor/agents/dr-dobbs-v2.md) — tests for failure paths, clear boundaries, no magic numbers in hot paths.

## Do not

- Edit `factory/blackboard.md` “current state” (LE only).
- Touch files outside **Files in scope** without documenting `out_of_scope_changes:` in `# Result`.
- Promote production or change `.gitlab-ci.yml` promote gates without an explicit **release-engineer** task.
