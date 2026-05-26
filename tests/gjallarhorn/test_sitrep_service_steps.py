"""sitrep_service.build_narrative_plan_steps tests — T-66."""

import pytest

from gjallarhorn.services.sitrep_service import build_narrative_plan_steps
from tests.factories import (
    ProjectFactory,
    RulesOfEngagementFactory,
    RulesOfEngagementVariableFactory,
    RulesOfEngagementVersionFactory,
)


class TestBuildNarrativePlanSteps:
    def test_returns_five_steps_when_no_project(self):
        """When project is None, returns 5 steps (4 data + narrative, no variables)."""
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        assert len(steps) == 5

    def test_canonical_order(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        assert "commit" in steps[0]["action"].lower()
        assert "narrative" in steps[4]["action"].lower()

    def test_narrative_only_mode_has_no_variable_steps(self):
        """When project has no RoE or no variables, no Variable assessment steps are inserted."""
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        for step in steps:
            action_lower = step["action"].lower()
            assert "variable" not in action_lower or "assess" not in action_lower
            assert "decision" not in action_lower

    def test_all_steps_have_required_fields(self):
        steps = build_narrative_plan_steps(project=None, from_dt=None, to_dt=None)
        for step in steps:
            assert step.get("action")
            assert step.get("reasoning_why_needed")
            assert step.get("expected_outcome")

    @pytest.mark.django_db
    def test_with_two_variables_returns_seven_steps(self):
        """4 data + 2 variable assessment + 1 narrative = 7 steps."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="Var1", abbrev="V1")
        RulesOfEngagementVariableFactory(roe_version=version, name="Var2", abbrev="V2")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        assert len(steps) == 7

    @pytest.mark.django_db
    def test_with_no_variables_still_returns_five_steps(self):
        """4 data + 0 variables + 1 narrative = 5 steps."""
        roe = RulesOfEngagementFactory()
        RulesOfEngagementVersionFactory(roe=roe, version_number=1)
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        assert len(steps) == 5

    @pytest.mark.django_db
    def test_variable_steps_are_between_data_and_narrative(self):
        """Variable assessment steps are inserted after data steps and before narrative."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="TestVar", abbrev="TV")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        assert len(steps) == 6  # 4 + 1 + 1
        assert steps[0]["order"] == 1  # data
        assert steps[3]["order"] == 4  # last data step
        assert steps[4]["order"] == 5  # variable assessment
        assert steps[4].get("is_variable_assessment") is True
        assert "Assess TestVar" in steps[4]["action"]
        assert steps[5]["order"] == 6  # narrative
        assert steps[5].get("is_planning") is True

    @pytest.mark.django_db
    def test_build_variable_steps_one_per_variable(self):
        """One variable assessment step is created for each RoE Variable."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="Throughput", abbrev="Tp")
        RulesOfEngagementVariableFactory(roe_version=version, name="Cycle Time", abbrev="CT")
        RulesOfEngagementVariableFactory(roe_version=version, name="Lead Time", abbrev="LT")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        variable_steps = [s for s in steps if s.get("is_variable_assessment")]
        assert len(variable_steps) == 3

    @pytest.mark.django_db
    def test_variable_step_has_is_variable_assessment_true(self):
        """Variable assessment steps have is_variable_assessment=True."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        variable_step = next(s for s in steps if "Assess Test" in s["action"])
        assert variable_step["is_variable_assessment"] is True

    @pytest.mark.django_db
    def test_variable_step_is_planning_false(self):
        """Variable assessment steps have is_planning=False (use execution model, not planning)."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="Test", abbrev="T")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        variable_step = next(s for s in steps if "Assess Test" in s["action"])
        assert variable_step["is_planning"] is False

    @pytest.mark.django_db
    def test_variable_step_action_contains_name_and_abbrev(self):
        """Variable step action is 'Assess {name} ({abbrev})'."""
        roe = RulesOfEngagementFactory()
        version = RulesOfEngagementVersionFactory(roe=roe)
        RulesOfEngagementVariableFactory(roe_version=version, name="Throughput", abbrev="Tp")
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        variable_step = next(s for s in steps if s.get("is_variable_assessment"))
        assert variable_step["action"] == "Assess Throughput (Tp)"

    @pytest.mark.django_db
    def test_empty_variables_returns_empty_list(self):
        """When RoE has zero variables, no variable steps are added."""
        roe = RulesOfEngagementFactory()
        RulesOfEngagementVersionFactory(roe=roe)
        project = ProjectFactory(assigned_roe=roe)

        steps = build_narrative_plan_steps(project, from_dt=None, to_dt=None)

        variable_steps = [s for s in steps if s.get("is_variable_assessment")]
        assert len(variable_steps) == 0
