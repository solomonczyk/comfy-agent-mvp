"""
Tests for Operator Visual Decision Forbidden Actions — RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001.

Verifies that the operator visual decision gate does NOT:
- new_generation_performed
- comfyui_submit_executed
- retry_attempted
- agent_visual_acceptance_executed
- preview_render_executed
- assembly_executed
- downstream_executed
- production_accepted set to True

Also verifies state machine forbids certain transitions from new states.
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    (tmp_path / "output" / "control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "assets").mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestForbiddenActionsInOutput:
    """Tests that forbidden actions are never set in output artifacts."""

    def test_forbidden_actions_all_false_accepted(self, project_dir):
        """Forbidden actions must be False for accepted branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["retry_attempted"] is False
        assert result["agent_visual_acceptance_executed"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_forbidden_actions_all_false_rejected(self, project_dir):
        """Forbidden actions must be False for rejected branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="test",
        )

        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["retry_attempted"] is False
        assert result["agent_visual_acceptance_executed"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_forbidden_actions_all_false_needs_fix(self, project_dir):
        """Forbidden actions must be False for needs_fix branch."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="needs_fix",
            reason="test",
        )

        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["retry_attempted"] is False
        assert result["agent_visual_acceptance_executed"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_forbidden_actions_all_false_missing(self, project_dir):
        """Forbidden actions must be False for missing verdict."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["retry_attempted"] is False
        assert result["agent_visual_acceptance_executed"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_decision_artifact_has_production_accepted_false(self, project_dir):
        """operator_visual_decision.json must have production_accepted=False."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "operator_visual_decision.json") as f:
            artifact = json.load(f)

        assert artifact.get("production_accepted") is False

    def test_artifact_index_has_production_accepted_false(self, project_dir):
        """artifact_index.json must have production_accepted=False."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx.get("production_accepted") is False
        assert idx.get("visual_acceptance_executed") is False

    def test_technical_pass_not_treated_as_visual_pass(self, project_dir):
        """Artifact index must have technical_pass_not_treated_as_visual_pass=True."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "artifact_index.json") as f:
            idx = json.load(f)

        assert idx.get("technical_pass_not_treated_as_visual_pass") is True

    def test_generation_blocked_accepted(self, project_dir):
        """Accepted branch must not allow generation."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        assert result["new_generation_performed"] is False
        assert result["comfyui_submit_executed"] is False

    def test_retry_blocked_rejected(self, project_dir):
        """Rejected branch must not allow retry."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="test",
        )

        assert result["retry_attempted"] is False

    def test_assembly_blocked_all_branches(self, project_dir):
        """Assembly must be blocked for all branches."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        for v in ["accepted", "rejected", "needs_fix", None]:
            r = record_operator_visual_decision(
                project_root=str(project_dir),
                verdict=v,
                reason="test" if v else None,
            )
            assert r["assembly_executed"] is False, f"assembly_executed must be False for verdict={v}"

    def test_downstream_blocked_all_branches(self, project_dir):
        """Downstream must be blocked for all branches."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        for v in ["accepted", "rejected", "needs_fix", None]:
            r = record_operator_visual_decision(
                project_root=str(project_dir),
                verdict=v,
                reason="test" if v else None,
            )
            assert r["downstream_executed"] is False, f"downstream_executed must be False for verdict={v}"

    def test_agent_cannot_accept_visually(self, project_dir):
        """Agent must not accept visually."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="test",
        )

        assert result["agent_visual_acceptance_executed"] is False


class TestStateMachineForbiddenTransitions:
    """Tests that the state machine correctly forbids unsafe transitions."""

    def test_generation_blocked_from_accepted(self):
        """Visual_asset_operator_accepted cannot transition to generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_asset_operator_accepted", "generate_assets"
        )

    def test_real_generation_blocked_from_accepted(self):
        """Visual_asset_operator_accepted cannot transition to real_generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_asset_operator_accepted", "real_generate_assets"
        )

    def test_visual_qa_blocked_from_accepted(self):
        """Visual_asset_operator_accepted cannot transition to visual_qa_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_asset_operator_accepted", "visual_qa_required"
        )

    def test_completed_blocked_from_accepted(self):
        """Visual_asset_operator_accepted cannot transition to completed."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_asset_operator_accepted", "completed"
        )

    def test_production_accepted_blocked_from_accepted(self):
        """Visual_asset_operator_accepted cannot transition to production_accepted."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_asset_operator_accepted", "production_accepted"
        )

    def test_generation_blocked_from_correction(self):
        """Visual_correction_required cannot transition to generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_correction_required", "generate_assets"
        )

    def test_assembly_blocked_from_correction(self):
        """Visual_correction_required cannot transition to assembly_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_correction_required", "assembly_required"
        )

    def test_generation_blocked_from_needs_fix(self):
        """Visual_review_needs_fix cannot transition to generate_assets."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_review_needs_fix", "generate_assets"
        )

    def test_assembly_blocked_from_needs_fix(self):
        """Visual_review_needs_fix cannot transition to assembly_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition(
            "visual_review_needs_fix", "assembly_required"
        )

    def test_new_states_are_valid(self):
        """New states must be valid in the state machine."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.is_valid_state("visual_asset_operator_accepted")
        assert CombineStateMachine.is_valid_state("visual_correction_required")
        assert CombineStateMachine.is_valid_state("visual_review_needs_fix")


class TestForbiddenActionsInModule:
    """Tests that the module-level forbidden actions are correct."""

    def test_forbidden_actions_not_in_function(self):
        """The record_operator_visual_decision function must not set forbidden actions to True."""
        import inspect
        from app.qa import operator_visual_decision

        source = inspect.getsource(operator_visual_decision.record_operator_visual_decision)

        # These patterns should NOT appear in the function (as True assignments)
        forbidden_patterns = [
            "new_generation_performed = True",
            "comfyui_submit_executed = True",
            "retry_attempted = True",
            "agent_visual_acceptance_executed = True",
            "assembly_executed = True",
            "downstream_executed = True",
            "production_accepted = True",
        ]
        for pattern in forbidden_patterns:
            assert pattern not in source, f"Found forbidden pattern in function: {pattern}"
