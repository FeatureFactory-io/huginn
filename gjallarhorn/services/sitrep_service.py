"""SitRep service — narrative plan step definitions."""


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
