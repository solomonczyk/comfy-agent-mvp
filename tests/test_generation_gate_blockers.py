"""Test generation gate blocker detection and handling.

RC-COMBINE-V2-86001-94000
"""

import json
from pathlib import Path

import pytest

from app.generation_gate import evaluate_generation_gate


def _write_artifacts(control_dir, overrides=None):
    """Write standard test artifacts with optional overrides."""
    wf_assets = control_dir / "workflow_assets"
    wf_assets.mkdir(parents=True)

    contract = {
        "task_id": "RC-COMBINE-V2-70001-86000",
        "per_shot_workflow_contracts": [
            {"shot_id": "shot_001", "workflow_family": "sdxl_txt2img",
             "forbidden_fake_prompt_id": True, "forbidden_fake_asset": True}
        ],
        "forbidden_fake_prompt_id": True,
        "forbidden_fake_asset": True,
        "comfyui_submit_executed": False,
        "workflow_execution_performed": False,
    }
    validation = {
        "ksampler_required": True,
        "saveimage_required": True,
        "filename_prefix_policy_defined": True,
        "legacy_512_workflow_blocked": True,
        "stub_workflow_blocked": True,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
        "generation_performed": False,
    }
    requirements = {"task_id": "test", "total_requirements": 1}
    resolution = {"task_id": "test", "missing_assets": []}
    verification = {
        "required_assets_available": True,
        "required_assets_blocked": False,
        "missing_assets_not_hidden": True,
    }
    blocker = None
    preflight = {
        "has_asset_blocker": False,
        "generation_preflight_ready": True,
    }

    if overrides:
        contract.update(overrides.get("contract", {}))
        validation.update(overrides.get("validation", {}))
        requirements.update(overrides.get("requirements", {}))
        resolution.update(overrides.get("resolution", {}))
        verification.update(overrides.get("verification", {}))
        blocker = overrides.get("blocker")
        preflight.update(overrides.get("preflight", {}))

    with open(wf_assets / "submitted_workflow_contract.json", "w") as f:
        json.dump(contract, f)
    with open(wf_assets / "workflow_validation_report.json", "w") as f:
        json.dump(validation, f)
    with open(wf_assets / "asset_requirements.json", "w") as f:
        json.dump(requirements, f)
    with open(wf_assets / "asset_resolution_plan.json", "w") as f:
        json.dump(resolution, f)
    with open(wf_assets / "asset_verification_report.json", "w") as f:
        json.dump(verification, f)
    if blocker is not None:
        with open(wf_assets / "asset_blocker_report.json", "w") as f:
            json.dump(blocker, f)
    with open(wf_assets / "generation_preflight_operator_review_packet.json", "w") as f:
        json.dump(preflight, f)


class TestGenerationGateBlockers:
    """Test blocker detection and handling."""

    def test_asset_blocker_prevents_authorization(self, tmp_path):
        """Active asset blocker must prevent generation authorization."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "verification": {
                "required_assets_available": False,
                "required_assets_blocked": True,
                "errors": ["Required assets missing: ['checkpoint_sdxl_base']"],
            },
            "blocker": {
                "blocker_id": "test_blocker",
                "missing_or_invalid_asset": "checkpoint_sdxl_base",
                "generation_preflight_allowed": False,
            },
            "preflight": {
                "has_asset_blocker": True,
                "generation_preflight_ready": False,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["generation_gate_decision"] == "blocked_by_missing_assets"
        assert result["generation_can_be_authorized"] is False
        assert result["asset_blocker_active"] is True

    def test_no_blocker_allows_ready(self, tmp_path):
        """No asset blocker should result in ready."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control)
        result = evaluate_generation_gate(str(tmp_path))
        assert result["generation_gate_decision"] == "ready_for_operator_authorization"
        assert result["asset_blocker_active"] is False

    def test_missing_ksaver_detected(self, tmp_path):
        """Missing KSampler requirement must be a workflow validation failure."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "validation": {
                "ksampler_required": False,
                "saveimage_required": True,
                "filename_prefix_policy_defined": True,
                "legacy_512_workflow_blocked": True,
                "stub_workflow_blocked": True,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["report_valid"] is False

    def test_missing_saveimage_detected(self, tmp_path):
        """Missing SaveImage requirement must be detected."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "validation": {
                "ksampler_required": True,
                "saveimage_required": False,
                "filename_prefix_policy_defined": True,
                "legacy_512_workflow_blocked": True,
                "stub_workflow_blocked": True,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["report_valid"] is False

    def test_missing_filename_prefix_policy_detected(self, tmp_path):
        """Missing filename_prefix policy must be detected."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "validation": {
                "ksampler_required": True,
                "saveimage_required": True,
                "filename_prefix_policy_defined": False,
                "legacy_512_workflow_blocked": True,
                "stub_workflow_blocked": True,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["report_valid"] is False

    def test_legacy_512_not_blocked_detected(self, tmp_path):
        """Legacy 512 workflow not blocked must be detected."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "validation": {
                "ksampler_required": True,
                "saveimage_required": True,
                "filename_prefix_policy_defined": True,
                "legacy_512_workflow_blocked": False,
                "stub_workflow_blocked": True,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["report_valid"] is False

    def test_stub_workflow_not_blocked_detected(self, tmp_path):
        """Stub workflow not blocked must be detected."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "validation": {
                "ksampler_required": True,
                "saveimage_required": True,
                "filename_prefix_policy_defined": True,
                "legacy_512_workflow_blocked": True,
                "stub_workflow_blocked": False,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        assert result["report_valid"] is False

    def test_missing_asset_verification_report(self, tmp_path):
        """Missing asset verification report must be detected."""
        control = tmp_path / "output" / "control"
        wf_assets = control / "workflow_assets"
        wf_assets.mkdir(parents=True)
        # Write only contract and validation
        with open(wf_assets / "submitted_workflow_contract.json", "w") as f:
            json.dump({"per_shot_workflow_contracts": [], "forbidden_fake_prompt_id": True}, f)
        with open(wf_assets / "workflow_validation_report.json", "w") as f:
            json.dump({"ksampler_required": True, "saveimage_required": True,
                       "filename_prefix_policy_defined": True, "legacy_512_workflow_blocked": True,
                       "stub_workflow_blocked": True}, f)
        result = evaluate_generation_gate(str(tmp_path))
        assert result["asset_verification_valid"] is False

    def test_checkpoint_blocker_routes_to_acquisition(self, tmp_path):
        """Checkpoint blocker should be flagged as requiring controlled acquisition."""
        control = tmp_path / "output" / "control"
        _write_artifacts(control, {
            "verification": {
                "required_assets_available": False,
                "required_assets_blocked": True,
                "errors": ["Required assets missing: ['checkpoint_sdxl_base']"],
            },
            "blocker": {
                "blocker_id": "asset_blocker_test",
                "missing_or_invalid_asset": "checkpoint_sdxl_base",
                "generation_preflight_allowed": False,
            },
            "preflight": {
                "has_asset_blocker": True,
                "generation_preflight_ready": False,
            },
        })
        result = evaluate_generation_gate(str(tmp_path))
        blocker_types = [b["type"] for b in result["blockers"]]
        assert "active_asset_blocker" in blocker_types or "missing_required_assets" in blocker_types
