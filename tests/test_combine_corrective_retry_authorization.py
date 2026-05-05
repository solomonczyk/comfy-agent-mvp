"""RC-COMBINE-V2-801-860 — Test controlled corrective retry authorization.

Tests for the combine-authorize-corrective-retry-implementation CLI command.
"""

import json
import tempfile
from pathlib import Path
import pytest
import argparse

from app.cli import combine_authorize_corrective_retry_implementation


class TestCombineCorrectiveRetryAuthorization:
    """Test controlled corrective retry implementation authorization."""

    def setup_control_dir(self, project_root: Path):
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        return control_dir

    def create_required_preconditions(self, control_dir: Path):
        auth_request = {
            "stage": "controlled_retry_authorization_required",
            "operator_review_required": True,
            "recommended_operator_decision": "approve_corrective_retry_implementation",
            "operator_actions": [
                "approve_corrective_retry_implementation",
                "request_corrective_plan_changes",
                "manual_review",
                "abort_route"
            ],
            "generation_allowed": False,
            "retry_allowed": False,
            "workflow_submitted": False,
            "production_accepted": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_controlled_retry_authorization_request.json", 'w') as f:
            json.dump(auth_request, f, indent=2)

        corrective_plan = {
            "stage": "corrective_retry_plan_required",
            "plan_type": "controlled_corrective_retry_plan",
            "source_asset": "output/assets/test_asset.png",
            "failure_basis": [
                "semantic_content_failed",
                "subject_not_recognizable",
                "blur_or_softness",
                "low_detail_quality",
                "composition_failed",
                "production_quality_failed"
            ],
            "blind_retry_allowed": False,
            "retry_requires_operator_authorization": True,
            "generation_allowed": False,
            "next_allowed_action": "controlled_retry_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
            json.dump(corrective_plan, f, indent=2)

    def test_authorize_corrective_retry_implementation_approval(self, tmp_path):
        """Test approving corrective retry implementation authorization."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_required_preconditions(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="approve_corrective_retry_implementation",
            reason="operator_approved_corrective_retry_package_preparation_after_visual_rejection",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 0

        # Verify authorization artifact
        auth_path = control_dir / "combine_v2_corrective_retry_implementation_authorization.json"
        assert auth_path.exists()

        with open(auth_path, 'r') as f:
            auth = json.load(f)

        assert auth["stage"] == "controlled_retry_authorization_required"
        assert auth["operator_decision"] == "approve_corrective_retry_implementation"
        assert auth["corrective_retry_implementation_authorized"] is True
        assert auth["retry_generation_authorized"] is False
        assert auth["generation_allowed"] is False
        assert auth["retry_allowed"] is False
        assert auth["comfyui_execution"] is False
        assert auth["workflow_submitted"] is False
        assert auth["production_accepted"] is False
        assert auth["next_allowed_action"] == "corrective_retry_implementation_required"

        # Verify artifact index
        artifact_index_path = control_dir / "artifact_index.json"
        assert artifact_index_path.exists()

        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["current_state"] == "corrective_retry_implementation_required"
        assert artifact_index["next_allowed_action"] == "corrective_retry_implementation_required"
        assert artifact_index["corrective_retry_implementation_authorized"] is True
        assert artifact_index["retry_generation_authorized"] is False
        assert artifact_index["generation_allowed"] is False
        assert artifact_index["retry_allowed"] is False
        assert artifact_index["retry_attempted"] is False
        assert artifact_index["comfyui_execution"] is False
        assert artifact_index["workflow_submitted"] is False
        assert artifact_index["downstream_executed"] is False
        assert artifact_index["production_accepted"] is False

        # Verify episode ledger
        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()

        with open(ledger_path, 'r') as f:
            ledger = json.load(f)

        assert isinstance(ledger, list)
        assert len(ledger) > 0
        last_event = ledger[-1]
        assert last_event["event_type"] == "corrective_retry_implementation_authorized"
        assert last_event["corrective_retry_implementation_authorized"] is True
        assert last_event["retry_generation_authorized"] is False
        assert last_event["generation_allowed"] is False

    def test_reject_corrective_retry_implementation(self, tmp_path):
        """Test rejecting corrective retry implementation authorization."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_required_preconditions(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="abort_route",
            reason="operator_decided_to_abort_retry_route",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 1

        # Verify rejection artifact
        rejection_path = control_dir / "combine_v2_corrective_retry_implementation_rejection.json"
        assert rejection_path.exists()

        with open(rejection_path, 'r') as f:
            rejection = json.load(f)

        assert rejection["operator_decision"] == "abort_route"
        assert rejection["corrective_retry_implementation_authorized"] is False
        assert rejection["retry_generation_authorized"] is False
        assert rejection["next_allowed_action"] == "controlled_retry_authorization_required"

    def test_missing_preconditions_fails(self, tmp_path):
        """Test authorization fails without preconditions."""
        control_dir = self.setup_control_dir(tmp_path)
        # Don't create preconditions

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="approve_corrective_retry_implementation",
            reason="test_reason",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 1

    def test_invalid_decision_fails(self, tmp_path):
        """Test invalid decision is rejected."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_required_preconditions(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="invalid_decision",
            reason="test_reason",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 1

    def test_generation_and_retry_blocked(self, tmp_path):
        """Test that generation and retry remain blocked after authorization."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_required_preconditions(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="approve_corrective_retry_implementation",
            reason="operator_approved_corrective_retry_package_preparation_after_visual_rejection",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 0

        with open(control_dir / "combine_v2_corrective_retry_implementation_authorization.json", 'r') as f:
            auth = json.load(f)

        assert auth["generation_allowed"] is False
        assert auth["retry_allowed"] is False
        assert auth["retry_generation_authorized"] is False
        assert auth["comfyui_execution"] is False
        assert auth["workflow_submitted"] is False
        assert auth["production_accepted"] is False

    def test_next_allowed_action_after_authorization(self, tmp_path):
        """Test that next_allowed_action points to corrective_retry_implementation_required."""
        control_dir = self.setup_control_dir(tmp_path)
        self.create_required_preconditions(control_dir)

        args = argparse.Namespace(
            project_root=str(tmp_path),
            decision="approve_corrective_retry_implementation",
            reason="operator_approved_corrective_retry_package_preparation_after_visual_rejection",
            json=True
        )

        result_code = combine_authorize_corrective_retry_implementation(args)
        assert result_code == 0

        with open(control_dir / "artifact_index.json", 'r') as f:
            artifact_index = json.load(f)

        assert artifact_index["next_allowed_action"] == "corrective_retry_implementation_required"

    def test_state_machine_has_new_states(self):
        """Test that state machine recognizes the new states."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert CombineStateMachine.is_valid_state("corrective_retry_implementation_required")
        assert CombineStateMachine.is_valid_state("operator_retry_generation_authorization_required")
        assert CombineStateMachine.can_transition("controlled_retry_authorization_required", "corrective_retry_implementation_required")
        assert CombineStateMachine.can_transition("corrective_retry_implementation_required", "operator_retry_generation_authorization_required")

    def test_state_machine_blocks_unsafe_transitions(self):
        """Test that state machine blocks unsafe transitions from corrective_retry_implementation_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition("corrective_retry_implementation_required", "generate_assets")
        assert not CombineStateMachine.can_transition("corrective_retry_implementation_required", "real_generate_assets")
        assert not CombineStateMachine.can_transition("corrective_retry_implementation_required", "assembly_required")
        assert not CombineStateMachine.can_transition("corrective_retry_implementation_required", "completed")

    def test_state_machine_blocks_generate_assets_from_retry_authorization(self):
        """Test that state machine does NOT allow generate_assets from operator_retry_generation_authorization_required."""
        from app.orchestrator.state_machine import CombineStateMachine

        assert not CombineStateMachine.can_transition("operator_retry_generation_authorization_required", "generate_assets")
        assert "generate_assets" not in CombineStateMachine.get_allowed_next_states("operator_retry_generation_authorization_required")
        assert CombineStateMachine.can_transition("operator_retry_generation_authorization_required", "operator_retry_generation_authorization_required")
