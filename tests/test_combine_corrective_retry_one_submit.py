"""RC-COMBINE-V2-861-920 — Test One Controlled Corrective Retry Submit.

Tests for the combine-corrective-retry-generate-assets CLI command.
Verifies that one corrective retry submit:
- Uses corrective retry package from 801-860
- Is limited to exactly one generation attempt
- Blocks blind retry
- Blocks legacy 512 workflow
- Enforces minimum short side 1024
- Submits workflow
- Does not run visual QA
- Does not run assembly
- Does not run downstream
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

from app.cli import combine_corrective_retry_generate_assets
from app.orchestrator.state_machine import CombineStateMachine


class TestCorrectiveRetryOneSubmit:
    """Test one controlled corrective retry generation submit."""

    def test_requires_operator_authorization(self, tmp_path):
        """Submit must fail without operator authorization artifact."""
        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 1

    def test_rejects_max_generations_not_one(self, tmp_path):
        """Submit must reject max_generations != 1."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=2,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 1

    def test_uses_corrective_retry_package(self, tmp_path):
        """Submit must use corrective retry package and set corrective_retry_package_used True."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create authorization artifact
        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_decision": "approve_one_corrective_retry_generation",
            "operator_retry_generation_authorized": True,
            "max_generations": 1,
            "next_allowed_action": "corrective_retry_generate_assets"
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        # Create corrective retry implementation report
        package = {
            "stage": "corrective_retry_implementation_required",
            "package_type": "controlled_corrective_retry_implementation",
            "prompt_patch_created": True,
            "workflow_patch_created": True
        }
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 0

        # Verify submit request artifact
        submit_path = control_dir / "combine_v2_corrective_retry_submit_request.json"
        assert submit_path.exists()
        with open(submit_path) as f:
            data = json.load(f)

        assert data["corrective_retry_package_used"] is True
        assert data["generation_attempts"] == 1
        assert data["max_generations"] == 1
        assert data["workflow_submitted"] is True
        assert data["generation_performed"] is True
        assert data["retry_attempted"] is True
        assert data["second_generation_attempted"] is False
        assert data["blind_retry_allowed"] is False
        assert data["legacy_512_workflow_blocked"] is True
        assert data["minimum_short_side_1024_enforced"] is True
        assert data["visual_qa_executed"] is False
        assert data["assembly_executed"] is False
        assert data["downstream_executed"] is False
        assert data["production_accepted"] is False

    def test_dry_run_does_not_execute_comfyui(self, tmp_path):
        """Dry run must set comfyui_execution False."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_retry_generation_authorized": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        package = {"stage": "corrective_retry_implementation_required"}
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 0

        result_path = control_dir / "combine_v2_corrective_retry_generation_result.json"
        with open(result_path) as f:
            data = json.load(f)

        assert data["comfyui_execution"] is False

    def test_execute_mode_sets_comfyui_execution_true(self, tmp_path, monkeypatch):
        """Execute mode must set comfyui_execution True and attempt real ComfyUI submit."""
        from unittest.mock import AsyncMock, MagicMock
        import asyncio

        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_retry_generation_authorized": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        package = {"stage": "corrective_retry_implementation_required"}
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        # Create a mock ComfyClient that simulates successful execution with zero outputs
        mock_client = MagicMock()
        mock_client.queue_prompt = AsyncMock(return_value="mock_prompt_id")
        mock_client.wait_for_history = AsyncMock(return_value={
            "outputs": {},
            "status": {"completed": True, "status_str": "success"}
        })
        mock_client.fetch_image = AsyncMock(return_value={"content": b"", "content_length": 0})

        def mock_comfy_client_init(*args, **kwargs):
            return mock_client

        monkeypatch.setattr("app.comfy.comfy_client.ComfyClient", mock_comfy_client_init)

        args = Namespace(
            project_root=str(tmp_path),
            execute=True,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        # With zero outputs, status is "failed" and returns 1 per the real generation pattern
        assert result == 1

        result_path = control_dir / "combine_v2_corrective_retry_generation_result.json"
        with open(result_path) as f:
            data = json.load(f)

        assert data["comfyui_execution"] is True
        assert data["workflow_submitted"] is True
        assert data["generation_performed"] is True
        assert data["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"

    def test_generation_trace_blocks_blind_retry(self, tmp_path):
        """Generation trace must record blind_retry_blocked event."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_retry_generation_authorized": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        package = {"stage": "corrective_retry_implementation_required"}
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 0

        trace_path = control_dir / "combine_v2_corrective_retry_generation_trace.json"
        assert trace_path.exists()
        with open(trace_path) as f:
            trace = json.load(f)

        event_names = [e["event"] for e in trace["events"]]
        assert "blind_retry_blocked" in event_names
        assert "legacy_512_blocked" in event_names
        assert "minimum_short_side_1024" in event_names
        assert "visual_qa_skipped" in event_names
        assert "assembly_skipped" in event_names
        assert "downstream_skipped" in event_names

    def test_artifact_index_updated(self, tmp_path):
        """Artifact index must record submit state."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_retry_generation_authorized": True
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        package = {"stage": "corrective_retry_implementation_required"}
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 0

        index_path = control_dir / "artifact_index.json"
        assert index_path.exists()
        with open(index_path) as f:
            index = json.load(f)

        assert index["current_state"] == "corrective_retry_result_review_required"
        assert index["next_allowed_action"] == "corrective_retry_result_review_required"
        assert index["corrective_retry_package_used"] is True
        assert index["generation_attempts"] == 1
        assert index["max_generations"] == 1
        assert index["workflow_submitted"] is True
        assert index["generation_performed"] is True
        assert index["retry_attempted"] is True
        assert index["second_generation_attempted"] is False
        assert index["blind_retry_allowed"] is False
        assert index["legacy_512_workflow_blocked"] is True
        assert index["minimum_short_side_1024_enforced"] is True
        assert index["visual_qa_executed"] is False
        assert index["assembly_executed"] is False
        assert index["downstream_executed"] is False
        assert index["production_accepted"] is False

    def test_not_authorized_blocks_submit(self, tmp_path):
        """Submit must be blocked if operator authorization is false."""
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        auth = {
            "stage": "operator_retry_generation_authorization_required",
            "operator_retry_generation_authorized": False
        }
        with open(control_dir / "combine_v2_operator_retry_generation_authorization.json", 'w') as f:
            json.dump(auth, f)

        package = {"stage": "corrective_retry_implementation_required"}
        with open(control_dir / "combine_v2_corrective_retry_implementation_report.json", 'w') as f:
            json.dump(package, f)

        args = Namespace(
            project_root=str(tmp_path),
            execute=False,
            max_generations=1,
            json=True
        )

        result = combine_corrective_retry_generate_assets(args)
        assert result == 1

    def test_state_machine_blocks_second_generation(self):
        """State machine must block corrective_retry_generate_assets -> generate_assets (second generation)."""
        assert not CombineStateMachine.can_transition(
            "corrective_retry_generate_assets",
            "generate_assets"
        )

    def test_state_machine_blocks_real_generation(self):
        """State machine must block corrective_retry_generate_assets -> real_generate_assets."""
        assert not CombineStateMachine.can_transition(
            "corrective_retry_generate_assets",
            "real_generate_assets"
        )

    def test_state_machine_blocks_assembly(self):
        """State machine must block corrective_retry_generate_assets -> assembly_required."""
        assert not CombineStateMachine.can_transition(
            "corrective_retry_generate_assets",
            "assembly_required"
        )
