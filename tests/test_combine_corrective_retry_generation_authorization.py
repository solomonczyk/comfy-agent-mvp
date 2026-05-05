"""RC-COMBINE-V2-861-920 — Test Operator Corrective Retry Generation Authorization.

Tests for the combine-authorize-corrective-retry-generation CLI command.
Verifies that operator authorization:
- Requires corrective retry package
- Authorizes exactly one corrective retry generation
- Sets next_allowed_action to corrective_retry_generate_assets
- Blocks blind retry
- Blocks downstream
- Production accepted is false
"""

import json
import pytest
from pathlib import Path
from argparse import Namespace
import sys
import os

# Add app to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.cli import combine_authorize_corrective_retry_generation
from app.orchestrator.state_machine import CombineStateMachine


class TestCorrectiveRetryGenerationAuthorization:
    """Test operator corrective retry generation authorization gate."""

    def test_authorization_requires_corrective_retry_package(self, tmp_path):
        """Authorization must fail if corrective retry package is missing."""
        args = Namespace(
            project_root=str(tmp_path),
            decision="approve_one_corrective_retry_generation",
            reason="operator_approved_one_corrective_retry_generation_after_package_review",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 1

    def test_authorization_sets_correct_next_action(self, tmp_path):
        """Authorization must set next_allowed_action to corrective_retry_generate_assets."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create prerequisite artifacts
        auth_request = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_review_required": True,
            "retry_generation_authorized": False,
            "next_allowed_action": "operator_retry_generation_authorization_required"
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization_request.json", 'w') as f:
            json.dump(auth_request, f)

        package = {
            "stage": "corrective_retry_implementation_required",
            "package_type": "controlled_corrective_retry_implementation",
            "prompt_patch_created": True,
            "workflow_patch_created": True,
            "next_allowed_action": "operator_retry_generation_authorization_required"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            decision="approve_one_corrective_retry_generation",
            reason="operator_approved_one_corrective_retry_generation_after_package_review",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 0

        # Verify authorization artifact
        auth_path = control_dir / "combine_v2_operator_retry_generation_authorization.json"
        assert auth_path.exists()
        with open(auth_path) as f:
            data = json.load(f)

        assert data["operator_retry_generation_authorized"] is True
        assert data["max_generations"] == 1
        assert data["generation_allowed"] is True
        assert data["retry_allowed"] is True
        assert data["workflow_submitted"] is False
        assert data["comfyui_execution"] is False
        assert data["production_accepted"] is False
        assert data["next_allowed_action"] == "corrective_retry_generate_assets"
        assert data["corrective_retry_package_required"] is True
        assert data["corrective_retry_package_available"] is True

    def test_rejection_blocks_generation(self, tmp_path):
        """Non-approval decision must block generation and keep state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth_request = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_review_required": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization_request.json", 'w') as f:
            json.dump(auth_request, f)

        package = {
            "stage": "corrective_retry_implementation_required",
            "package_type": "controlled_corrective_retry_implementation"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            decision="abort_route",
            reason="operator_aborted",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 1

        # Verify rejection artifact
        rejection_path = control_dir / "combine_v2_operator_retry_generation_rejection.json"
        assert rejection_path.exists()
        with open(rejection_path) as f:
            data = json.load(f)

        assert data["operator_retry_generation_authorized"] is False
        assert data["generation_allowed"] is False
        assert data["retry_allowed"] is False
        assert data["production_accepted"] is False
        assert data["next_allowed_action"] == "operator_retry_generation_authorization_required"

    def test_invalid_decision_is_rejected(self, tmp_path):
        """Invalid decision must be rejected."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        args = Namespace(
            project_root=str(tmp_path),
            decision="invalid_decision",
            reason="test",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 1

    def test_state_machine_allows_transition_to_corrective_retry_generate_assets(self):
        """State machine must allow transition from operator_retry_generation_authorization_required to corrective_retry_generate_assets."""
        assert CombineStateMachine.can_transition(
            "operator_retry_generation_authorization_required",
            "corrective_retry_generate_assets"
        )

    def test_state_machine_blocks_transition_to_assembly(self):
        """State machine must block transition from operator_retry_generation_authorization_required to assembly."""
        assert not CombineStateMachine.can_transition(
            "operator_retry_generation_authorization_required",
            "assembly_required"
        )

    def test_state_machine_blocks_transition_to_completed(self):
        """State machine must block transition from corrective_retry_generate_assets to completed."""
        assert not CombineStateMachine.can_transition(
            "corrective_retry_generate_assets",
            "completed"
        )

    def test_artifact_index_updated(self, tmp_path):
        """Artifact index must be updated with authorization state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth_request = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_review_required": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization_request.json", 'w') as f:
            json.dump(auth_request, f)

        package = {
            "stage": "corrective_retry_implementation_required",
            "package_type": "controlled_corrective_retry_implementation"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            decision="approve_one_corrective_retry_generation",
            reason="operator_approved_one_corrective_retry_generation_after_package_review",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 0

        # Verify artifact index
        index_path = control_dir / "artifact_index.json"
        assert index_path.exists()
        with open(index_path) as f:
            index = json.load(f)

        assert index["current_state"] == "corrective_retry_generate_assets"
        assert index["next_allowed_action"] == "corrective_retry_generate_assets"
        assert index["operator_retry_generation_authorized"] is True
        assert index["max_generations"] == 1
        assert index["generation_allowed"] is True
        assert index["retry_allowed"] is True
        assert index["workflow_submitted"] is False
        assert index["comfyui_execution"] is False
        assert index["visual_qa_executed"] is False
        assert index["assembly_executed"] is False
        assert index["downstream_executed"] is False
        assert index["production_accepted"] is False

    def test_ledger_updated(self, tmp_path):
        """Episode ledger must record authorization event."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth_request = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_review_required": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization_request.json", 'w') as f:
            json.dump(auth_request, f)

        package = {
            "stage": "corrective_retry_implementation_required",
            "package_type": "controlled_corrective_retry_implementation"
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            decision="approve_one_corrective_retry_generation",
            reason="operator_approved_one_corrective_retry_generation_after_package_review",
            json=True
        )

        result = combine_authorize_corrective_retry_generation(args)
        assert result == 0

        # Verify ledger
        ledger_path = control_dir / "episode_ledger.json"
        assert ledger_path.exists()
        with open(ledger_path) as f:
            ledger = json.load(f)

        assert isinstance(ledger, list)
        assert len(ledger) >= 1
        last_event = ledger[-1]
        assert last_event["event_type"] == "operator_retry_generation_authorized"
        assert last_event["operator_retry_generation_authorized"] is True
        assert last_event["max_generations"] == 1
