"""SitRep generation Celery task and sync signal receiver."""

import logging

from celery import shared_task
from django.db import transaction

from ingestion.models import Increment, Project
from ingestion.signals import sync_project_completed

logger = logging.getLogger("gjallarhorn.sitrep")


@shared_task(name="gjallarhorn.generate_sitrep_for_project")
def generate_sitrep_for_project(project_id, from_dt, to_dt, trigger="automatic"):
    """Create an ExecutionPlan that generates a SitRep for the given period.

    Args:
        project_id: PK of the Project
        from_dt: ISO-format string or datetime — start of assessed period
        to_dt: ISO-format string or datetime — end of assessed period (usually sync time)
        trigger: 'automatic' or 'manual'
    """
    from django.utils import timezone
    from django.utils.dateparse import parse_datetime

    from gjallarhorn.models import Conversation
    from gjallarhorn.services.sitrep_service import build_narrative_plan_steps
    from sitrep.models import SitRep

    project = Project.objects.select_related("assigned_playbook", "imported_by").get(pk=project_id)

    if not project.assigned_playbook:
        logger.warning("generate_sitrep_for_project: project %s has no playbook, skipping", project.slug)
        return None

    to_dt_parsed = parse_datetime(to_dt) if isinstance(to_dt, str) else to_dt
    from_dt_parsed = parse_datetime(from_dt) if isinstance(from_dt, str) else from_dt

    if to_dt_parsed and timezone.is_naive(to_dt_parsed):
        to_dt_parsed = timezone.make_aware(to_dt_parsed)
    if from_dt_parsed and timezone.is_naive(from_dt_parsed):
        from_dt_parsed = timezone.make_aware(from_dt_parsed)

    # Idempotency guard (automatic only)
    if trigger == "automatic":
        existing = SitRep.objects.filter(project=project, to_dt=to_dt_parsed).first()
        if existing:
            logger.info(
                "generate_sitrep_for_project: SitRep already exists for %s to_dt=%s, returning existing plan",
                project.slug,
                to_dt_parsed,
            )
            return str(existing.source_plan_id) if existing.source_plan_id else None

    user = project.imported_by
    if user is None:
        logger.warning("generate_sitrep_for_project: project %s has no imported_by user, skipping", project.slug)
        return None

    from gjallarhorn.models import ExecutionPlan, PlanStep
    from gjallarhorn.tasks.plan_tasks import execute_plan

    steps = build_narrative_plan_steps(project=project, from_dt=from_dt_parsed, to_dt=to_dt_parsed)
    goal = f"Generate SitRep for {project.slug} — {from_dt_parsed} → {to_dt_parsed}"

    with transaction.atomic():
        conversation, _ = Conversation.objects.get_or_create(
            user=user,
            project=project,
            defaults={"conversation_type": "sitrep_generation"},
        )
        plan = ExecutionPlan.objects.create(
            conversation=conversation,
            goal=goal,
            progress_total=len(steps),
            sitrep_from_dt=from_dt_parsed,
            sitrep_to_dt=to_dt_parsed,
            sitrep_trigger=trigger,
        )
        for i, step_dict in enumerate(steps, 1):
            PlanStep.objects.create(
                plan=plan,
                order=i,
                action=step_dict["action"],
                reasoning_why_needed=step_dict["reasoning_why_needed"],
                expected_outcome=step_dict["expected_outcome"],
            )

    execute_plan.delay(str(plan.plan_id))
    return str(plan.plan_id)


def create_agent_for_sitrep(project, user):
    """Build GjallarhornAgent scoped to the given project. Patched in tests."""
    from gjallarhorn.agent.agent import GjallarhornAgent
    from gjallarhorn.llm.claude import ClaudeLLM
    from gjallarhorn.services.factory import build_executor

    executor = build_executor(user=user, project=project)
    llm = ClaudeLLM()
    return GjallarhornAgent(llm=llm, tool_executor=executor)


def _resolve_from_dt(project, prior_sitrep):
    """Resolve from_dt: prior SitRep's to_dt, or earliest commit time."""

    if prior_sitrep is not None:
        return prior_sitrep.to_dt

    earliest = (
        Increment.objects.filter(project=project).order_by("occurred_at").values_list("occurred_at", flat=True).first()
    )
    return earliest


def on_sync_project_completed(sender, project, to_dt, **kwargs):
    """Signal receiver: schedule SitRep generation after a successful sync."""
    from sitrep.models import SitRep

    try:
        prior = SitRep.objects.filter(project=project).order_by("-generated_at").first()
        from_dt = _resolve_from_dt(project, prior)

        if from_dt is None:
            logger.warning("on_sync_project_completed: no commits for project %s, skipping SitRep", project.slug)
            return

        generate_sitrep_for_project.delay(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="automatic",
        )
    except Exception:
        logger.exception("on_sync_project_completed: error scheduling SitRep for %s", project.slug)


sync_project_completed.connect(on_sync_project_completed)
