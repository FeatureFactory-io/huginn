"""GjallarhornAgent — create_plan, execute_single_step, process_user_message (deferred)."""

import json
import logging

from django.db import transaction

from gjallarhorn.agent.exceptions import ToolExecutionError
from gjallarhorn.agent.prompts import SITREP_NARRATIVE_SYSTEM_PROMPT
from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.llm.base import LLM
from gjallarhorn.models import ExecutionPlan, PlanStep

logger = logging.getLogger(__name__)

NARRATIVE_TOOLS: list[dict] = []


def _planning_model() -> str:
    """Lazy import to avoid circular dependency: agent → services.factory → agent."""
    from gjallarhorn.services.factory import PLANNING_MODEL  # noqa: PLC0415

    return PLANNING_MODEL


class GjallarhornAgent:
    def __init__(self, llm: LLM, tool_executor: ToolExecutor):
        self.llm = llm
        self.tool_executor = tool_executor

    def create_plan(
        self,
        conversation,
        goal: str,
        steps: list[dict],
    ) -> ExecutionPlan:
        """Persist ExecutionPlan + PlanSteps atomically, then enqueue execute_plan."""
        with transaction.atomic():
            plan = ExecutionPlan.objects.create(
                conversation=conversation,
                goal=goal,
                status="pending",
                progress_total=len(steps),
                planning_model=_planning_model(),
            )
            for i, s in enumerate(steps):
                PlanStep.objects.create(
                    plan=plan,
                    order=i + 1,
                    action=s["action"],
                    tool=s.get("tool", ""),
                    reasoning_why_needed=s["reasoning_why_needed"],
                    expected_outcome=s["expected_outcome"],
                    status="pending",
                    is_planning=s.get("is_planning", False),
                    is_variable_assessment=s.get("is_variable_assessment", False),
                )

        # Lazy import to break circular dependency: agent → tasks → agent
        from gjallarhorn.tasks.plan_tasks import execute_plan  # noqa: PLC0415

        execute_plan.delay(str(plan.plan_id))
        # TODO(chat-milestone): publish plan_started to Redis
        return plan

    def execute_single_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        """Dispatch to data-collection, variable-assessment, or planning execution based on step type.

        Data steps (is_planning=False, is_variable_assessment=False): call the registered tool directly — no LLM.
        Variable assessment steps (is_variable_assessment=True): LLM call using execution model.
        Planning step (is_planning=True): LLM call using planning model with all collected data as context.
        """
        if step.is_variable_assessment:
            self._execute_variable_assessment_step(plan, step)
        elif step.is_planning:
            self._execute_planning_step(plan, step)
        else:
            self._execute_data_step(plan, step)

    def process_user_message(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise NotImplementedError("Chat surfaces in a future milestone")

    # ------------------------------------------------------------------
    # Private: step execution
    # ------------------------------------------------------------------

    def _execute_data_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        """Call the step's registered tool and persist the result — no LLM call."""
        if not step.tool:
            logger.warning("plan=%s step %s has no tool configured — skipping data fetch", plan.plan_id, step.order)
            step.result = {"success": False, "result": None, "error": "no tool configured"}
            step.outcome_assessment = "no tool configured"
            step.status = "completed"
            step.save()
            return

        kwargs = self._resolve_tool_kwargs(step.tool, plan)
        logger.info("plan=%s step %s calling tool %r with kwargs %s", plan.plan_id, step.order, step.tool, list(kwargs))
        result = self.tool_executor.execute(step.tool, **kwargs)

        if result["success"] is False:
            if step.is_critical:
                raise ToolExecutionError(step.tool, result["error"])
            # Non-critical: mark step failed but let the plan continue.
            step.result = result
            step.outcome_assessment = f"Tool {step.tool!r}: failed — {result['error']}"
            step.status = "failed"
            step.model_used = ""
            step.save()
            return

        step.result = result
        step.outcome_assessment = f"Tool {step.tool!r}: ok"
        step.status = "completed"
        step.model_used = ""
        step.save()
        # TODO(chat-milestone): publish plan_step_update to Redis

    def _execute_planning_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        """Single LLM call: inject collected data from prior steps, produce narrative."""
        collected = self._format_collected_data(plan)
        step_prompt = (
            f"STEP GOAL: {step.action}\n"
            f"REASONING: {step.reasoning_why_needed}\n\n"
            f"COLLECTED PROJECT DATA:\n{collected}\n\n"
            "Compose the SitRep narrative now."
        )

        system_blocks = self._build_system_blocks(plan)
        messages = [{"role": "user", "content": step_prompt}]
        response = self.llm.generate_with_tools(
            messages=messages,
            tools=NARRATIVE_TOOLS,
            system_blocks=system_blocks,
        )

        # LLM tool calls are theoretically possible (NARRATIVE_TOOLS is empty today but may grow)
        tool_results = []
        for tool_call in response.tool_calls:
            result = self.tool_executor.execute(tool_call["name"], **tool_call["input"])
            if result["success"] is False:
                raise ToolExecutionError(tool_call["name"], result["error"])
            tool_results.append({"tool": tool_call["name"], "result": result["result"]})

        step.result = {"tool_results": tool_results, "synthesis": response.content}
        step.outcome_assessment = response.content
        step.status = "completed"
        step.model_used = response.model or ""
        step.save()
        # TODO(chat-milestone): publish plan_step_update to Redis

    def _execute_variable_assessment_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        """Execute a variable assessment step: LLM call using execution model (Sonnet).

        Gathers collected data from prior steps, adds variable-specific context
        (calculating + interpreting rules), and asks the LLM to compute the variable value.
        On parse error, defaults to value=None, color='grey' without failing the plan.
        """
        from gjallarhorn.mcp_tools.roe_tools import get_roe_variables  # noqa: PLC0415

        # Get variable definition
        project = plan.conversation.project
        roe_variables = get_roe_variables(project.pk)
        if not roe_variables:
            step.result = {"value": None, "color": "grey"}
            step.outcome_assessment = "No RoE variables configured"
            step.status = "completed"
            step.model_used = ""
            step.save()
            return

        # Extract variable name from action: "Assess {name} ({abbrev})"
        import re

        match = re.match(r"Assess (.+?) \((.+?)\)", step.action)
        if not match:
            step.result = {"value": None, "color": "grey"}
            step.outcome_assessment = "Could not parse variable name from action"
            step.status = "completed"
            step.model_used = ""
            step.save()
            return

        variable_name = match.group(1)

        var_def = next((v for v in roe_variables if v["name"] == variable_name), None)
        if not var_def:
            step.result = {"value": None, "color": "grey"}
            step.outcome_assessment = f"Variable {variable_name} not found in RoE"
            step.status = "completed"
            step.model_used = ""
            step.save()
            return

        # Format collected data
        collected = self._format_collected_data(plan)

        # Build assessment prompt
        step_prompt = (
            f"VARIABLE: {var_def['name']} ({var_def['abbrev']})\n\n"
            f"CALCULATING RULE:\n{var_def['calculating']}\n\n"
            f"INTERPRETING RULE:\n{var_def['interpreting']}\n\n"
            f"COLLECTED PROJECT DATA:\n{collected}\n\n"
            'Compute the variable value and color. Respond with JSON: {"value": "...", "color": "green|orange|red|grey"}\n'
            "If data is insufficient, return: " + '{"value": null, "color": "grey"}'
        )

        messages = [{"role": "user", "content": step_prompt}]

        # Use execution model (Sonnet), NOT planning model (Opus)
        response = self.llm.generate_with_tools(
            messages=messages,
            tools=[],
            system_blocks=[],
        )

        # Parse response
        try:
            from gjallarhorn.services.sitrep_service import _extract_json  # noqa: PLC0415

            result = _extract_json(response.content)
            value = result.get("value")
            color = result.get("color", "grey")

            if color not in ("green", "orange", "red", "grey"):
                color = "grey"

            step.result = {"value": value, "color": color}
            step.outcome_assessment = f"Variable assessed: {value} ({color})"

        except (json.JSONDecodeError, TypeError, KeyError) as exc:
            logger.warning(
                "plan=%s step %s variable assessment parse error (%s); defaulting to grey",
                plan.plan_id,
                step.order,
                exc,
            )
            step.result = {"value": None, "color": "grey"}
            step.outcome_assessment = f"Parse error: {exc}"

        step.status = "completed"
        step.model_used = response.model or ""
        step.save()
        # TODO(chat-milestone): publish plan_step_update to Redis

    # ------------------------------------------------------------------
    # Private: helpers
    # ------------------------------------------------------------------

    def _resolve_tool_kwargs(self, tool_name: str, plan: ExecutionPlan) -> dict:
        """Return the kwargs to pass to a data tool based on the plan's time window."""
        if tool_name in ("list_commits", "get_contributor_activity"):
            return {"from_dt": plan.sitrep_from_dt, "to_dt": plan.sitrep_to_dt}
        if tool_name == "list_active_fragos":
            return {"at_dt": plan.sitrep_to_dt}
        return {}

    def _format_collected_data(self, plan: ExecutionPlan) -> str:
        """Build a human-readable context block from all completed data steps."""
        sections = []
        for step in plan.steps.filter(status="completed", is_planning=False).order_by("order"):
            raw = step.result or {}
            data = raw.get("result") if raw.get("success") else None
            label = step.action
            if data is not None:
                try:
                    body = json.dumps(data, default=str, indent=2)
                except (TypeError, ValueError):
                    body = str(data)
            else:
                error = raw.get("error", "unavailable")
                body = f"[{label} unavailable: {error}]"
            sections.append(f"### {label}\n{body}")
        return "\n\n".join(sections) if sections else "[No data collected]"

    def _build_system_blocks(self, plan: ExecutionPlan) -> list[dict]:
        """Assemble cached system prompt blocks for the planning step.

        Provides: system prompt + static commander context (RoE, FRAGOs, SA).
        Dynamic data (commits, activity) is injected via the user message in
        _execute_planning_step so it stays separate from the cached system context.
        """
        blocks = [
            {
                "type": "text",
                "text": SITREP_NARRATIVE_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        static_tools = [
            ("get_active_roe", "Active Rules of Engagement"),
            ("list_active_fragos", "Active FRAGOs"),
            ("get_active_situational_awareness", "Situational Awareness"),
        ]
        for tool_name, label in static_tools:
            result = self.tool_executor.execute(tool_name)
            if result["success"] and result["result"] is not None:
                text = str(result["result"])
            else:
                text = f"[{label} unavailable]"
            blocks.append(
                {
                    "type": "text",
                    "text": text,
                    "cache_control": {"type": "ephemeral"},
                }
            )

        return blocks
