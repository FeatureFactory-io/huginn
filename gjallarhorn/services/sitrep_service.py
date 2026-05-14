"""SitRep service — build canonical narrative plan steps."""


def build_narrative_plan_steps(project, from_dt, to_dt) -> list[dict]:
    """Return the 5 canonical narrative plan steps for SitRep generation."""
    return [
        {
            "order": 1,
            "action": "Get commits for period",
            "reasoning_why_needed": "Establish what changed in this window.",
            "expected_outcome": "List of commits with author and message.",
        },
        {
            "order": 2,
            "action": "Get contributor activity for period",
            "reasoning_why_needed": "Identify unusual contribution patterns.",
            "expected_outcome": "Per-contributor commit counts.",
        },
        {
            "order": 3,
            "action": "Load active FRAGOs in window",
            "reasoning_why_needed": "FRAGOs modify assessment scope.",
            "expected_outcome": "List of active FRAGOs at to_dt.",
        },
        {
            "order": 4,
            "action": "Load Situational Awareness",
            "reasoning_why_needed": "Commander context shapes the narrative.",
            "expected_outcome": "Current SA capsule.",
        },
        {
            "order": 5,
            "action": "Compose SitRep narrative",
            "reasoning_why_needed": "Synthesise all context into headline + assessment.",
            "expected_outcome": '{"headline": "...", "situation_assessment": "...", "notable_activity": [...]}',
        },
    ]
