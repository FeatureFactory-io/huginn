# Blueprint: T-SITREP-LIST-STEPS — RED test file for SITREP-LIST+FIND-1

**Issue:** [#76](https://gitlab.com/dp2580/huginn/-/issues/76) — SITREP-LIST+FIND-1
**Task:** [`factory/tasks/pending/T-SITREP-LIST-STEPS.md`](../tasks/pending/T-SITREP-LIST-STEPS.md)
**Feature file:** `docs/features/act-5-sitrep/sitrep-list-find.feature` (SITREP-LIST+FIND-01 … 22)

## Goal

Translate the 22 Gherkin scenarios in `sitrep-list-find.feature` into a pure
`pytest` + `pytest-django` test file at
`tests/ui/test_sitrep_list_scenarios.py`. **No `pytest-bdd`.** Each scenario
becomes one test function whose docstring quotes the scenario block verbatim
and whose body asserts the same outcome via Django test client + DOM
inspection (`bs4` is already available; otherwise use string assertions on
`response.content`).

The test file lands **RED on `main`** — every test must fail at collection or
at first assertion until T-SITREP-LIST-IMPL lands the view, URL, and
template. T-SITREP-LIST-IMPL is the gate that turns them green; this writer
task is purely the test-contract.

## Context

- `tests/ui/conftest.py` exposes `commander_user` + `commander_client`
  fixtures. Use them — do not reinvent auth.
- The mockup `ui/templates/ui/mockups/sitrep/list.html` is the visual
  contract. `data-testid` attributes there become the assertion handles in
  this test file (`generate-sitrep-btn`, `sitrep-table`, `sitrep-row-{id}`,
  `sitrep-empty-state`, `sitrep-period-since-last`, `sitrep-period-2h`, etc).
  The IMPL task ports the template and inherits these testids.
- URL name to assert: `sitrep-list` (resolves to
  `/projects/<int:project_pk>/sitreps/`) and `sitrep-generate` (POST to
  `/projects/<int:project_pk>/sitrep/generate/`). Both are landed by
  T-SITREP-GEN (`sitrep-generate`) and T-SITREP-LIST-IMPL (`sitrep-list`).
- The screen is reached via `Project` PK in URL. The Background's "Project
  atlas-backend exists" maps to a fixture that creates an `ingestion.Project`
  + assigned `Playbook` and uses its PK in the URL.
- Existing models the tests reference: `ingestion.Project`,
  `playbooks.Playbook` + `PlaybookVersion`, `sitrep.SitRep`. SitRep has
  `trigger`, `from_dt`, `to_dt`, `generated_at`, `headline`,
  `playbook_version` (int).
- The two scenarios that mention separate screens (LIST-FIND-02 → reaches
  this screen via PROJECTS-VIEW_PROJECT-1 link; LIST-FIND-08 → row View
  navigates to SITREP-VIEW_SITREP-1) **assert the link `href` only** (not
  cross-page navigation in this test file).

## Files touched

| File | Change |
|------|--------|
| `tests/ui/test_sitrep_list_scenarios.py` | NEW — one test function per scenario; helper fixtures at the top of the file. |

## Interfaces locked

- Test file path: exactly `tests/ui/test_sitrep_list_scenarios.py`.
- Test function naming: `test_sitrep_list_find_NN_<slug>` (NN = 2-digit scenario
  number, slug = 3-5 word kebab → snake). Example:
  `test_sitrep_list_find_06_table_columns`.
- Each function has a docstring containing `# SCENARIO: SITREP-LIST+FIND-NN`
  on its first line followed by the verbatim Gherkin block.
- Module-level `pytestmark = [pytest.mark.django_db]` so every test gets DB.
- Project + Playbook setup as a `@pytest.fixture` named `atlas_project`.
- Asserts use `response.status_code == 200` for happy paths and DOM
  substring / `data-testid` lookups via `bs4.BeautifulSoup`.
- Tests for **GENERATE** dropdown (LIST-FIND-15…20) assert the **GET** of the
  list page contains the dropdown markup. The dropdown's POST behavior is
  asserted by T-SITREP-GEN tests; this file does not POST.
- Tests for filters (LIST-FIND-11…14) issue `?trigger=manual`,
  `?from=…&to=…`, `?pb_version=v1` GET requests against `sitrep-list`. The
  IMPL must accept these query params.
- LIST-FIND-22 (a11y) asserts both `aria-label="Generate SitRep"` and
  `data-testid="generate-sitrep-btn"` on the same element.

## Risks

- Without `bs4`: the helper test parses raw HTML — keep assertions narrow
  (substrings + `data-testid="…"` markers). `bs4` is in the venv (used
  elsewhere in `tests/ui/`); confirm via `rg "bs4" tests/`.
- Some scenarios reference UI-only behavior (tooltip, "Since last SitRep
  (3h 20m ago)" computed label). Test the **template variable**
  presence, not the JS render. Example: assert that the "Since last SitRep"
  `<li>` contains both the testid `sitrep-period-since-last` and a class /
  `disabled` attribute matching the "no prior SitRep" branch.
- LIST-FIND-08 ("row View action navigates"): assert
  `<a … data-testid="sitrep-row-view-{id}" href="…/sitreps/{id}/">` exists.
  The cross-page navigation is for an integration test in a future sprint.
- **Do not** bake fixture dates relative to "today" — Gherkin is explicit
  ("2026-05-10 09:00", "2026-05-11 13:15"). Use `freezegun` only if already
  in test deps; otherwise pass the literal datetimes into the model and
  assert their formatted strings appear in the HTML.

## Acceptance

```
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py --collect-only -q
# expect: 22 collected
.venv/bin/python -m pytest tests/ui/test_sitrep_list_scenarios.py -x
# expect: ERRORS or FAILURES (file exists, tests RED — IMPL not landed)
```

After T-SITREP-LIST-IMPL lands and merges, the same suite runs **green**.
