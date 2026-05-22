"""Celery tasks and signal receivers for SitRep generation."""

import logging

from celery import shared_task
from django.db import transaction
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


def on_sync_project_completed(sender, project, to_dt, **kwargs):
    """Signal receiver: enqueue generate_sitrep_for_project after a successful sync.

    Wrapped in try/except so any handler failure cannot break the sync task.
    """
    try:
        from ingestion.models import Increment  # noqa: PLC0415
        from sitrep.models import SitRep  # noqa: PLC0415

        last = SitRep.objects.filter(project=project).order_by("-to_dt").first()
        if last:
            from_dt = last.to_dt
        else:
            earliest = Increment.objects.filter(project=project).order_by("occurred_at").first()
            from_dt = earliest.occurred_at if earliest else to_dt

        generate_sitrep_for_project.delay(
            project_id=project.pk,
            from_dt=from_dt.isoformat(),
            to_dt=to_dt.isoformat(),
            trigger="automatic",
        )
    except Exception:  # noqa: BLE001
        logger.exception("on_sync_project_completed: failed to enqueue generate_sitrep_for_project")


@shared_task(name="gjallarhorn.generate_sitrep_for_project")
def generate_sitrep_for_project(
    project_id: int,
    from_dt: str,
    to_dt: str,
    trigger: str = "automatic",
) -> str | None:
    """Create Conversation + ExecutionPlan + 5 PlanSteps and enqueue execute_plan.

    Returns the plan_id hex string, or None when generation is not applicable
    (no playbook assigned, or no user associated with the project).

    Idempotency: automatic triggers with an existing SitRep for the same to_dt
    return the existing plan_id without creating a new plan.
    """
    from gjallarhorn.models import Conversation, ExecutionPlan, PlanStep  # noqa: PLC0415
    from gjallarhorn.services.factory import PLANNING_MODEL  # noqa: PLC0415
    from gjallarhorn.services.sitrep_service import build_narrative_plan_steps  # noqa: PLC0415
    from gjallarhorn.tasks.plan_tasks import execute_plan  # noqa: PLC0415
    from ingestion.models import Project  # noqa: PLC0415
    from sitrep.models import SitRep  # noqa: PLC0415

    project = Project.objects.get(pk=project_id)

    if not project.assigned_playbook:
        logger.info("generate_sitrep: project=%s has no assigned playbook — skipping", project_id)
        return None

    user = project.imported_by
    if user is None:
        logger.info("generate_sitrep: project=%s has no imported_by user — skipping", project_id)
        return None

    from_dt_obj = parse_datetime(from_dt) if isinstance(from_dt, str) else from_dt
    to_dt_obj = parse_datetime(to_dt) if isinstance(to_dt, str) else to_dt

    if trigger == "automatic":
        existing = SitRep.objects.filter(project=project, to_dt=to_dt_obj).first()
        if existing and existing.source_plan_id:
            return str(existing.source_plan_id)

    conv, _ = Conversation.objects.get_or_create(
        user=user,
        project=project,
        defaults={"conversation_type": "sitrep_generation"},
    )

    steps = build_narrative_plan_steps(project, from_dt_obj, to_dt_obj)

    with transaction.atomic():
        plan = ExecutionPlan.objects.create(
            conversation=conv,
            goal=f"Generate SitRep for {project.name} ({from_dt} → {to_dt})",
            status="pending",
            progress_total=len(steps),
            sitrep_from_dt=from_dt_obj,
            sitrep_to_dt=to_dt_obj,
            sitrep_trigger=trigger,
            planning_model=PLANNING_MODEL,
        )
        for s in steps:
            PlanStep.objects.create(
                plan=plan,
                order=s["order"],
                action=s["action"],
                tool=s.get("tool", ""),
                reasoning_why_needed=s["reasoning_why_needed"],
                expected_outcome=s["expected_outcome"],
                status="pending",
                is_planning=s.get("is_planning", False),
            )

    logger.info(
        "generate_sitrep: project=%s plan=%s created (%s steps, trigger=%s, %s → %s)",
        project_id,
        plan.plan_id,
        len(steps),
        trigger,
        from_dt,
        to_dt,
    )
    execute_plan.delay(str(plan.plan_id))
    # TODO(chat-milestone): publish plan_started to Redis
    return str(plan.plan_id)
