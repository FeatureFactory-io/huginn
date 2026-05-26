"""Variables pipeline integration — full stack, real Anthropic API.

No agent mocking, no manual PlanStep injection, no _persist_variable_datapoints shortcuts.
Runs: generate_sitrep_for_project → execute_plan → create_agent → ToolExecutor →
MCP tools → ClaudeLLM → _persist_sitrep_from_plan → VariableDatapoint rows.

Requires ANTHROPIC_API_KEY (from .env or environment). Skipped in CI without key.
Run: pytest tests/integration/test_variables_pipeline_e2e.py -v -s
"""

import os
from datetime import timedelta
from pathlib import Path

import pytest
from django.test import override_settings
from django.utils import timezone

try:
    from dotenv import load_dotenv as _load_dotenv

    _load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)
except ImportError:
    pass

from gjallarhorn.models import ExecutionPlan
from gjallarhorn.tasks.sitrep_tasks import generate_sitrep_for_project
from ingestion.models import Contributor, Increment
from sitrep.models import SitRep, VariableDatapoint
from tests.factories import (
    DataSourceFactory,
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
    UserFactory,
)
from ui.services.variable_datapoints_service import get_latest_datapoints

_SKIP_NO_KEY = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live variables pipeline test",
)

# Seven variables — same shape as production FeatureFactory RoE seed.
_ROE_VARIABLES = [
    ("Transparency", "T", "hours", "Hours since last ingested increment", "Green if < 24h"),
    ("Throughput", "TP", "commits", "Count commits in period", "Green if >= 5"),
    ("Cycle & Lead Time", "CLT", "days", "Median days commit to merge", "Green if < 5 days"),
    ("Rework", "RW", "ratio", "Fix commits / total commits", "Green if < 0.2"),
    ("Quality", "Q", "score", "Defect signals in commit messages", "Green if no fix/revert"),
    ("Complexity", "CX", "areas", "Distinct commit topic areas", "Green if <= 2 areas"),
    ("Contribution", "CON", "contributors", "Active contributors in period", "Green if >= 2"),
]

_COMMITS = [
    ("dev@huginn.local", "Dev One", "feat(api): add paginated projects endpoint"),
    ("dev@huginn.local", "Dev One", "fix(auth): resolve session cache expiry"),
    ("dev@huginn.local", "Dev One", "test(api): pagination edge cases"),
    ("other@huginn.local", "Dev Two", "refactor(db): repository pattern"),
    ("other@huginn.local", "Dev Two", "docs: update architecture notes"),
]


@pytest.fixture()
def variables_pipeline_world(db):
    """Project with 7 RoE variables, commits in window, ready for SitRep generation."""
    user = UserFactory()
    ds = DataSourceFactory()
    roe = RulesOfEngagementFactory(name="FeatureFactory RoE")
    version = RulesOfEngagementVersionFactory(
        roe=roe,
        version_number=1,
        workflow_md="Assess delivery health from commits in the reporting window.",
    )
    for sort_order, (name, abbrev, y_axis, calculating, interpreting) in enumerate(_ROE_VARIABLES, start=1):
        RulesOfEngagementVariableFactory(
            roe_version=version,
            sort_order=sort_order,
            name=name,
            abbrev=abbrev,
            y_axis_label=y_axis,
            calculating=calculating,
            interpreting=interpreting,
        )

    project = ProjectFactory(
        name="variables-e2e",
        slug="variables-e2e",
        datasource=ds,
        imported_by=user,
        assigned_roe=roe,
    )

    now = timezone.now()
    from_dt = now - timedelta(hours=8)
    to_dt = now

    contributors = {}
    for email, name in {c[0]: c[1] for c in _COMMITS}.items():
        contributors[email] = Contributor.objects.create(datasource=ds, email=email, name=name)

    window_minutes = max(int((to_dt - from_dt).total_seconds() / 60), 1)
    step = max(window_minutes // len(_COMMITS), 1)
    for i, (email, _name, message) in enumerate(_COMMITS):
        Increment.objects.create(
            project=project,
            datasource=ds,
            kind=Increment.Kind.COMMIT,
            external_id=f"var-e2e-sha{i:04d}",
            occurred_at=from_dt + timedelta(minutes=i * step),
            summary=message,
            payload={"message": message},
            contributor=contributors[email],
        )

    return {
        "project": project,
        "user": user,
        "version": version,
        "from_dt": from_dt,
        "to_dt": to_dt,
        "variable_count": len(_ROE_VARIABLES),
    }


@_SKIP_NO_KEY
@pytest.mark.slow
@pytest.mark.django_db
def test_full_variables_pipeline_integration(variables_pipeline_world):
    """Full integration: Celery task → agent → real Claude → datapoints + snapshot + service."""
    project = variables_pipeline_world["project"]
    from_dt = variables_pipeline_world["from_dt"]
    to_dt = variables_pipeline_world["to_dt"]
    n_vars = variables_pipeline_world["variable_count"]
    expected_steps = 4 + n_vars + 1  # data + variable assessments + narrative
    api_key = os.environ["ANTHROPIC_API_KEY"]

    with override_settings(ANTHROPIC_API_KEY=api_key):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    assert plan_id is not None, "generate_sitrep_for_project must return a plan_id"

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.status == "completed", f"plan failed: {plan.last_error!r}"
    assert plan.progress_current == expected_steps
    assert plan.steps.filter(is_variable_assessment=True).count() == n_vars
    assert plan.steps.filter(is_variable_assessment=True, status="completed").count() == n_vars

    sitrep = SitRep.objects.filter(source_plan=plan).first()
    assert sitrep is not None, "SitRep must be persisted from completed plan"
    assert sitrep.headline
    assert sitrep.situation_assessment

    datapoints = list(VariableDatapoint.objects.filter(sitrep=sitrep).order_by("roe_variable__sort_order"))
    assert len(datapoints) == n_vars, (
        f"expected {n_vars} VariableDatapoint rows, got {len(datapoints)}: "
        f"{[(d.variable_name, d.value, d.color) for d in datapoints]}"
    )

    for dp in datapoints:
        assert dp.color in ("green", "orange", "red", "grey")
        assert dp.variable_name
        assert dp.roe_variable_id is not None
        assert dp.source_plan_step_id is not None

    sitrep.refresh_from_db()
    assert len(sitrep.variables_snapshot) == n_vars
    snapshot_names = {entry["variable_name"] for entry in sitrep.variables_snapshot}
    assert snapshot_names == {name for name, *_ in _ROE_VARIABLES}
    for entry in sitrep.variables_snapshot:
        assert entry["color"] in ("green", "orange", "red", "grey")
        assert "abbrev" in entry
        assert "y_axis_label" in entry

    latest = get_latest_datapoints(project.pk)
    assert len(latest) == n_vars
    latest_by_name = {row["variable_name"]: row for row in latest}
    for name, abbrev, y_axis, *_ in _ROE_VARIABLES:
        row = latest_by_name[name]
        assert row["abbrev"] == abbrev
        assert row["y_axis_label"] == y_axis
        assert row["color"] in ("green", "orange", "red", "grey")
        # Latest service row must reflect the SitRep we just generated.
        assert row["to_dt"] == sitrep.to_dt
