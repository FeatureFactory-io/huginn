"""Work-items SitRep pipeline — full stack, real Anthropic API.

Seeds ingested UnitOfWork + Milestone rows (no GitLab HTTP mocks) and runs the
real generate_sitrep_for_project → execute_plan → ToolExecutor → Claude path.

Requires ANTHROPIC_API_KEY. Skipped in CI without key.
Run: pytest tests/integration/test_work_items_pipeline_e2e.py -v -s
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
from ingestion.models import Contributor, Increment, Milestone, UnitOfWork
from sitrep.models import SitRep, VariableDatapoint
from tests.factories import (
    DataSourceFactory,
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
    UserFactory,
)

_SKIP_NO_KEY = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — skipping live work-items pipeline test",
)

_ROE_VARIABLES = [
    ("Throughput", "TP", "items", "Count issues closed in period", "Green if >= 1"),
    ("Rework", "RW", "ratio", "Reopened issues / total issues", "Green if no reopen"),
]

_COMMITS = [
    ("dev@huginn.local", "Dev One", "feat(api): add endpoint"),
    ("other@huginn.local", "Dev Two", "fix(auth): session cache"),
]


@pytest.fixture()
def work_items_pipeline_world(db):
    """Project with RoE variables, commits, issues, MRs, and milestones in window."""
    user = UserFactory()
    ds = DataSourceFactory()
    roe = RulesOfEngagementFactory(name="Work Items RoE")
    version = RulesOfEngagementVersionFactory(
        roe=roe,
        version_number=1,
        workflow_md="Assess delivery from commits and ingested GitLab work items.",
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
        name="work-items-e2e",
        slug="work-items-e2e",
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
            external_id=f"wi-e2e-sha{i:04d}",
            occurred_at=from_dt + timedelta(minutes=i * step),
            summary=message,
            payload={"message": message},
            contributor=contributors[email],
        )

    active_ms = Milestone.objects.create(
        project=project,
        datasource=ds,
        external_id="ms-active",
        title="Sprint Alpha",
        state="active",
        updated_at=from_dt + timedelta(hours=1),
        payload={"web_url": "https://gitlab.com/g/p/-/milestones/1"},
    )
    Milestone.objects.create(
        project=project,
        datasource=ds,
        external_id="ms-closed",
        title="Sprint Zero",
        state="closed",
        updated_at=from_dt + timedelta(hours=2),
        payload={"web_url": "https://gitlab.com/g/p/-/milestones/0"},
    )

    UnitOfWork.objects.create(
        project=project,
        datasource=ds,
        kind=UnitOfWork.Kind.ISSUE,
        external_id="issue-101",
        iid=12,
        title="Fix login redirect",
        state="closed",
        milestone=active_ms,
        assignee=contributors["dev@huginn.local"],
        labels=["bug"],
        created_at=from_dt,
        updated_at=from_dt + timedelta(hours=3),
        closed_at=from_dt + timedelta(hours=4),
        payload={"web_url": "https://gitlab.com/g/p/-/issues/12"},
    )
    UnitOfWork.objects.create(
        project=project,
        datasource=ds,
        kind=UnitOfWork.Kind.MERGE_REQUEST,
        external_id="mr-202",
        iid=5,
        title="Add pagination API",
        state="merged",
        milestone=active_ms,
        assignee=contributors["other@huginn.local"],
        labels=["feature"],
        created_at=from_dt + timedelta(hours=1),
        updated_at=from_dt + timedelta(hours=5),
        closed_at=from_dt + timedelta(hours=5),
        payload={"web_url": "https://gitlab.com/g/p/-/merge_requests/5"},
    )

    return {
        "project": project,
        "from_dt": from_dt,
        "to_dt": to_dt,
        "variable_count": len(_ROE_VARIABLES),
        "issue_external_id": "issue-101",
        "mr_external_id": "mr-202",
        "milestone_title": "Sprint Alpha",
    }


@_SKIP_NO_KEY
@pytest.mark.slow
@pytest.mark.django_db
def test_full_work_items_pipeline_integration(work_items_pipeline_world):
    """Real stack: data steps 1–7 complete with ingested work-item payloads."""
    project = work_items_pipeline_world["project"]
    from_dt = work_items_pipeline_world["from_dt"]
    to_dt = work_items_pipeline_world["to_dt"]
    n_vars = work_items_pipeline_world["variable_count"]
    expected_steps = 7 + n_vars + 1
    api_key = os.environ["ANTHROPIC_API_KEY"]

    with override_settings(ANTHROPIC_API_KEY=api_key):
        plan_id = generate_sitrep_for_project(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="manual",
        )

    assert plan_id is not None

    plan = ExecutionPlan.objects.get(plan_id=plan_id)
    assert plan.status == "completed", f"plan failed: {plan.last_error!r}"
    assert plan.progress_current == expected_steps

    data_steps = list(plan.steps.filter(is_planning=False, is_variable_assessment=False).order_by("order"))
    assert len(data_steps) == 7
    for step in data_steps:
        assert step.status == "completed"
        assert step.result is not None
        assert step.result.get("success") is True

    issues_step = plan.steps.get(order=5)
    issues_payload = issues_step.result.get("result") or []
    issue_ids = {row["external_id"] for row in issues_payload}
    assert work_items_pipeline_world["issue_external_id"] in issue_ids

    milestones_step = plan.steps.get(order=6)
    ms_titles = {row["title"] for row in (milestones_step.result.get("result") or [])}
    assert work_items_pipeline_world["milestone_title"] in ms_titles

    mrs_step = plan.steps.get(order=7)
    mr_ids = {row["external_id"] for row in (mrs_step.result.get("result") or [])}
    assert work_items_pipeline_world["mr_external_id"] in mr_ids

    assert plan.steps.filter(is_variable_assessment=True, status="completed").count() == n_vars

    sitrep = SitRep.objects.filter(source_plan=plan).first()
    assert sitrep is not None
    assert sitrep.headline
    assert len(VariableDatapoint.objects.filter(sitrep=sitrep)) == n_vars
