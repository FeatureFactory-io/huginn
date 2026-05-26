"""SitRep service — build canonical narrative plan steps and persist from plan."""

import logging
import re

logger = logging.getLogger(__name__)

DATAPOINT_VALUE_MAX_LENGTH = 64


def _normalize_datapoint_value(value) -> str | None:
    """Coerce LLM output to a string that fits VariableDatapoint.value (varchar 64)."""
    if value is None:
        return None
    text = str(value)
    if len(text) <= DATAPOINT_VALUE_MAX_LENGTH:
        return text
    logger.warning(
        "Truncating variable value from %d to %d chars: %.40s…",
        len(text),
        DATAPOINT_VALUE_MAX_LENGTH,
        text,
    )
    return text[:DATAPOINT_VALUE_MAX_LENGTH]


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
    """Return the canonical narrative plan steps for SitRep generation.

    Steps 1–4 are pure data-collection steps (tool calls, no LLM).
    Steps 5–N are Variable assessment steps (one per RoE Variable, using execution model).
    Final step is the narrative-composition step (LLM call using planning model).

    Total: 4 + N + 1, where N = number of Variables (0 if no RoE or no Variables).
    """
    from gjallarhorn.mcp_tools.roe_tools import get_roe_variables  # noqa: PLC0415

    steps = [
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
    ]

    # Insert Variable assessment steps between data-collection and narrative
    roe_variables = get_roe_variables(project.pk) if project else None
    if roe_variables:
        for idx, var in enumerate(roe_variables, start=5):
            steps.append(
                {
                    "order": idx,
                    "action": f"Assess {var['name']} ({var['abbrev']})",
                    "tool": "",
                    "reasoning_why_needed": f"Compute variable value using: {var['calculating'][:100]}...",
                    "expected_outcome": '{"value": "...", "color": "green|orange|red|grey"}',
                    "is_planning": False,
                    "is_variable_assessment": True,
                }
            )

    # Final step: narrative composition (always last, order = 4 + N + 1)
    final_order = len(steps) + 1
    datapoints_note = (
        ', "datapoints": [{"variable_name": "...", "abbrev": "...", "y_axis_label": "...", "value": "...", "color": "..."}]'
        if roe_variables
        else ""
    )
    steps.append(
        {
            "order": final_order,
            "action": "Compose SitRep narrative",
            "tool": "",
            "reasoning_why_needed": "Synthesise all collected data into headline + assessment.",
            "expected_outcome": '{"headline": "...", "situation_assessment": "...", "notable_activity": [...]'
            + datapoints_note
            + "}",
            "is_planning": True,
        }
    )

    return steps


def _persist_sitrep_from_plan(plan):
    """Parse the final step result and write a SitRep row.

    On missing required field, marks the plan as failed and raises ValueError.
    """
    import json as _json  # noqa: PLC0415 — used for JSONDecodeError type reference

    from django.db import transaction  # noqa: PLC0415

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

    # Idempotent: if a SitRep already exists for this (project, to_dt) window, refresh variables.
    existing = SitRep.objects.filter(project=project, to_dt=plan.sitrep_to_dt).first()
    if existing:
        _persist_variable_datapoints(existing, plan)
        return existing

    fragos = Frago.objects.filter(project=project, enabled=True)

    roe_version = None
    if project.assigned_roe:
        pv = project.assigned_roe.versions.first()
        if pv:
            roe_version = pv.version_number

    mode = getattr(project, "gjallarhorn_mode", "semi_auto") or "semi_auto"

    with transaction.atomic():
        sitrep = SitRep.objects.create(
            project=project,
            from_dt=plan.sitrep_from_dt,
            to_dt=plan.sitrep_to_dt,
            trigger=plan.sitrep_trigger or "automatic",
            mode_at_generation=mode,
            roe_version=roe_version,
            headline=result["headline"],
            situation_assessment=result["situation_assessment"],
            notable_activity=result.get("notable_activity", []),
            source_plan=plan,
        )
        sitrep.fragos_applied.set(fragos)
        _persist_variable_datapoints(sitrep, plan)

    logger.info("plan=%s sitrep=%s created (headline=%r)", plan.plan_id, sitrep.pk, sitrep.headline)
    return sitrep


def _persist_variable_datapoints(sitrep, plan):
    """Persist VariableDatapoint rows and SitRep.variables_snapshot from variable assessment steps."""
    from sitrep.models import VariableDatapoint  # noqa: PLC0415

    variable_steps = [s for s in plan.steps.all() if s.is_variable_assessment]
    if not variable_steps:
        return

    project = sitrep.project
    roe = project.assigned_roe
    if not roe:
        logger.warning(
            "plan=%s sitrep=%s has %d variable steps but project has no assigned RoE — skipping datapoints",
            plan.plan_id,
            sitrep.pk,
            len(variable_steps),
        )
        return

    roe_version = roe.versions.first()
    if not roe_version:
        logger.warning(
            "plan=%s sitrep=%s has variable steps but RoE has no version — skipping datapoints",
            plan.plan_id,
            sitrep.pk,
        )
        return

    datapoints = []
    skipped = 0

    for step in variable_steps:
        if not step.result:
            skipped += 1
            logger.warning(
                "plan=%s sitrep=%s variable step %s (%s) has no result — skipping",
                plan.plan_id,
                sitrep.pk,
                step.order,
                step.action,
            )
            continue

        result_data = step.result if isinstance(step.result, dict) else {}
        value = _normalize_datapoint_value(result_data.get("value"))
        color = result_data.get("color", "grey")

        if color not in ("green", "orange", "red", "grey"):
            color = "grey"

        # Extract variable name from action: "Assess {name} ({abbrev})"
        import re

        match = re.match(r"Assess (.+?) \((.+?)\)", step.action)
        if not match:
            skipped += 1
            logger.warning(
                "plan=%s sitrep=%s cannot parse variable name from action %r — skipping",
                plan.plan_id,
                sitrep.pk,
                step.action,
            )
            continue

        variable_name = match.group(1)
        abbrev = match.group(2)

        # Find the RoE variable
        roe_var = roe_version.variables.filter(name=variable_name).first()
        if not roe_var:
            skipped += 1
            logger.warning(
                "plan=%s sitrep=%s RoE variable %r not found for step %s — skipping",
                plan.plan_id,
                sitrep.pk,
                variable_name,
                step.order,
            )
            continue

        y_axis_label = roe_var.y_axis_label

        # Create or update the datapoint
        datapoint, created = VariableDatapoint.objects.get_or_create(
            sitrep=sitrep,
            roe_variable=roe_var,
            defaults={
                "variable_name": variable_name,
                "y_axis_label": y_axis_label,
                "value": value,
                "color": color,
                "from_dt": sitrep.from_dt,
                "to_dt": sitrep.to_dt,
                "source_plan_step": step,
            },
        )

        if not created:
            # Idempotent update
            datapoint.value = value
            datapoint.color = color
            datapoint.source_plan_step = step
            datapoint.save(update_fields=["value", "color", "source_plan_step"])

        # Build snapshot entry
        datapoints.append(
            {
                "variable_name": variable_name,
                "abbrev": abbrev,
                "y_axis_label": y_axis_label,
                "value": value,
                "color": color,
            }
        )

    # Write variables_snapshot to SitRep
    if datapoints:
        sitrep.variables_snapshot = datapoints
        sitrep.save(update_fields=["variables_snapshot"])
    elif skipped:
        logger.warning(
            "plan=%s sitrep=%s persisted 0/%d variable datapoints (%d skipped)",
            plan.plan_id,
            sitrep.pk,
            len(variable_steps),
            skipped,
        )
