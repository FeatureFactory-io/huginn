"""SitRep service — narrative plan step definitions and persistence."""

import logging

logger = logging.getLogger("gjallarhorn.sitrep")


def _persist_sitrep_from_plan(plan):
    """Parse the final PlanStep result and create a SitRep row.

    Expects the last completed step's result dict to contain:
        headline (str), situation_assessment (str), notable_activity (list, optional)

    Raises ValueError and marks plan.status = 'failed' if headline is missing.
    """
    from sitrep.models import Frago, SitRep

    last_step = plan.steps.filter(status="completed").order_by("-order").first()

    if last_step is None or not last_step.result:
        plan.mark_failed(ValueError("No completed step with result found"))
        raise ValueError("No completed step with result found")

    import json

    result = last_step.result
    headline = result.get("headline", "")
    situation_assessment = result.get("situation_assessment", "")
    notable_activity = result.get("notable_activity", [])

    if not headline:
        content = result.get("content", "")
        try:
            parsed = json.loads(content) if isinstance(content, str) else {}
            headline = parsed.get("headline", "")
            situation_assessment = parsed.get("situation_assessment", situation_assessment or content)
            notable_activity = parsed.get("notable_activity", notable_activity)
        except (json.JSONDecodeError, AttributeError):
            pass

    if not headline:
        exc = ValueError("Final step result missing 'headline'")
        plan.mark_failed(exc)
        raise exc

    project = plan.conversation.project

    pb_version = None
    if project.assigned_playbook:
        from playbooks.models import PlaybookVersion

        pv = PlaybookVersion.objects.filter(playbook=project.assigned_playbook).order_by("-version_number").first()
        if pv:
            pb_version = pv.version_number

    sitrep, _ = SitRep.objects.get_or_create(
        project=project,
        to_dt=plan.sitrep_to_dt,
        defaults={
            "from_dt": plan.sitrep_from_dt,
            "trigger": plan.sitrep_trigger or "automatic",
            "mode_at_generation": "semi_auto",
            "playbook_version": pb_version,
            "headline": headline,
            "situation_assessment": situation_assessment,
            "notable_activity": notable_activity,
            "source_plan": plan,
        },
    )

    active_fragos = Frago.objects.filter(
        project=project,
        enabled=True,
    )
    sitrep.fragos_applied.set(active_fragos)

    return sitrep


def build_narrative_plan_steps(project, from_dt, to_dt) -> list[dict]:
    """Return the 5 canonical PlanStep dicts for SitRep narrative generation.

    Args:
        project: Project instance (reserved for future filtering)
        from_dt: Period start datetime
        to_dt: Period end datetime

    Returns:
        List of 5 dicts with keys: order, action, reasoning_why_needed, expected_outcome
    """
    return [
        {
            "order": 1,
            "action": "Fetch commits for the assessed period from the project repository",
            "reasoning_why_needed": (
                "Commit data is the primary factual record of what happened in the assessed window."
            ),
            "expected_outcome": ("A list of commits with author, timestamp, and message within the period."),
        },
        {
            "order": 2,
            "action": "Fetch contributor activity summary for the assessed period",
            "reasoning_why_needed": (
                "Understanding who contributed and how much reveals team health and workload distribution."
            ),
            "expected_outcome": ("Aggregated commit counts per contributor, sorted by activity level."),
        },
        {
            "order": 3,
            "action": "Retrieve active Playbook workflow, active FRAGOs, and Situational Awareness context",
            "reasoning_why_needed": (
                "The Playbook defines the standards for assessment; "
                "FRAGOs provide current doctrine overrides; SA frames the broader context."
            ),
            "expected_outcome": ("Active Playbook workflow text, enabled in-window FRAGOs, and current SA capsule."),
        },
        {
            "order": 4,
            "action": "Analyse project activity against Playbook standards and identify key findings",
            "reasoning_why_needed": (
                "Synthesising raw data against doctrine surfaces compliance status and notable patterns."
            ),
            "expected_outcome": (
                "A structured analysis identifying overall status and key observations from the period."
            ),
        },
        {
            "order": 5,
            "action": "Compose the SitRep narrative with headline and situation assessment prose",
            "reasoning_why_needed": (
                "The final narrative communicates the assessed situation to the Commander in actionable prose."
            ),
            "expected_outcome": (
                "A complete SitRep narrative with a one-sentence headline and a situation_assessment paragraph."
            ),
        },
    ]
