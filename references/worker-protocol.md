# Worker protocol — dark factory (Huginn)

Filesystem queue under **`factory/tasks/`**. The Lead Engineer (LE) writes **`pending/`** and **`blocked/`**; workers **claim** with atomic `mv`; LE reviews **`done/`**.

## Task file (`pending/T-NNN.md`)

YAML frontmatter (between `---` lines) **required**:

```yaml
---
id: T-042
role: feature-builder   # step-def-writer | feature-builder | release-engineer | manual-tester
attempt: 1
depends_on:
  - T-041
gitlab_issue: 123
branch: factory/T-042-short-slug
tools:
  - git
  - glab
  - pytest
files_in_scope:
  - ui/views/foo.py
---
```

- **`depends_on`:** omit key, use `[]`, one-line `[ T-041, T-042 ]`, or YAML list. Every listed id must have **`factory/tasks/done/<id>.md`** before `scripts/claim.sh` succeeds.
- **`branch`:** convention above; worker pushes this branch and opens MR to **`main`** (or task-specified base).

Body sections (minimum):

- **Goal** — one paragraph.
- **Blueprint** — link: `factory/blueprints/T-042.md`.
- **Acceptance** — verbatim bullets from the `.feature` Scenario(s).
- **Checkpoint command** — pytest (or other) command line.

## Claim

From repo root:

```bash
./scripts/claim.sh T-042 feature-builder
```

Prints absolute path to **`factory/tasks/claimed/T-042.md`**. On failure (wrong role, deps missing, race): exit `1`.

## While working

- Work only in **`files_in_scope`** unless justified under **`out_of_scope_changes:`** in `# Result`.
- Follow declared **`tools`** only.

## Finish (`done/`)

Prefer:

```bash
./scripts/done.sh T-042
```

Edit **`# Result`** before or after move:

```markdown
# Result

status: passed          # passed | failed | blocked
branch: factory/T-042-slug
mr: 456
commit_sha: abc1234

Brief notes for LE review.
out_of_scope_changes: []   # or list with justification
```

Atomicity: when writing the done file from scratch, write to **`factory/tasks/done/.T-042.md.tmp`** then **`mv`** to **`factory/tasks/done/T-042.md`** (same pattern inside `claimed/`).

## Rejection (LE)

```bash
./scripts/reject.sh T-042 "Check 5 failed: scenario X …"
```

Archives snapshot under **`factory/tasks/rejected/T-042/<timestamp>.txt`**. LE re-creates **`pending/T-042.md`** with bumped **`attempt:`**.

## Merge request

- Title: include **`T-042`** and short summary.
- Description: link blueprint + scenarios + **`Closes #<gitlab_issue>`** when closing is intended.

## Git commits

Factory convention (from skill): one logical transition → one commit when updating **`factory/**`** (e.g. `factory: claim T-042`, `factory: done T-042`). Feature code follows normal project conventions.
