"""Test generation gate forbidden actions — must never claim execution.

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
            "blocker_id": "test",
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


class TestGenerationGateForbiddenActions:
    """Test that forbidden actions are never performed or claimed."""

    def test_generation_not_performed_blocked_path(self, tmp_path):
        """Blocked path must not claim generation performed."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["workflow_execution_performed"] is False
        assert result["retry_attempted"] is False
        assert result["visual_qa_executed"] is False
        assert result["production_accepted"] is False
        assert result["downstream_executed"] is False
        assert result["assembly_executed"] is False

    def test_generation_not_performed_ready_path(self, tmp_path):
        """Ready path must not claim generation performed."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["generation_performed"] is False
        assert result["comfyui_submit_executed"] is False
        assert result["workflow_execution_performed"] is False
        assert result["production_accepted"] is False

    def test_fake_prompt_id_forbidden(self, tmp_path):
        """Fake prompt_id must not be created in gate artifacts."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))

        # Check prompt_id contract
        prompt_id_path = control_dir / "prompt_id_report_contract.json"
        if prompt_id_path.exists():
            with open(prompt_id_path) as f:
                data = json.load(f)
            assert data["prompt_id"] is None

    def test_fake_generated_assets_forbidden(self, tmp_path):
        """Fake generated assets must not be created."""
        control_dir = tmp_path / "output" / "control"
        _write_ready_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))

        # Check output manifest
        manifest_path = control_dir / "canonical_outputs_manifest_contract.json"
        if manifest_path.exists():
            with open(manifest_path) as f:
                data = json.load(f)
            assert data["canonical_outputs"] == []

    def test_validation_rejects_execution_claim(self, tmp_path):
        """Validation must reject any execution claims in gate artifacts."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))

        # Tamper with gate decision
        decision_path = control_dir / "generation_gate_decision.json"
        with open(decision_path) as f:
            decision = json.load(f)
        decision["generation_performed"] = True
        decision["comfyui_submit_executed"] = True
        with open(decision_path, "w") as f:
            json.dump(decision, f)

        validation = validate_generation_gate_package(str(tmp_path))
        # Validation should flag the execution claims
        assert any("generation_performed" in e for e in validation.get("errors", []))

    def test_comfyui_submit_not_executed_any_path(self, tmp_path):
        """ComfyUI submit must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["comfyui_submit_executed"] is False

        # Also check ready path
        ready_control = tmp_path / "ready_control"
        _write_ready_artifacts(ready_control)
        result2 = build_generation_gate_package(str(ready_control))
        assert result2["comfyui_submit_executed"] is False

    def test_visual_qa_not_executed(self, tmp_path):
        """Visual QA must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["visual_qa_executed"] is False

    def test_assembly_not_executed(self, tmp_path):
        """Assembly must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["assembly_executed"] is False

    def test_downstream_not_executed(self, tmp_path):
        """Downstream must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["downstream_executed"] is False

    def test_preview_render_not_executed(self, tmp_path):
        """Preview render must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["preview_render_executed"] is False

    def test_visual_acceptance_not_executed(self, tmp_path):
        """Visual acceptance must never be executed in gate layer."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        result = build_generation_gate_package(str(tmp_path))
        assert result["visual_acceptance_executed"] is False

    def test_fake_checkpoint_availability_forbidden(self, tmp_path):
        """Fake checkpoint availability must not be reported."""
        control_dir = tmp_path / "output" / "control"
        _write_blocked_artifacts(control_dir)
        build_generation_gate_package(str(tmp_path))

        # Runtime blocker must explicitly forbid fake availability
        blocker_path = control_dir / "generation_runtime_blocker_report.json"
        with open(blocker_path) as f:
            blocker = json.load(f)
        assert blocker.get("fake_availability_forbidden") is True
        assert blocker.get("runtime_execution_forbidden") is True
