"""Test generation gate state transitions — correctness of state updates.

RC-COMBINE-V2-86001-94000
"""

import json
from pathlib import Path

import pytest

from app.generation_gate import (
    build_generation_gate_package,
    validate_generation_gate_package,
)


def _write_blocked_artifacts(control_dir: Path):
    """Write blocked-path input artifacts."""
    wf_assets = control_dir / "workflow_assets"
    wf_assets.mkdir(parents=True)
    for name, data in {
        "submitted_workflow_contract.json": {
            "per_shot_workflow_contracts": [
                {"shot_id": "shot_001", "workflow_family": "sdxl_txt2img",
                 "forbidden_fake_prompt_id": True, "forbidden_fake_asset": True},
            ],
            "forbidden_fake_prompt_id": True,
            "forbidden_fake_asset": True,
            "comfyui_submit_executed": False,
            "workflow_execution_performed": False,
        },
        "workflow_validation_report.json": {
            "ksampler_required": True, "saveimage_required": True,
            "filename_prefix_policy_defined": True,
            "legacy_512_workflow_blocked": True, "stub_workflow_blocked": True,
            "workflow_execution_performed": False, "comfyui_submit_executed": False,
        },
        "asset_requirements.json": {"task_id": "test"},
        "asset_resolution_plan.json": {"task_id": "test", "missing_assets": ["checkpoint_sdxl_base"]},
        "asset_verification_report.json": {
            "required_assets_available": False,
            "required_assets_blocked": True,
            "errors": ["Required assets missing: ['checkpoint_sdxl_base']"],
        },
        "asset_blocker_report.json": {
            "blocker_id": "test_blocker",
            "missing_or_invalid_asset": "checkpoint_sdxl_base",
            "generation_preflight_allowed": False,
        },
        "generation_preflight_operator_review_packet.json": {
            "has_asset_blocker": True,
            "generation_preflight_ready": False,
        },
    }.items():
        with open(wf_assets / name, "w") as f:
            json.dump(data, f)


def _write_ready_artifacts(control_dir: Path):
    """Write ready-path input artifacts."""
    wf_assets = control_dir / "workflow_assets"
    wf_assets.mkdir(parents=True)
    for name, data in {
        "submitted_workflow_contract.json": {
            "per_shot_workflow_contracts": [
                {"shot_id": "shot_001", "workflow_family": "sdxl_txt2img",
                 "forbidden_fake_prompt_id": True, "forbidden_fake_asset": True},
            ],
            "forbidden_fake_prompt_id": True,
            "forbidden_fake_asset": True,
            "comfyui_submit_executed": False,
            "workflow_execution_performed": False,
        },
        "workflow_validation_report.json": {
            "ksampler_required": True, "saveimage_required": True,
            "filename_prefix_policy_defined": True,
            "legacy_512_workflow_blocked": True, "stub_workflow_blocked": True,
        },
        "asset_requirements.json": {"task_id": "test"},
        "asset_resolution_plan.json": {"task_id": "test", "missing_assets": []},
        "asset_verification_report.json": {
            "required_assets_available": True,
            "required_assets_blocked": False,
        },
        "generation_preflight_operator_review_packet.json": {
            "has_asset_blocker": False,
            "generation_preflight_ready": True,
        },
    }.items():
        with open(wf_assets / name, "w") as f:
            json.dump(data, f)


