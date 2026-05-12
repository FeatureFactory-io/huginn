"""sitrep_service.build_narrative_plan_steps tests — T-66."""

from gjallarhorn.services.sitrep_service import build_narrative_plan_steps


class TestBuildNarrativePlanSteps:
    def test_returns_five_steps(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        assert len(steps) == 5

    def test_canonical_order(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        assert "commit" in steps[0]["action"].lower()
        assert "narrative" in steps[4]["action"].lower()

    def test_no_variable_or_decision_language(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        for step in steps:
            action_lower = step["action"].lower()
            assert "variable" not in action_lower
            assert "decision" not in action_lower

    def test_all_steps_have_required_fields(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        for step in steps:
            assert step.get("action")
            assert step.get("reasoning_why_needed")
            assert step.get("expected_outcome")
