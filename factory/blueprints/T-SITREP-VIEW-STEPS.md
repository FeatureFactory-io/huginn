# Blueprint: T-SITREP-VIEW-STEPS — RED test file for SITREP-VIEW_SITREP-1

**Issue:** [#77](https://gitlab.com/dp2580/huginn/-/issues/77) — SITREP-VIEW_SITREP-1
**Task:** [`factory/tasks/pending/T-SITREP-VIEW-STEPS.md`](../tasks/pending/T-SITREP-VIEW-STEPS.md)
**Feature file:** `docs/features/act-5-sitrep/sitrep-view.feature` (SITREP-VIEW-01 … 31)

## Goal

Translate the 31 Gherkin scenarios in `sitrep-view.feature` into a pure
`pytest` + `pytest-django` test file at
`tests/ui/test_sitrep_view_scenarios.py`. **No `pytest-bdd`.** Each scenario
becomes one test function (`test_sitrep_view_NN_<slug>`); docstring quotes the
verbatim scenario.

The test file lands **RED on `main`** until T-SITREP-VIEW-IMPL lands the
view + template + URL.

## Context

- `tests/ui/conftest.py` exposes `commander_user` + `commander_client`. Reuse.
- The mockup `ui/templates/ui/mockups/sitrep/view.html` is the visual
  contract — its `data-testid` attributes are the assertion handles.
- URL: `sitrep-view` resolves to `/projects/<int:project_pk>/sitreps/<int:pk>/`.
- Background: a `Project` + assigned `Playbook` v1 + a seeded `SitRep`
  with the literal field values from the feature's Background Given table
  (`generated_at='2026-05-11 13:15'`, `from_dt='2026-05-11 09:00'`, etc).
- Five sections to assert: **Situation Assessment**, **Variables Snapshot**
  (placeholder), **Decisions** (placeholder), **FRAGOs Applied**, **Notable
  Activity**.
- Several scenarios reference cross-screens (VIEW-27 → CHAT-FULLSCREEN-1,
  VIEW-29 → SITREP-LIST+FIND-1). Assert the link `href` only.
- VIEW-04, VIEW-08, VIEW-37 (Manual badge / Auto mode badge / FRAGOs variants)
  require new SitRep fixtures with overridden fields. Use parametrize or
  separate fixtures.

## Files touched

| File | Change |
|------|--------|
| `tests/ui/test_sitrep_view_scenarios.py` | NEW — 31 test functions; helper fixtures at the top. |

## Interfaces locked

- Test file path: exactly `tests/ui/test_sitrep_view_scenarios.py`.
- Function naming: `test_sitrep_view_NN_<slug>`. Example:
  `test_sitrep_view_06_no_variables_badge_grey`.
- Module-level `pytestmark = [pytest.mark.django_db]`.
- Fixtures: `atlas_project` (Project + Playbook v1), `auto_sitrep`
  (the Background SitRep), `manual_sitrep` / `auto_mode_sitrep` for VIEW-04 /
  VIEW-08, `fragos_active_in_window`, `fragos_disabled_before_period`.
- Tests use `bs4.BeautifulSoup`. Assertions look up `data-testid`s:
  `sitrep-assessed-period`, `sitrep-status-badge`, `sitrep-mode-badge`,
  `sitrep-open-decisions-btn`, `sitrep-open-variables-btn`.
- Section headings asserted by `<h2>` / `<h3>` text content — not testid —
  per scenarios VIEW-09 / -12 / -14 / -16 / -21.
- VIEW-27 (chat link) asserts an `<a href>` to the URL named
  `chat-fullscreen` if present in `ui/urls.py`; if not, accept a placeholder
  `#` and **flag** in the result block (Chat milestone wires the actual
  route).

## Risks

- Background field types: `generated_at` is `auto_now_add`, so the fixture
  must `update_or_create` then **`SitRep.objects.filter(pk=…).update(
  generated_at=…)`** to override. Document this in the fixture.
- Timezone (VIEW-02): "the period is displayed in the user's local timezone".
  The Django test client sets `TIME_ZONE` from settings; assert the rendered
  `assessed_period` matches `Mon 09:00 → 13:15` formatted via
  `django.utils.timezone.localtime` of the SitRep's `from_dt` / `to_dt`.
- VIEW-13 / VIEW-15 (placeholder messages) — assert the **literal** text
  "Variables will be available in a future release" and "No Decisions
  proposed" and that no Variable / Decision rows render
  (assert no element with a `*-row-*` testid the mockup uses for those).
- VIEW-19 (FRAGO empty state): assert the literal "No FRAGOs were applied to
  this assessment" string.
- VIEW-26 (Generate dropdown on view screen): assert the dropdown's
  "Since last SitRep" `<li>` is selected/present and labeled
  "Since last SitRep (Xh Ym ago)" — same pattern as LIST-FIND-18.
- VIEW-28 (read-only): assert the response **does not** contain the strings
  "Edit", "Delete", or "Modify" anywhere in the rendered HTML (case-insensitive
  search; allow `data-testid="*"` matching to be more precise — e.g. assert
  no element with testid `sitrep-edit-btn` exists).

## Acceptance

```
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py --collect-only -q
# expect: 31 collected
.venv/bin/python -m pytest tests/ui/test_sitrep_view_scenarios.py -x
# expect: ERRORS or FAILURES (file exists, tests RED — IMPL not landed)
```
