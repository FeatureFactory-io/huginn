---
id: T-SITREP-LIST-STEPS
role: step-def-writer
attempt: 1
depends_on: [T-SITREP-GEN]
gitlab_issue: 76
branch: factory/T-SITREP-LIST-STEPS-red-tests
tools:
  - git
  - glab
  - python
  - pytest
  - ruff
files_in_scope:
  - tests/ui/test_sitrep_list_scenarios.py
---

# Task T-SITREP-LIST-STEPS — RED tests for SITREP-LIST+FIND-1

## Goal

Land **`tests/ui/test_sitrep_list_scenarios.py`** containing one pytest
function per Gherkin scenario in
`docs/features/act-5-sitrep/sitrep-list-find.feature` (22 scenarios). The
file lands RED on `main` — tests fail at collection or first assertion until
T-SITREP-LIST-IMPL lands the view + template + URL.

This is a **step-def-writer** task. You write tests, not implementation.

## Must read first

1. **GitLab issue #76** — `glab issue view 76`.
2. [`factory/blueprints/T-SITREP-LIST-STEPS.md`](../../blueprints/T-SITREP-LIST-STEPS.md).
3. [`factory/blueprints/system.md`](../../blueprints/system.md).
4. **Feature file (verbatim acceptance contract)** —
   `docs/features/act-5-sitrep/sitrep-list-find.feature` (read every scenario;
   write one test for every scenario).
5. **Mockup** — `ui/templates/ui/mockups/sitrep/list.html`. The `data-testid`
   attributes there are the test handles. Do not invent new testids; if the
   mockup is missing one a scenario needs, **flag** in the result block.
6. `tests/ui/conftest.py` — `commander_user`, `commander_client` fixtures.
7. `sitrep/models/sitrep.py`, `ingestion/models/project.py`,
   `playbooks/models/{playbook,playbook_version}.py` — for fixture setup.

## Acceptance criteria

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py --collect-only -q
# 22 tests collected, no collection errors
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
# every test RED (FAILED or ERROR — never passed) until T-SITREP-LIST-IMPL lands
ruff check tests/ui/test_sitrep_list_scenarios.py && ruff format --check tests/ui/test_sitrep_list_scenarios.py
# clean
.venv/bin/python -m pytest tests/ -x --ignore=tests/ui/test_sitrep_list_scenarios.py
# full suite (excluding the new RED file) green — no regressions
```

## Files in scope

- `tests/ui/test_sitrep_list_scenarios.py` (NEW) — see blueprint for
  structure. One pytest function per scenario; module-level
  `pytestmark = [pytest.mark.django_db]`; helper fixtures at the top.
  Function naming: `test_sitrep_list_find_NN_<slug>`.
- Each test function's docstring **first line** contains
  `# SCENARIO: SITREP-LIST+FIND-NN`, followed by the verbatim Gherkin block
  (so a future grep finds the source).

## Test contract (per the blueprint)

- URL name `sitrep-list` resolves to
  `/projects/<int:project_pk>/sitreps/` (the IMPL task lands the route).
- URL name `sitrep-generate` resolves to
  `/projects/<int:project_pk>/sitrep/generate/` (T-SITREP-GEN landed it; you
  may rely on `reverse('sitrep-generate', kwargs={'project_pk': p.pk})`
  returning the right URL by the time tests run because T-SITREP-GEN merged
  before this task per `depends_on`).
- Background fixtures: a `commander_user` (from conftest), an `ingestion.Project`
  with `slug='atlas-backend'` + assigned Playbook + PlaybookVersion v1,
  optionally seeded SitReps.
- Use `bs4.BeautifulSoup(response.content, 'html.parser')` to look up
  testids: `soup.select_one('[data-testid="…"]')`. `bs4` is available in
  the venv.

## Do not touch

- `ui/views/`, `ui/templates/`, `ui/urls.py` — owned by T-SITREP-LIST-IMPL.
- Any other test file under `tests/`.
- `gjallarhorn/`, `sitrep/models/`, `ingestion/models/` — model surface is frozen.
- **Do not** introduce `FOB-*` Screen IDs anywhere
  (`.cursor/rules/no-fob-screen-ids.mdc`). The Screen ID this feature uses is
  `SITREP-LIST+FIND-1` (no `FOB-` prefix).

## Branch & MR

```bash
cd .worktrees/step-def-writer
git fetch origin && git checkout main && git reset --hard origin/main
git checkout -b factory/T-SITREP-LIST-STEPS-red-tests

# … write tests/ui/test_sitrep_list_scenarios.py …

.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py --collect-only -q
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x ; echo "exit=$?  (non-zero is EXPECTED — these are RED)"
.venv/bin/python -m pytest tests/ -x --ignore=tests/ui/test_sitrep_list_scenarios.py
ruff check . && ruff format --check .

git add tests/ui/test_sitrep_list_scenarios.py
git commit -m "test(ui): RED scenarios for SITREP-LIST+FIND-1 (22 functions)"
git push -u origin factory/T-SITREP-LIST-STEPS-red-tests

glab mr create \
  --source-branch factory/T-SITREP-LIST-STEPS-red-tests \
  --target-branch main \
  --title "test(ui): RED scenarios for SITREP-LIST+FIND-1" \
  --description "Lands 22 RED test functions covering SITREP-LIST+FIND-01..22. T-SITREP-LIST-IMPL turns them GREEN. Part of #76." \
  --yes
```

## Checkpoint

```bash
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py --collect-only -q
# expect: 22 collected
```

## Do not

- Do NOT use `pytest-bdd` — pure `pytest` + `pytest-django`.
- Do NOT make tests pass — they MUST fail until IMPL lands.
- Do NOT add `@pytest.mark.skip` or `xfail`. RED means fail, not skip.
- Do NOT modify the mockup or invent new `data-testid`s.

# Result

status:
branch:
mr:
commit_sha:
