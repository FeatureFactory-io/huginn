"""SitRep service — build canonical narrative plan steps and persist from plan."""

import logging
import re

logger = logging.getLogger(__name__)


def _extract_json(text: str) -> dict:
    """Best-effort JSON extraction from an LLM response.

    Tries in order:
    1. Direct parse (clean JSON).
    2. Strip markdown code fences (```json ... ``` or ``` ... ```).
    3. Extract the first balanced {...} block from the text.

    Raises json.JSONDecodeError if all attempts fail.
    """
    import json  # noqa: PLC0415

    # 1. Direct
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        pass

    # 2. Strip code fences
    stripped = re.sub(r"```(?:json)?\s*", "", text).strip()
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        pass

    # 3. Extract first balanced brace block
    start = text.find("{")
    if start != -1:
        depth = 0
        for i, ch in enumerate(text[start:], start):
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidate = text[start : i + 1]
                    try:
                        return json.loads(candidate)
                    except (json.JSONDecodeError, TypeError):
                        break

    return json.loads(text)  # re-raise original error


def build_narrative_plan_steps(project, from_dt, to_dt) -> list[dict]:
    """Return the 5 canonical narrative plan steps for SitRep generation.

    Steps 1–4 are pure data-collection steps (tool calls, no LLM).
    Step 5 is the single LLM call that synthesises the collected data.
    """
    return [
        {
            "order": 1,
            "action": "Get commits for period",
            "tool": "list_commits",
            "reasoning_why_needed": "Establish what changed in this window.",
            "expected_outcome": "List of commits with author and message.",
            "is_planning": False,
        },
        {
            "order": 2,
            "action": "Get contributor activity for period",
            "tool": "get_contributor_activity",
            "reasoning_why_needed": "Identify unusual contribution patterns.",
            "expected_outcome": "Per-contributor commit counts.",
            "is_planning": False,
        },
        {
            "order": 3,
            "action": "Load active FRAGOs in window",
            "tool": "list_active_fragos",
            "reasoning_why_needed": "FRAGOs modify assessment scope.",
            "expected_outcome": "List of active FRAGOs at to_dt.",
            "is_planning": False,
        },
        {
            "order": 4,
            "action": "Load Situational Awareness",
            "tool": "get_active_situational_awareness",
            "reasoning_why_needed": "Commander context shapes the narrative.",
            "expected_outcome": "Current SA capsule.",
            "is_planning": False,
        },
        {
            "order": 5,
            "action": "Compose SitRep narrative",
            "tool": "",
            "reasoning_why_needed": "Synthesise all collected data into headline + assessment.",
            "expected_outcome": '{"headline": "...", "situation_assessment": "...", "notable_activity": [...]}',
            "is_planning": True,
        },
    ]


def _persist_sitrep_from_plan(plan):
    """Parse the final step result and write a SitRep row.

    On missing required field, marks the plan as failed and raises ValueError.
    """
    import json as _json  # noqa: PLC0415 — used for JSONDecodeError type reference

    from sitrep.models import Frago, SitRep  # noqa: PLC0415

    logger.info(
        "plan=%s persisting sitrep (project=%s, to_dt=%s)",
        plan.plan_id,
        plan.conversation.project_id,
        plan.sitrep_to_dt,
    )

    final_step = plan.steps.order_by("-order").first()
    raw = final_step.result if final_step and final_step.result else {}

    # execute_single_step wraps the LLM response as {"tool_results": ..., "synthesis": "<json>"}
    # Fall back to treating raw itself as the narrative dict (e.g. direct unit-test fixtures).
    if isinstance(raw, dict) and "synthesis" in raw:
        synthesis = raw["synthesis"]
        if isinstance(synthesis, str):
            try:
                result = _extract_json(synthesis)
            except (_json.JSONDecodeError, TypeError) as exc:
                logger.warning(
                    "plan=%s step-5 synthesis is not parseable JSON (%s); raw synthesis: %.200s",
                    plan.plan_id,
                    exc,
                    synthesis,
                )
                result = raw
        else:
            result = synthesis if isinstance(synthesis, dict) else raw
    else:
        result = raw

    for required in ("headline", "situation_assessment"):
        if required not in result:
            exc = ValueError(f"missing field: {required}")
            logger.error("plan=%s cannot persist sitrep — %s", plan.plan_id, exc)
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
    logger.info("plan=%s sitrep=%s created (headline=%r)", plan.plan_id, sitrep.pk, sitrep.headline)
    return sitrep
