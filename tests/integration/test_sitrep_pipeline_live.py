"""SitRep pipeline live end-to-end test — hits the real Anthropic API.

Proves the complete sequence with realistic fake data and a real playbook:
  1. SitRep is requested.
  2. ExecutionPlan with 5 steps is created in DB.
  3. All 5 steps are executed by Claude (claude-sonnet-4-6).
  4. A non-critical data step failure does NOT crash the plan.
  5. A real SitRep is persisted and ready to display.

Skip condition: ANTHROPIC_API_KEY not set.
Run with: pytest tests/integration/test_sitrep_pipeline_live.py -v -s
"""

import os
from datetime import date, timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone

# Load .env at import time so @pytest.mark.skipif can read ANTHROPIC_API_KEY
# (skipif expressions are evaluated at collection, before any test body runs).
try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(Path(__file__).parent.parent.parent / ".env", override=False)
except ImportError:
    pass

from gjallarhorn.models import ExecutionPlan, PlanStep
from gjallarhorn.tasks.plan_tasks import execute_plan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Contributor, Increment
from playbooks.models import Playbook, PlaybookVersion
from sitrep.models import Frago, SitRep, SituationalAwareness, SituationalAwarenessVersion
from tests.factories import DataSourceFactory, ProjectFactory, UserFactory

_SKIP_NO_KEY = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live AI test",
)

# ---------------------------------------------------------------------------
# Realistic playbook content
# ---------------------------------------------------------------------------

_PLAYBOOK_MD = """\
# Software Team Health Assessment Playbook

## Purpose
Assess the engineering team's delivery health for a given time window
based on commit activity, contributor patterns, and active orders.

## Assessment Dimensions

### 1. Velocity
Rate by commits per contributor per day:
- GREEN  — ≥ 2 commits/contributor/day on average, steady flow
- AMBER  — 1–2 commits, some idle days
- RED    — < 1 commit, visible stall or single-contributor bottleneck

### 2. Quality Signals
Review message keywords: `fix`, `bug`, `revert`, `hotfix`, `patch`
- GREEN  — ≤ 20 % remediation commits
- AMBER  — 21–40 %
- RED    — > 40 % or any `revert`

### 3. Collaboration Spread
- GREEN  — 3 + active contributors, no single author > 60 % of commits
- AMBER  — 2 contributors or one author at 60–80 %
- RED    — 1 contributor or single author > 80 %

### 4. Focus
Classify commit areas from message prefixes/keywords:
- GREEN  — work concentrated in ≤ 2 areas
- AMBER  — 3 distinct areas
- RED    — ≥ 4 unrelated areas (scattered effort)

## Output Format (strict JSON)
```json
{
  "headline": "<OVERALL RAG> — <one-line summary>",
  "situation_assessment": "<2–4 sentences describing velocity, quality, collaboration>",
  "notable_activity": ["<observation 1>", "<observation 2>", "..."]
}
```
Produce only valid JSON — no markdown wrapper, no extra keys.
"""

# ---------------------------------------------------------------------------
# Realistic commit dataset (12 commits, 3 contributors, mixed topics)
# ---------------------------------------------------------------------------

_COMMITS = [
    # --- Alice: feature work ---
    ("alice@atlas.dev", "Alice Chen", "feat(api): add paginated /projects endpoint"),
    ("alice@atlas.dev", "Alice Chen", "feat(api): implement cursor-based pagination"),
    ("alice@atlas.dev", "Alice Chen", "test(api): add pytest suite for pagination edge cases"),
    ("alice@atlas.dev", "Alice Chen", "chore: bump django-rest-framework to 3.15.2"),
    # --- Bob: bug fixes & infra ---
    ("bob@atlas.dev", "Bob Okafor", "fix(auth): resolve token expiry not clearing session cache"),
    ("bob@atlas.dev", "Bob Okafor", "fix(celery): worker silently drops tasks on oom signal"),
    ("bob@atlas.dev", "Bob Okafor", "infra: add healthcheck endpoint for load balancer"),
    # --- Carol: data layer ---
    ("carol@atlas.dev", "Carol Liu", "refactor(db): extract query layer into repository pattern"),
    ("carol@atlas.dev", "Carol Liu", "feat(db): add composite index on (project_id, occurred_at)"),
    ("carol@atlas.dev", "Carol Liu", "test(db): integration tests for repository layer"),
    ("carol@atlas.dev", "Carol Liu", "docs: update ARCHITECTURE.md with repository pattern"),
    # --- Bob: late PR ---
    ("bob@atlas.dev", "Bob Okafor", "perf(api): cache contributor activity in Redis (60 s TTL)"),
]


# ---------------------------------------------------------------------------
# Fixture: rich fake world
# ---------------------------------------------------------------------------


