"""GjallarhornAgent — create_plan, execute_single_step, process_user_message (deferred)."""

from django.db import transaction
from django.utils import timezone

from gjallarhorn.agent.exceptions import ToolExecutionError
from gjallarhorn.agent.prompts import SITREP_NARRATIVE_SYSTEM_PROMPT
from gjallarhorn.models import ExecutionPlan, PlanStep


class GjallarhornAgent:
    """AI agent for Huginn.

    Narrative phase: create_plan + execute_single_step only.
    process_user_message is deferred to the chat milestone.
    """

    def __init__(self, llm, tool_executor):
        self.llm = llm
        self.tool_executor = tool_executor

    def create_plan(self, conversation, goal: str, steps: list[dict]) -> ExecutionPlan:
        """Persist ExecutionPlan + PlanStep rows atomically, then enqueue execute_plan.

        Args:
            conversation: Conversation instance
            goal: Human-readable goal for the plan
            steps: List of dicts with keys: order, action, reasoning_why_needed, expected_outcome

        Returns:
            The created ExecutionPlan
        """
        with transaction.atomic():
            plan = ExecutionPlan.objects.create(
                conversation=conversation,
                goal=goal,
                progress_total=len(steps),
            )
            for step_data in steps:
                PlanStep.objects.create(plan=plan, **step_data)

        # Lazy import avoids circular dep: tasks → agent → tasks
        from gjallarhorn.tasks.plan_tasks import execute_plan

        execute_plan.delay(str(plan.plan_id))
        return plan

    def execute_single_step(self, plan, step) -> None:
        """Execute one PlanStep: assemble context, call LLM, dispatch tools, persist result.

        Args:
            plan: ExecutionPlan instance
            step: PlanStep instance (status must be 'pending')
        """
        system_blocks = self._build_system_blocks(plan)
        messages = self._build_step_messages(plan, step)

        response = self.llm.generate_with_tools(
            messages=messages,
            tools=[],
            system_blocks=system_blocks,
        )

        if response.stop_reason == "tool_use":
            for tool_call in response.tool_calls:
                tool_name = tool_call.get("name", "")
                tool_input = tool_call.get("input", {})
                result = self.tool_executor.execute(tool_name, **tool_input)
                if not result["success"]:
                    raise ToolExecutionError(result.get("error", "Unknown tool error"))

        step.result = {"content": response.content}
        step.outcome_assessment = response.content
        step.status = "completed"
        step.save()

    def process_user_message(self, *args, **kwargs) -> None:
        raise NotImplementedError("Chat milestone")

    def _build_system_blocks(self, plan) -> list[dict]:
        """Build the 4 Anthropic prompt-cache blocks for plan execution (§17.6)."""
        project_id = plan.conversation.project_id

        # Block 1: Base system prompt (never changes)
        block1 = {
            "type": "text",
            "text": SITREP_NARRATIVE_SYSTEM_PROMPT,
            "cache_control": {"type": "ephemeral"},
        }

        # Block 2: Active Playbook
        pb_result = self.tool_executor.execute("get_active_playbook", project_id=project_id)
        if pb_result.get("success") and pb_result.get("result"):
            pb = pb_result["result"]
            pb_text = f"# Active Playbook: {pb.get('playbook_name', '')}\n{pb.get('workflow_md', '')}"
        else:
            pb_text = "# Active Playbook\n(No playbook assigned)"
        block2 = {"type": "text", "text": pb_text, "cache_control": {"type": "ephemeral"}}

        # Block 3: Active FRAGOs
        at_dt = timezone.now().date()
        fragos_result = self.tool_executor.execute("list_active_fragos", project_id=project_id, at_dt=at_dt)
        if fragos_result.get("success") and fragos_result.get("result"):
            fragos_text = "# Active FRAGOs\n" + "\n".join(
                f"## {f['title']}\n{f['body_md']}" for f in fragos_result["result"]
            )
        else:
            fragos_text = "# Active FRAGOs\n(No active FRAGOs)"
        block3 = {"type": "text", "text": fragos_text, "cache_control": {"type": "ephemeral"}}

        # Block 4: Situational Awareness
        sa_result = self.tool_executor.execute("get_active_situational_awareness", project_id=project_id)
        if sa_result.get("success") and sa_result.get("result"):
            sa = sa_result["result"]
            sa_text = (
                f"# Situational Awareness\n"
                f"## Standing\n{sa.get('standing_md', '')}\n"
                f"## Active\n{sa.get('active_md', '')}"
            )
        else:
            sa_text = "# Situational Awareness\n(No SA configured)"
        block4 = {"type": "text", "text": sa_text, "cache_control": {"type": "ephemeral"}}

        return [block1, block2, block3, block4]

    def _build_step_messages(self, plan, step) -> list[dict]:
        """Build message history including prior step results and current step instruction."""
        messages = []

        completed = plan.steps.filter(status="completed").order_by("order")
        for prev in completed:
            if prev.order < step.order:
                messages.append(
                    {
                        "role": "assistant",
                        "content": (f"[Step {prev.order} — {prev.action}]\nResult: {prev.result}"),
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": (
                    f"STEP GOAL: {step.action}\n"
                    f"REASONING: {step.reasoning_why_needed}\n"
                    f"Execute this step now using available tools."
                ),
            }
        )
        return messages