class TestGenerationGateStateTransitions:
    """Test state transition correctness."""

    def test_blocked_path_state_transition(self, tmp_path):
        """Blocked path must set controlled_asset_acquisition_required."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["current_state"] == "controlled_asset_acquisition_required"
        assert result["next_allowed_action"] == "controlled_asset_acquisition_required"
        assert result["selected_branch"] == "blocked_by_missing_assets"

    def test_ready_path_state_transition(self, tmp_path):
        """Ready path must set generation_operator_authorization_required."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["current_state"] == "generation_operator_authorization_required"
        assert result["next_allowed_action"] == "generation_operator_authorization_required"
        assert result["selected_branch"] == "ready_for_operator_authorization"

    def test_artifact_index_updated_blocked(self, tmp_path):
        """Blocked path must update artifact_index.json."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)

        # Create initial artifact index with some previous state
        index_path = control_dir / "artifact_index.json"
        initial_index = {
            "current_state": "generation_preflight_operator_review_required",
            "next_allowed_action": "generation_preflight_operator_review_required",
            "generation_performed": False,
        }
        with open(index_path, "w") as f:
            json.dump(initial_index, f)

        build_generation_gate_package(str(tmp_path))

        # Load updated index
        with open(index_path) as f:
            index = json.load(f)

        assert index.get("generation_gate_layer_executed") is True
        assert index.get("generation_runtime_blocker_report_created") is True
        assert index.get("generation_authorization_contract_created") is False
        assert index.get("current_state") == "controlled_asset_acquisition_required"
        assert index.get("next_allowed_action") == "controlled_asset_acquisition_required"
        assert index.get("generation_performed") is False

    def test_artifact_index_updated_ready(self, tmp_path):
        """Ready path must update artifact_index.json."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)

        index_path = control_dir / "artifact_index.json"
        with open(index_path, "w") as f:
            json.dump({
                "current_state": "generation_preflight_operator_review_required",
                "next_allowed_action": "generation_preflight_operator_review_required",
            }, f)

        build_generation_gate_package(str(tmp_path))

        with open(index_path) as f:
            index = json.load(f)

        assert index.get("generation_gate_layer_executed") is True
        assert index.get("generation_authorization_contract_created") is True
        assert index.get("current_state") == "generation_operator_authorization_required"
        assert index.get("generation_performed") is False

    def test_episode_ledger_updated_blocked(self, tmp_path):
        """Blocked path must add episode_ledger entry."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)

        ledger_path = control_dir / "episode_ledger.json"
        with open(ledger_path, "w") as f:
            json.dump([], f)

        build_generation_gate_package(str(tmp_path))

        with open(ledger_path) as f:
            ledger = json.load(f)

        assert len(ledger) >= 1
        last_entry = ledger[-1]
        assert last_entry["event"] == "generation_gate_evaluated"
        assert last_entry["selected_branch"] == "blocked_by_missing_assets"
        assert last_entry["generation_authorized"] is False
        assert last_entry["generation_performed"] is False
        assert last_entry["current_state"] == "controlled_asset_acquisition_required"

    def test_episode_ledger_updated_ready(self, tmp_path):
        """Ready path must add episode_ledger entry."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)

        ledger_path = control_dir / "episode_ledger.json"
        with open(ledger_path, "w") as f:
            json.dump([], f)

        build_generation_gate_package(str(tmp_path))

        with open(ledger_path) as f:
            ledger = json.load(f)

        last_entry = ledger[-1]
        assert last_entry["selected_branch"] == "ready_for_operator_authorization"
        assert last_entry["current_state"] == "generation_operator_authorization_required"

    def test_state_transition_correct_execution_flags(self, tmp_path):
        """State transitions must properly clear execution flags."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))

        assert result["generation_authorized"] is False
        assert result["generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["workflow_execution_performed"] is False
        assert result["retry_attempted"] is False
        assert result["visual_qa_executed"] is False
        assert result["visual_acceptance_executed"] is False
        assert result["preview_render_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False

    def test_invalid_workflow_contract_state(self, tmp_path):
        """Invalid workflow contract must result in blocked state."""
        control_dir = tmp_path / "output" / "control"
        wf_assets = control_dir / "workflow_assets"
        wf_assets.mkdir(parents=True)

        # Write contract that claims execution
        with open(wf_assets / "submitted_workflow_contract.json", "w") as f:
            json.dump({
                "prompt_id": "fake-prompt",
                "comfyui_submit_executed": True,
                "generated_assets": ["fake.png"],
            }, f)
        with open(wf_assets / "workflow_validation_report.json", "w") as f:
            json.dump({
                "ksampler_required": True, "saveimage_required": True,
                "filename_prefix_policy_defined": True,
                "legacy_512_workflow_blocked": True, "stub_workflow_blocked": True,
            }, f)

        build_generation_gate_package(str(tmp_path))

        # Should result in invalid_workflow_contract
        with open(control_dir / "generation_gate_decision.json") as f:
            decision = json.load(f)
        assert decision["generation_gate_decision"] == "invalid_workflow_contract"
        assert decision["generation_can_be_authorized"] is False

    def test_blocker_state_preserved_across_paths(self, tmp_path):
        """Blocker state must be preserved in both evaluation and package build."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))

        # Check gate decision artifact
        with open(control_dir / "generation_gate_decision.json") as f:
            decision = json.load(f)
        assert decision.get("asset_blocker_active") is True
        assert decision.get("generation_can_be_authorized") is False
