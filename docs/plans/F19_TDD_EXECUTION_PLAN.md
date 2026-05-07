# F19 — Red / Green / Refactor execution plan

Companion to [`F19_projects_view_vitals_transparency_IMPLEMENTATION_PLAN.md`](F19_projects_view_vitals_transparency_IMPLEMENTATION_PLAN.md).

This is the **micro-plan** an implementor follows to land both issues:

- [huginn#32 — F19a (service + UI + humanize)](https://gitlab.com/dp2580/huginn/-/issues/32)
- [huginn#33 — F19b (BDD scenarios 01–07)](https://gitlab.com/dp2580/huginn/-/issues/33)

Each step is one **Red → Green → Refactor** cycle. **Commit on each step** (Angular convention). Do not advance until the previous cycle is green and the full suite still passes.

> **Rule:** Each Red step must show a failing test (`pytest -x`). Never skip Red — if a test is already green before you write the implementation, your assertion is too weak.

## Pre-flight

- Branch from `main`: `feature/f19-vitals-transparency`.
- Pull latest. Run `pytest tests/ -x -q` — must be green before starting.
- Confirm `data-testid` names with `docs/features/act-2-projects/projects-view-vitals-tab.feature`.

## Cycle map

| # | Cycle | Scenario(s) | Code touched |
|---|-------|-------------|--------------|
| 0 | Setup | — | settings, factories |
| 1 | Service exists & null path | unit (supports VITALS-05) | `ui/services/project_vitals_service.py` |
| 2 | Service returns latest `occurred_at` | unit (supports VITALS-03) | service |
| 3 | View injects `latest_commit_at` | view-level integration | `ui/views/projects.py` |
| 4 | Transparency card present | VITALS-03 | `detail.html` |
| 5 | "Last sync" relative + a11y row | VITALS-03, VITALS-07 | `detail.html` |
| 6 | "Last commits" relative + a11y row | VITALS-03, VITALS-07 | `detail.html` |
| 7 | Never-synced empty state | VITALS-04 | `detail.html` |
| 8 | No-commits empty state | VITALS-05 | `detail.html` |
| 9 | Tabs labels & `data-testid` | VITALS-01 | tighten existing test |
| 10 | `?tab=vitals` deep-link | VITALS-02 | tighten existing test |
| 11 | Coexistence with Identity/Playbook/Sync | VITALS-06 | tests-only |
| 12 | Refactor & cleanup | — | dedup Sync section, partial extract |

---

## Cycle 0 — Setup (no Red; infrastructure only)

- Add `"django.contrib.humanize"` to `INSTALLED_APPS` in `huginn/settings/base.py`.
- Run full suite — must remain green (nothing depends on it yet, but registration must not break startup).
- Commit: `chore(settings): enable django.contrib.humanize for relative timestamps`.

## Cycle 1 — Service exists, null path (Red → Green → Refactor)

**Red.** Create `tests/unit/test_project_vitals_service.py`:

```python
import pytest
from ui.services.project_vitals_service import ProjectVitalsService
from tests.factories import ProjectFactory


@pytest.mark.django_db
def test_latest_increment_occurred_at_none_for_project_without_commits():
    project = ProjectFactory()
    assert ProjectVitalsService().latest_increment_occurred_at(project.pk) is None
```

`pytest tests/unit/test_project_vitals_service.py -x` → **fails** (module missing).

**Green.** Create `ui/services/project_vitals_service.py` with the smallest method:

```python
from datetime import datetime
from django.db.models import Max
from ingestion.models import Increment


class ProjectVitalsService:
    def latest_increment_occurred_at(self, project_id: int) -> datetime | None:
        return (
            Increment.objects
            .filter(project_id=project_id)
            .aggregate(latest=Max("occurred_at"))["latest"]
        )
```

Run unit test → green.

**Refactor.** Add module docstring; type hints already present.
Commit: `feat(ui): add ProjectVitalsService.latest_increment_occurred_at`.

## Cycle 2 — Service returns latest `occurred_at`

**Red.** Add second test asserting two-row case:

```python
from datetime import timedelta
from django.utils import timezone
from tests.factories import IncrementFactory


@pytest.mark.django_db
def test_latest_increment_occurred_at_returns_newest_timestamp():
    project = ProjectFactory()
    older = timezone.now() - timedelta(days=2)
    newer = timezone.now() - timedelta(hours=2)
    IncrementFactory(project=project, occurred_at=older)
    IncrementFactory(project=project, occurred_at=newer)
    result = ProjectVitalsService().latest_increment_occurred_at(project.pk)
    assert result is not None
    assert abs((result - newer).total_seconds()) < 1
```

Run → fails only if Cycle 1's `Max` query is wrong; otherwise it should already pass — that's fine, we're proving the contract holds with multiple rows. **If it goes green immediately, write a stronger assertion** (e.g. project isolation: another project's newer increment must not leak).

**Green.** No code change expected. If the query was naïve, fix it.

**Refactor.** Add isolation test:

```python
@pytest.mark.django_db
def test_latest_increment_occurred_at_isolated_per_project():
    a = ProjectFactory()
    b = ProjectFactory()
    IncrementFactory(project=a, occurred_at=timezone.now())
    assert ProjectVitalsService().latest_increment_occurred_at(b.pk) is None
```

Commit: `test(ui): cover latest_increment_occurred_at multi-row + isolation`.

## Cycle 3 — View injects `latest_commit_at`

**Red.** In `tests/integration/test_projects_view_vitals_tab.py`, add:

```python
@pytest.mark.django_db
def test_view_provides_latest_commit_context(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    IncrementFactory(project=p, occurred_at=timezone.now() - timedelta(hours=5))
    r = commander_client.get(reverse("projects-detail", args=[p.pk]))
    body = r.content.decode()
    assert "project-widget-transparency" in body  # placeholder; will be added next cycle
```

Will fail (no widget yet).

**Green.** In `ProjectsDetailView.get`, compute `latest_commit_at = ProjectVitalsService().latest_increment_occurred_at(project.pk)` and add to context. **Do not yet** add the template card — assertion above will still fail, which forces Cycle 4.

> Optional ordering: skip Cycle 3 standalone test and combine with Cycle 4 — but keeping them separate documents the seam between view and template.

Commit: `feat(ui): expose latest commit time on project detail context`.

## Cycle 4 — Transparency card present (VITALS-03 anchor)

**Red.** Cycle 3 test `assert "project-widget-transparency" in body` is still red.

**Green.** In `detail.html` Vitals pane, before the Identity section, add:

```html
{% load humanize %}
<section class="hg-vitals-section" aria-labelledby="project-transparency-heading">
  <h2 id="project-transparency-heading" class="h6 text-uppercase text-muted hg-label-caps mb-3">Transparency</h2>
  <dl class="row small mb-0" data-testid="project-widget-transparency">
    {# rows added in cycles 5/6 #}
  </dl>
</section>
```

Re-run integration → green.
Commit: `feat(ui): scaffold Transparency widget on project Vitals`.

## Cycle 5 — "Last sync" relative time row (VITALS-03 + VITALS-07)

**Red.** Add:

```python
@pytest.mark.django_db
def test_vitals_03_last_sync_humanized(commander_client):
    p = ProjectFactory(
        sync_state=Project.SyncState.ACTIVE,
        last_sync_at=timezone.now() - timedelta(hours=2),
    )
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-sync"' in body
    assert "hours ago" in body  # humanize naturaltime
```

Fails — testid missing.

**Green.** Add inside `<dl data-testid="project-widget-transparency">`:

```html
<dt class="col-sm-4 text-muted">Last sync</dt>
<dd class="col-sm-8" data-testid="project-transparency-last-sync">
  {% if project.last_sync_at %}{{ project.last_sync_at|naturaltime }}{% else %}<span class="text-muted">Never</span>{% endif %}
</dd>
```

Re-run → green.

**Refactor.** Verify a11y: `<dt>`/`<dd>` association is implicit (covers VITALS-07 for this row).
Commit: `feat(ui): show relative last_sync_at in Transparency widget`.

## Cycle 6 — "Last commits" relative time row (VITALS-03 + VITALS-07)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_03_last_commits_humanized(commander_client):
    p = ProjectFactory(sync_state=Project.SyncState.ACTIVE)
    IncrementFactory(project=p, occurred_at=timezone.now() - timedelta(hours=5))
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-commits"' in body
    assert "hours ago" in body
```

Fails — testid missing.

**Green.** Add the matching `<dt>/<dd>`:

```html
<dt class="col-sm-4 text-muted">Last commits</dt>
<dd class="col-sm-8" data-testid="project-transparency-last-commits">
  {% if latest_commit_at %}{{ latest_commit_at|naturaltime }}{% else %}<span class="text-muted">No commits yet</span>{% endif %}
</dd>
```

Re-run → green.
Commit: `feat(ui): show relative latest commit time in Transparency widget`.

## Cycle 7 — Never-synced empty state (VITALS-04)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_04_never_synced_empty_state(commander_client):
    p = ProjectFactory(last_sync_at=None)
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-sync"' in body
    assert "Never" in body
```

Should already pass after Cycle 5 — if it does, **strengthen** the assertion (e.g. ensure no `naturaltime` artefact like "ago" appears in the Last sync `<dd>`). If it fails, fix template.

**Refactor.** Confirm copy with feature file; if you change "Never", update the feature file Scenario 04 to remove the `(copy TBD)` qualifier and run again.
Commit: `test(ui): cover never-synced state for Transparency`.

## Cycle 8 — No-commits empty state (VITALS-05)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_05_no_commits_empty_state(commander_client):
    p = ProjectFactory()
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-transparency-last-commits"' in body
    assert "No commits yet" in body
```

Should pass post-Cycle 6 — same strengthening rule applies.
Commit: `test(ui): cover no-commits state for Transparency`.

## Cycle 9 — Tabs labels & `data-testid` (VITALS-01)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_01_tab_labels_and_testids(commander_client):
    p = ProjectFactory()
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    assert 'data-testid="project-tab-vitals"' in body
    assert ">Vitals<" in body or "Vitals</button>" in body
    assert "Increments" in body
```

Should pass — strengthen if too lax.
Commit: `test(ui): tighten Vitals/Increments tab assertions`.

## Cycle 10 — Deep-link `?tab=vitals` (VITALS-02)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_02_deeplink_activates_vitals(commander_client):
    p = ProjectFactory()
    r = commander_client.get(reverse("projects-detail", args=[p.pk]) + "?tab=vitals")
    body = r.content.decode()
    assert 'aria-selected="true"' in body
    assert 'id="project-tab-vitals"' in body
    assert 'class="nav-link active" id="project-tab-vitals"' in body or \
           'class="nav-link active"\n          id="project-tab-vitals"' in body
```

> Use a soft contains check (e.g. parse with BeautifulSoup) if exact whitespace is brittle. Document choice in the test.

Should pass; tighten otherwise.
Commit: `test(ui): assert ?tab=vitals activates Vitals tab`.

## Cycle 11 — Coexistence (VITALS-06)

**Red.**

```python
@pytest.mark.django_db
def test_vitals_06_identity_playbook_sync_still_present(commander_client):
    p = ProjectFactory()
    body = commander_client.get(reverse("projects-detail", args=[p.pk])).content.decode()
    for tid in (
        "project-source-path",
        "project-playbook-section",
        "project-sync-schedule",
    ):
        assert f'data-testid="{tid}"' in body
    # Increments table appears only on tab=increments
    assert 'data-testid="increments-table"' not in body
```

Should pass — if the Increments table renders on Vitals, bug to fix.
Commit: `test(ui): assert coexistence of Identity/Playbook/Sync on Vitals`.

## Cycle 12 — Refactor & cleanup

> Tests must remain green throughout this cycle.

1. **Dedup Sync section:** Remove the redundant `<p>Last sync: …</p>` line (current `detail.html` line ~102) — Transparency now owns this. Keep `project-sync-schedule` and the next-cadence note.
   - Re-run integration tests; if any test asserted on `project-last-sync` as legacy, update it to assert on `project-transparency-last-sync`.
2. **Optional template partial:** if the Transparency block grows, extract `ui/templates/ui/projects/_transparency.html` and `{% include %}`.
3. **CSS:** keep within `static/css/huginn.css`; reuse `hg-vitals-section` & `hg-label-caps`. Avoid new utility classes.
4. **Self-review:** read `docs/architecture/SAO.md` §1 (`ui/` no business logic) — confirm view contains only the service call.
5. **Final regression:** `pytest tests/ -x -q`.

Commit: `refactor(ui): remove redundant Sync 'Last sync' (now in Transparency)`.

## Closing

- Push branch; open MR titled `F19 — Vitals Transparency widget`.
- In MR description, link both issues with `Closes #32, Closes #33` and quote checkpoint:

```bash
pytest tests/integration/test_projects_view_vitals_tab.py tests/unit/test_project_vitals_service.py -x -q
```

- Wait for CI green.
- After review: squash-merge if project policy requires; otherwise let small commits land.

## Drift / blockers

If a cycle reveals you cannot stay within the **Do Not Do** list (e.g. business logic creeping into the view), stop and raise a drift event in the MR description before continuing.
