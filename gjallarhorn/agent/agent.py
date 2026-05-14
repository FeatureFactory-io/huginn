"""GjallarhornAgent — create_plan, execute_single_step, process_user_message (deferred)."""

from django.db import transaction

from gjallarhorn.agent.exceptions import ToolExecutionError
from gjallarhorn.agent.prompts import SITREP_NARRATIVE_SYSTEM_PROMPT
from gjallarhorn.agent.tool_executor import ToolExecutor
from gjallarhorn.llm.base import LLM
from gjallarhorn.models import ExecutionPlan, PlanStep
from gjallarhorn.services.factory import PLANNING_MODEL

NARRATIVE_TOOLS: list[dict] = []


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
                planning_model=PLANNING_MODEL,
            )
            for i, s in enumerate(steps):
                PlanStep.objects.create(
                    plan=plan,
                    order=i + 1,
                    action=s["action"],
                    reasoning_why_needed=s["reasoning_why_needed"],
                    expected_outcome=s["expected_outcome"],
                    status="pending",
                    is_planning=s.get("is_planning", False),
                )

        # Lazy import to break circular dependency: agent → tasks → agent
        from gjallarhorn.tasks.plan_tasks import execute_plan  # noqa: PLC0415

        execute_plan.delay(str(plan.plan_id))
        # TODO(chat-milestone): publish plan_started to Redis
        return plan

    def execute_single_step(self, plan: ExecutionPlan, step: PlanStep) -> None:
        """Hybrid execution: build prompt → LLM → tool dispatch → persist result."""
        step_prompt = (
            f"STEP GOAL: {step.action}\n"
            f"REASONING: {step.reasoning_why_needed}\n"
            f"PREVIOUS STEPS COMPLETED: {self._format_previous_results(plan)}\n"
            "Execute this step now using available tools."
        )

        system_blocks = self._build_system_blocks(plan)
        messages = [{"role": "user", "content": step_prompt}]
        response = self.llm.generate_with_tools(
            messages=messages,
            tools=NARRATIVE_TOOLS,
            system_blocks=system_blocks,
        )

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

    def process_user_message(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
        raise NotImplementedError("Chat surfaces in a future milestone")

    def _format_previous_results(self, plan: ExecutionPlan) -> str:
        completed = plan.steps.filter(status="completed").order_by("order")
        if not completed.exists():
            return "None"
        lines = []
        for s in completed:
            assessment = s.outcome_assessment or ""
            lines.append(f"Step {s.order} ({s.action}): {assessment}")
        return "\n".join(lines)

    def _build_system_blocks(self, plan: ExecutionPlan) -> list[dict]:
        """Assemble the 4 cached system prompt blocks per SAO §17.6."""
        blocks = [
            {
                "type": "text",
                "text": SITREP_NARRATIVE_SYSTEM_PROMPT,
                "cache_control": {"type": "ephemeral"},
            }
        ]

        tool_names = [
            ("get_active_playbook", "Active Playbook"),
            ("list_active_fragos", "Active FRAGOs"),
            ("get_active_situational_awareness", "Situational Awareness"),
        ]
        for tool_name, label in tool_names:
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
