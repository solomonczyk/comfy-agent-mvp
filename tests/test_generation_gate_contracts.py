"""Test generation gate contract validation — READY and BLOCKED path artifacts.

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
    """Write standard blocked-path input artifacts."""
    wf_assets = control_dir / "workflow_assets"
    wf_assets.mkdir(parents=True)
    artifacts = {
        "submitted_workflow_contract.json": {
            "task_id": "test",
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
            "ksampler_required": True,
            "saveimage_required": True,
            "filename_prefix_policy_defined": True,
            "legacy_512_workflow_blocked": True,
            "stub_workflow_blocked": True,
            "workflow_execution_performed": False,
            "comfyui_submit_executed": False,
        },
        "asset_requirements.json": {"task_id": "test", "total_requirements": 1},
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
    }
    for name, data in artifacts.items():
        with open(wf_assets / name, "w") as f:
            json.dump(data, f)


def _write_ready_artifacts(control_dir: Path):
    """Write standard ready-path input artifacts."""
    wf_assets = control_dir / "workflow_assets"
    wf_assets.mkdir(parents=True)
    artifacts = {
        "submitted_workflow_contract.json": {
            "task_id": "test",
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
            "ksampler_required": True,
            "saveimage_required": True,
            "filename_prefix_policy_defined": True,
            "legacy_512_workflow_blocked": True,
            "stub_workflow_blocked": True,
        },
        "asset_requirements.json": {"task_id": "test", "total_requirements": 0},
        "asset_resolution_plan.json": {"task_id": "test", "missing_assets": []},
        "asset_verification_report.json": {
            "required_assets_available": True,
            "required_assets_blocked": False,
        },
        "generation_preflight_operator_review_packet.json": {
            "has_asset_blocker": False,
            "generation_preflight_ready": True,
        },
    }
    for name, data in artifacts.items():
        with open(wf_assets / name, "w") as f:
            json.dump(data, f)


class TestGenerationGateContracts:
    """Test contract validation and artifact creation."""

    def test_blocked_path_creates_correct_artifacts(self, tmp_path):
        """Blocked path must create blocker, acquisition, and review artifacts."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)

        result = build_generation_gate_package(str(tmp_path))

        assert result["generation_runtime_blocker_report"] is True
        assert result["controlled_asset_acquisition_gate_packet"] is True
        assert result["generation_blocked_operator_review_packet"] is True
        assert result["generation_authorization_contract"] is False
        assert result["selected_branch"] == "blocked_by_missing_assets"
        assert result["current_state"] == "controlled_asset_acquisition_required"
        assert result["generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["production_accepted"] is False

        # Verify artifacts on disk
        assert (control_dir / "generation_gate_decision.json").exists()
        assert (control_dir / "generation_runtime_blocker_report.json").exists()
        assert (control_dir / "controlled_asset_acquisition_gate_packet.json").exists()
        assert (control_dir / "generation_blocked_operator_review_packet.json").exists()
        assert not (control_dir / "generation_authorization_contract.json").exists()

    def test_ready_path_creates_correct_artifacts(self, tmp_path):
        """Ready path must create authorization and execution contracts."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)

        result = build_generation_gate_package(str(tmp_path))

        assert result["generation_authorization_contract"] is True
        assert result["generation_execution_contract"] is True
        assert result["prompt_id_report_contract"] is True
        assert result["native_output_report_contract"] is True
        assert result["canonical_outputs_manifest_contract"] is True
        assert result["visual_qa_input_packet_contract"] is True
        assert result["generation_runtime_blocker_report"] is False
        assert result["selected_branch"] == "ready_for_operator_authorization"
        assert result["current_state"] == "generation_operator_authorization_required"
        assert result["generation_performed"] is False
        assert result["production_accepted"] is False

    def test_blocked_path_validate_passes(self, tmp_path):
        """Blocked path validation must pass with correct artifacts."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))

        validation = validate_generation_gate_package(str(tmp_path))
        assert validation["validation_passed"] is True

    def test_ready_path_validate_passes(self, tmp_path):
        """Ready path validation must pass with correct artifacts."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))

        validation = validate_generation_gate_package(str(tmp_path))
        assert validation["validation_passed"] is True

    def test_missing_gate_decision_fails_validation(self, tmp_path):
        """Missing gate decision artifact must fail validation."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)

        validation = validate_generation_gate_package(str(tmp_path))
        assert validation["validation_passed"] is False
        assert any("not found" in e for e in validation["errors"])

    def test_authorization_contract_not_created_for_blocked(self, tmp_path):
        """Blocked path must not create authorization contract."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))
        assert not (control_dir / "generation_authorization_contract.json").exists()
