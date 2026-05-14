"""SitRep service — build canonical narrative plan steps and persist from plan."""


def build_narrative_plan_steps(project, from_dt, to_dt) -> list[dict]:
    """Return the 5 canonical narrative plan steps for SitRep generation."""
    return [
        {
            "order": 1,
            "action": "Get commits for period",
            "reasoning_why_needed": "Establish what changed in this window.",
            "expected_outcome": "List of commits with author and message.",
            "is_planning": False,
        },
        {
            "order": 2,
            "action": "Get contributor activity for period",
            "reasoning_why_needed": "Identify unusual contribution patterns.",
            "expected_outcome": "Per-contributor commit counts.",
            "is_planning": False,
        },
        {
            "order": 3,
            "action": "Load active FRAGOs in window",
            "reasoning_why_needed": "FRAGOs modify assessment scope.",
            "expected_outcome": "List of active FRAGOs at to_dt.",
            "is_planning": False,
        },
        {
            "order": 4,
            "action": "Load Situational Awareness",
            "reasoning_why_needed": "Commander context shapes the narrative.",
            "expected_outcome": "Current SA capsule.",
            "is_planning": False,
        },
        {
            "order": 5,
            "action": "Compose SitRep narrative",
            "reasoning_why_needed": "Synthesise all context into headline + assessment.",
            "expected_outcome": '{"headline": "...", "situation_assessment": "...", "notable_activity": [...]}',
            "is_planning": True,
        },
    ]


def _persist_sitrep_from_plan(plan):
    """Parse the final step result and write a SitRep row.

    On missing required field, marks the plan as failed and raises ValueError.
    """
    import json as _json  # noqa: PLC0415

    from sitrep.models import Frago, SitRep  # noqa: PLC0415

    final_step = plan.steps.order_by("-order").first()
    raw = final_step.result if final_step and final_step.result else {}

    # execute_single_step wraps the LLM response as {"tool_results": ..., "synthesis": "<json>"}
    # Fall back to treating raw itself as the narrative dict (e.g. direct unit-test fixtures).
    if isinstance(raw, dict) and "synthesis" in raw:
        synthesis = raw["synthesis"]
        try:
            result = _json.loads(synthesis) if isinstance(synthesis, str) else synthesis
        except (_json.JSONDecodeError, TypeError):
            result = raw
    else:
        result = raw

    for required in ("headline", "situation_assessment"):
        if required not in result:
            exc = ValueError(f"missing field: {required}")
            plan.mark_failed(exc)
            raise exc

    project = plan.conversation.project

    # Idempotent: if a SitRep already exists for this (project, to_dt) window, return it.
    existing = SitRep.objects.filter(project=project, to_dt=plan.sitrep_to_dt).first()
    if existing:
        return existing

    fragos = Frago.objects.filter(project=project, enabled=True)

    playbook_version = None
    if project.assigned_playbook:
        pv = project.assigned_playbook.versions.first()
        if pv:
            playbook_version = pv.version_number

    mode = getattr(project, "gjallarhorn_mode", "semi_auto") or "semi_auto"

    sitrep = SitRep.objects.create(
        project=project,
        from_dt=plan.sitrep_from_dt,
        to_dt=plan.sitrep_to_dt,
        trigger=plan.sitrep_trigger or "automatic",
        mode_at_generation=mode,
        playbook_version=playbook_version,
        headline=result["headline"],
        situation_assessment=result["situation_assessment"],
        notable_activity=result.get("notable_activity", []),
        source_plan=plan,
    )
    sitrep.fragos_applied.set(fragos)
    return sitrep