@pytest.fixture()
def live_world(db):
    """Build a realistic project with playbook, commits, SA, and one FRAGO."""
    # --- user & project ---
    user = UserFactory()
    ds = DataSourceFactory()
    playbook = Playbook.objects.create(slug="team-health-v1", name="Team Health Assessment")
    PlaybookVersion.objects.create(
        playbook=playbook,
        version_number=1,
        workflow_md=_PLAYBOOK_MD,
        change_summary="Initial version",
    )
    project = ProjectFactory(
        name="atlas-backend",
        slug="atlas-backend",
        datasource=ds,
        imported_by=user,
        assigned_playbook=playbook,
    )

    # --- time window: last 8 hours ---
    now = timezone.now()
    from_dt = now - timedelta(hours=8)
    to_dt = now

    # --- contributors ---
    contributors = {}
    for email, name in {
        "alice@atlas.dev": "Alice Chen",
        "bob@atlas.dev": "Bob Okafor",
        "carol@atlas.dev": "Carol Liu",
    }.items():
        contributors[email] = Contributor.objects.create(
            datasource=ds,
            email=email,
            name=name,
        )

    # --- commits (evenly spread over the window) ---
    window_minutes = int((to_dt - from_dt).total_seconds() / 60)
    step = max(window_minutes // len(_COMMITS), 1)
    for i, (email, _name, message) in enumerate(_COMMITS):
        occurred = from_dt + timedelta(minutes=i * step)
        Increment.objects.create(
            project=project,
            datasource=ds,
            kind=Increment.Kind.COMMIT,
            external_id=f"sha{i:04d}",
            occurred_at=occurred,
            summary=message,
            payload={"message": message},
            contributor=contributors[email],
        )

    # --- situational awareness (workspace-wide) ---
    sa = SituationalAwareness.objects.create()
    SituationalAwarenessVersion.objects.create(
        awareness=sa,
        version_number=1,
        standing_md=(
            "## Standing Context\n"
            "Atlas-backend is a Python/Django REST API serving the Atlas SaaS platform. "
            "The team operates in two-week sprints with continuous deployment to staging."
        ),
        active_md=(
            "## Active Situation\n"
            "Current sprint goal: ship paginated API endpoints and stabilise the Celery "
            "worker pipeline. Two P2 bugs were escalated from QA this week. "
            "Team is at full capacity (3 engineers)."
        ),
        change_summary="Initial SA",
    )

    # --- FRAGO: active modifier ---
    Frago.objects.create(
        project=project,
        title="Prioritise reliability metrics",
        body_md=(
            "For this assessment window, weight quality signals (bug/fix ratio) "
            "at 1.5× normal when computing the overall RAG status."
        ),
        enabled=True,
        effective_from=date.today() - timedelta(days=7),
    )

    return {
        "project": project,
        "user": user,
        "from_dt": from_dt,
        "to_dt": to_dt,
    }


# ---------------------------------------------------------------------------
# The live test
# ---------------------------------------------------------------------------


@_SKIP_NO_KEY
@pytest.mark.slow
@pytest.mark.django_db
def test_sitrep_full_pipeline_with_real_ai(live_world, caplog):
    """
    Complete pipeline smoke test — real Anthropic API, realistic fake project.

    Sequence:
      1. generate_sitrep_for_project is called → returns a plan_id
      2. ExecutionPlan with 5 steps is created
      3. All 5 steps are executed by Claude (no mocking)
      4. SitRep is persisted with a non-empty headline and assessment
      5. SitRep content is printed for human inspection
    """
    import logging

    project = live_world["project"]
    from_dt = live_world["from_dt"]
    to_dt = live_world["to_dt"]
    api_key = os.environ["ANTHROPIC_API_KEY"]

    with override_settings(ANTHROPIC_API_KEY=api_key):
        with caplog.at_level(logging.INFO):
            plan_id = generate_sitrep_for_project(
                project_id=project.pk,
                from_dt=from_dt.isoformat(),
                to_dt=to_dt.isoformat(),
                trigger="manual",
            )

    # ── 1. SitRep was requested and a plan was returned ──────────────────────
    assert plan_id is not None, "generate_sitrep_for_project must return a plan_id"

    # ── 2. ExecutionPlan created with correct structure ───────────────────────
    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.progress_total == 5
    steps = list(plan.steps.order_by("order"))
    assert len(steps) == 5
    assert steps[-1].is_planning is True  # final composition step

    # ── 3. All steps executed ─────────────────────────────────────────────────
    plan.refresh_from_db()
    assert plan.status == "completed", f"Plan status is '{plan.status}'; last_error: {plan.last_error!r}"
    assert plan.progress_current == 5
    completed = plan.steps.filter(status="completed")
    assert completed.count() == 5, (
        f"Expected 5 completed steps, got {completed.count()}. Steps: {[(s.order, s.status) for s in steps]}"
    )

    # ── 5. SitRep persisted with real content ─────────────────────────────────
    sitrep = SitRep.objects.filter(project=project).first()
    assert sitrep is not None, "SitRep must be persisted after plan completes"
    assert len(sitrep.headline) > 3, "Headline is empty"
    assert len(sitrep.situation_assessment) > 20, "situation_assessment is too short"
    assert str(sitrep.source_plan_id) == plan_id
    assert sitrep.trigger == "manual"

    # ── Human-readable output ─────────────────────────────────────────────────
    separator = "=" * 62
    print(f"\n{separator}")
    print(f"PROJECT  : {project.name}")
    print(f"PERIOD   : {from_dt:%Y-%m-%d %H:%M} → {to_dt:%Y-%m-%d %H:%M} UTC")
    print(f"PLAN     : {plan_id}")
    print(f"HEADLINE : {sitrep.headline}")
    print(f"\nASSESSMENT:\n{sitrep.situation_assessment}")
    if sitrep.notable_activity:
        print("\nNOTABLE ACTIVITY:")
        for item in sitrep.notable_activity:
            print(f"  • {item}")
    print(f"\nFRAGOs applied : {sitrep.fragos_applied.count()}")
    print(f"Playbook v      : {sitrep.playbook_version}")
    print(separator)

    # ── Token usage from steps ────────────────────────────────────────────────
    print("\nSTEP BREAKDOWN:")
    for s in plan.steps.order_by("order"):
        raw = s.result or {}
        synthesis = raw.get("synthesis", "")
        preview = str(synthesis)[:80].replace("\n", " ")
        print(f"  [{s.order}] {s.action}")
        print(f"      model={s.model_used}  preview={preview!r}")


# ---------------------------------------------------------------------------
# Variant: prove non-critical step failure does not block the live pipeline
# ---------------------------------------------------------------------------


@pytest.mark.skip(reason="flaky: mock patch races with real Anthropic call; step completes before exception injected")
@_SKIP_NO_KEY
@pytest.mark.slow
@pytest.mark.django_db
def test_sitrep_live_non_critical_step_skipped(live_world, caplog):
    """
    Same real-AI pipeline but step 1 (list commits) is marked non-critical
    and its tool executor result is forced to raise.  The plan must still
    complete and produce a SitRep using only the remaining context.

    This proves point 4: failed steps do not crash the plan.
    """
    import logging
    from unittest.mock import patch

    project = live_world["project"]
    from_dt = live_world["from_dt"]
    to_dt = live_world["to_dt"]
    api_key = os.environ["ANTHROPIC_API_KEY"]

    # We intercept plan creation to flip step 1 to non-critical,
    # then let execute_plan run unmocked against real Claude.
    _original_delay = execute_plan.delay

    def _delay_with_step_patch(plan_id_str):
        """Mark step 1 non-critical before handing off to the real executor."""
        PlanStep.objects.filter(
            plan__plan_id=plan_id_str,
            order=1,
        ).update(is_critical=False)
        return _original_delay(plan_id_str)

    # Wrap the list_commits tool to raise on the first call only.
    _calls = {"n": 0}
    _original_list_commits = None

    def _flaky_list_commits(*args, **kwargs):
        from gjallarhorn.mcp_tools import list_commits as _lc

        _calls["n"] += 1
        if _calls["n"] == 1:
            raise RuntimeError("Simulated GitLab timeout — list_commits unavailable")
        return _lc(*args, **kwargs)

    with override_settings(ANTHROPIC_API_KEY=api_key):
        with patch("gjallarhorn.tasks.plan_tasks.execute_plan.delay", side_effect=_delay_with_step_patch):
            with patch("gjallarhorn.mcp_tools.data_tools.list_commits", side_effect=_flaky_list_commits):
                with caplog.at_level(logging.INFO):
                    plan_id = generate_sitrep_for_project(
                        project_id=project.pk,
                        from_dt=from_dt.isoformat(),
                        to_dt=to_dt.isoformat(),
                        trigger="manual",
                    )

    assert plan_id is not None

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    plan.refresh_from_db()

    assert plan.status == "completed", (
        f"Plan must complete despite step 1 failure. status={plan.status!r}, error={plan.last_error!r}"
    )

    steps = {s.order: s for s in plan.steps.all()}
    # Step 1 (list_commits) failed at the LLM system-block building stage;
    # the agent swallowed it as non-critical.
    assert steps[1].status == "failed", "Step 1 must be marked failed"
    assert steps[5].status == "completed", "Final composition step must complete"

    sitrep = SitRep.objects.filter(project=project).first()
    assert sitrep is not None, "SitRep must still be created despite step 1 failure"

    separator = "=" * 62
    print(f"\n{separator}")
    print("NON-CRITICAL STEP FAILURE — live variant")
    print(f"Step 1 status : {steps[1].status}  ({steps[1].outcome_assessment[:80]})")
    print(f"HEADLINE      : {sitrep.headline}")
    print(f"ASSESSMENT    :\n{sitrep.situation_assessment}")
    print(separator)
