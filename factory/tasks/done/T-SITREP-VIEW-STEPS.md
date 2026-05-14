---
id: T-SITREP-VIEW-STEPS
role: step-def-writer
attempt: 1
depends_on: [T-SITREP-LIST-IMPL]
gitlab_issue: 77
branch: factory/T-SITREP-VIEW-STEPS-red-tests
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - tests/ui/test_sitrep_view_scenarios.py
---

# Task T-SITREP-VIEW-STEPS — RED tests for SITREP-VIEW_SITREP-1

## Goal

Land **`tests/ui/test_sitrep_view_scenarios.py`** containing one pytest
function per Gherkin scenario in
`docs/features/act-5-sitrep/sitrep-view.feature` (31 scenarios). The file
lands RED on `main`. T-SITREP-VIEW-IMPL turns them GREEN.

## Must read first

1. **GitLab issue #77** — `glab issue view 77`.
2. [`factory/blueprints/T-SITREP-VIEW-STEPS.md`](../../blueprints/T-SITREP-VIEW-STEPS.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. **Feature file (verbatim acceptance contract)** —
   `docs/features/act-5-sitrep/sitrep-view.feature`.
5. **Mockup** — `ui/templates/ui/mockups/sitrep/view.html`. The `data-testid`
   attributes are the test handles.
6. `tests/ui/conftest.py` — fixtures.
7. `tests/ui/test_sitrep_list_scenarios.py` (landed by T-SITREP-LIST-STEPS) —
   reuse the fixture style for consistency.
8. `sitrep/models/{sitrep,frago}.py`, `ingestion/models/project.py`,
   `playbooks/models/{playbook,playbook_version}.py`.

## Acceptance criteria

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py --collect-only -q
# 31 tests collected, no collection errors
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
# every test RED (FAILED or ERROR — never passed) until T-SITREP-VIEW-IMPL lands
ruff check tests/ui/test_sitrep_view_scenarios.py && ruff format --check tests/ui/test_sitrep_view_scenarios.py
.venv/bin/python -m pytest tests/ -x --ignore=tests/ui/test_sitrep_view_scenarios.py
# full suite (excluding the new RED file) green — no regressions
```

## Files in scope

- `tests/ui/test_sitrep_view_scenarios.py` (NEW) — see blueprint for
  structure. Function naming: `test_sitrep_view_NN_<slug>`. Each
  function's docstring **first line** is `# SCENARIO: SITREP-VIEW-NN`,
  followed by the verbatim Gherkin block.
- Fixture for the Background SitRep: see blueprint "Risks" — `update`
  generated_at after creation since it's `auto_now_add`.

## Test contract

- URL name `sitrep-view` resolves to
  `/projects/<int:project_pk>/sitreps/<int:pk>/` (T-SITREP-VIEW-IMPL lands).
- Use `bs4.BeautifulSoup(response.content, 'html.parser')`; query by
  `data-testid` and section heading text.
- VIEW-29 ("back" link) asserts `<a href>` to URL `sitrep-list`. By the
  time these tests run, T-SITREP-LIST-IMPL has merged (per `depends_on:
  [T-SITREP-LIST-IMPL]`), so `reverse('sitrep-list', kwargs={'project_pk':
  …})` resolves.
- VIEW-27 ("Open Chat") link target: assert the `<a>` has `data-testid=
  "sitrep-open-chat-link"`. If `chat-fullscreen` URL is not registered,
  accept `href="#"` and **flag** in the result block.
- VIEW-04, VIEW-08 use **separate fixtures** — do not parametrize the
  Background fixture; create distinct manual / auto-mode SitRep instances.

## Do not touch

- `ui/`, `gjallarhorn/`, `sitrep/models/`, `ingestion/models/` —
  implementation surface frozen to T-SITREP-VIEW-IMPL.
- Any other test file under `tests/`.
- **No `FOB-*` Screen IDs** — Screen ID is `SITREP-VIEW_SITREP-1` (no `FOB-`).

## Branch & MR

```bash
cd .worktrees/step-def-writer
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-SITREP-VIEW-STEPS-red-tests

# … write tests/ui/test_sitrep_view_scenarios.py …

.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py --collect-only -q
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x ; echo "exit=$?  (non-zero is EXPECTED — these are RED)"
.venv/bin/python -m pytest tests/ -x --ignore=tests/ui/test_sitrep_view_scenarios.py
ruff check . && ruff format --check .

git add tests/ui/test_sitrep_view_scenarios.py
git commit -m "test(ui): RED scenarios for SITREP-VIEW_SITREP-1 (31 functions)"
git push -u origin factory/T-SITREP-VIEW-STEPS-red-tests

glab mr create \
  --source-branch factory/T-SITREP-VIEW-STEPS-red-tests \
  --target-branch main \
  --title "test(ui): RED scenarios for SITREP-VIEW_SITREP-1" \
  --description "Lands 31 RED test functions covering SITREP-VIEW-01..31. T-SITREP-VIEW-IMPL turns them GREEN. Part of #77." \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py --collect-only -q
# expect: 31 collected
```

## Do not

- Do NOT use `pytest-bdd`.
- Do NOT make tests pass.
- Do NOT add `@pytest.mark.skip` or `xfail`.
- Do NOT modify mockups or invent new testids.


# Result

status: integrated
branch: factory/T-SITREP-VIEW-STEPS-red-tests
mr: 33
commit_sha: b973accd

Auto-filled by rescue-result.sh — worker exited without writing Result block.
