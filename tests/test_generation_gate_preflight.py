"""Test generation gate preflight evaluation — various readiness scenarios.

RC-COMBINE-V2-86001-94000
"""

import json
import os
from pathlib import Path

import pytest

from app.generation_gate import evaluate_generation_gate


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

SHOT_CONTRACT = {
    "shot_id": "shot_001",
    "workflow_family": "sdxl_txt2img",
    "expected_runtime_executor": "comfyui",
    "expected_generation_gate": "generation_authorization_required",
    "max_generations_per_gate": 1,
    "forbidden_fake_prompt_id": True,
    "forbidden_fake_asset": True,
}


def _make_submitted_workflow_contract() -> dict:
    return {
        "task_id": "RC-COMBINE-V2-70001-86000",
        "per_shot_workflow_contracts": [SHOT_CONTRACT.copy() for _ in range(12)],
        "total_shot_contracts": 12,
        "expected_runtime_executor": "comfyui",
        "expected_generation_gate": "generation_authorization_required",
        "max_generations_per_gate": 1,
        "forbidden_fake_prompt_id": True,
        "forbidden_fake_asset": True,
        "comfyui_submit_executed": False,
        "workflow_execution_performed": False,
    }


def _make_workflow_validation_report() -> dict:
    return {
        "task_id": "RC-COMBINE-V2-70001-86000",
        "ksampler_required": True,
        "saveimage_required": True,
        "filename_prefix_policy_defined": True,
        "legacy_512_workflow_blocked": True,
        "stub_workflow_blocked": True,
        "workflow_execution_performed": False,
        "comfyui_submit_executed": False,
        "generation_performed": False,
        "validation_passed": True,
    }


def _make_asset_verification_report(available: bool = True) -> dict:
    result = {
        "task_id": "RC-COMBINE-V2-70001-86000",
        "required_assets_available": available,
        "required_assets_blocked": not available,
        "missing_assets_not_hidden": True,
    }
    if not available:
        result["errors"] = ["Required assets missing: ['checkpoint_sdxl_base']"]
    return result


def _make_asset_blocker_report(active: bool = True) -> dict:
    return {
        "blocker_id": "asset_blocker_test",
        "missing_or_invalid_asset": "checkpoint_sdxl_base",
        "affected_shots": ["shot_001"],
        "next_required_operator_manual_gate": "manual_asset_resolution_required",
        "generation_preflight_allowed": not active,
    }


@pytest.fixture
def blocked_project(tmp_path) -> str:
    """Setup a project with active asset blocker."""
    control_dir = tmp_path / "output" / "control"
    wf_assets_dir = control_dir / "workflow_assets"
    wf_assets_dir.mkdir(parents=True)

    # Blocked state artifacts
    with open(wf_assets_dir / "submitted_workflow_contract.json", "w") as f:
        json.dump(_make_submitted_workflow_contract(), f)
    with open(wf_assets_dir / "workflow_validation_report.json", "w") as f:
        json.dump(_make_workflow_validation_report(), f)
    with open(wf_assets_dir / "asset_requirements.json", "w") as f:
        json.dump({"task_id": "test", "total_requirements": 1}, f)
    with open(wf_assets_dir / "asset_resolution_plan.json", "w") as f:
        json.dump({"task_id": "test", "missing_assets": ["checkpoint_sdxl_base"]}, f)
    with open(wf_assets_dir / "asset_verification_report.json", "w") as f:
        json.dump(_make_asset_verification_report(available=False), f)
    with open(wf_assets_dir / "asset_blocker_report.json", "w") as f:
        json.dump(_make_asset_blocker_report(active=True), f)
    with open(wf_assets_dir / "generation_preflight_operator_review_packet.json", "w") as f:
        json.dump({
            "has_asset_blocker": True,
            "generation_preflight_ready": False,
        }, f)

    return str(tmp_path)


@pytest.fixture
def ready_project(tmp_path) -> str:
    """Setup a project with all assets ready."""
    control_dir = tmp_path / "output" / "control"
    wf_assets_dir = control_dir / "workflow_assets"
    wf_assets_dir.mkdir(parents=True)

    with open(wf_assets_dir / "submitted_workflow_contract.json", "w") as f:
        json.dump(_make_submitted_workflow_contract(), f)
    with open(wf_assets_dir / "workflow_validation_report.json", "w") as f:
        json.dump(_make_workflow_validation_report(), f)
    with open(wf_assets_dir / "asset_requirements.json", "w") as f:
        json.dump({"task_id": "test", "total_requirements": 1}, f)
    with open(wf_assets_dir / "asset_resolution_plan.json", "w") as f:
        json.dump({"task_id": "test", "missing_assets": []}, f)
    with open(wf_assets_dir / "asset_verification_report.json", "w") as f:
        json.dump(_make_asset_verification_report(available=True), f)
    # No asset_blocker_report — all good
    with open(wf_assets_dir / "generation_preflight_operator_review_packet.json", "w") as f:
        json.dump({
            "has_asset_blocker": False,
            "generation_preflight_ready": True,
        }, f)

    return str(tmp_path)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGenerationGatePreflight:
    """Test the evaluate_generation_gate function with various scenarios."""

    def test_blocked_by_missing_assets(self, blocked_project):
        """Active asset blocker should result in blocked_by_missing_assets."""
        result = evaluate_generation_gate(blocked_project)
        assert result["generation_gate_decision"] == "blocked_by_missing_assets"
        assert result["generation_can_be_authorized"] is False
        assert result["generation_can_execute_now"] is False
        assert result["comfyui_submit_allowed"] is False
        assert result["asset_blocker_active"] is True
        assert len(result["blockers"]) > 0

    def test_ready_for_authorization(self, ready_project):
        """All assets ready should result in ready_for_operator_authorization."""
        result = evaluate_generation_gate(ready_project)
        assert result["generation_gate_decision"] == "ready_for_operator_authorization"
        assert result["generation_can_be_authorized"] is True
        assert result["generation_can_execute_now"] is False
        assert result["comfyui_submit_allowed"] is False
        assert result["asset_blocker_active"] is False

    def test_missing_workflow_contract(self, tmp_path):
        """Missing workflow contract should be detected."""
        control_dir = tmp_path / "output" / "control"
        wf_assets_dir = control_dir / "workflow_assets"
        wf_assets_dir.mkdir(parents=True)

        # Create validation report but no workflow contract
        with open(wf_assets_dir / "workflow_validation_report.json", "w") as f:
            json.dump(_make_workflow_validation_report(), f)
        with open(wf_assets_dir / "asset_requirements.json", "w") as f:
            json.dump({"task_id": "test"}, f)

        result = evaluate_generation_gate(str(tmp_path))
        assert result["generation_gate_decision"] == "invalid_workflow_contract"
        assert result["generation_can_be_authorized"] is False

    def test_contract_with_prompt_id_invalid(self, blocked_project):
        """Contract claiming prompt_id must be rejected."""
        control_dir = Path(blocked_project) / "output" / "control" / "workflow_assets"
        contract = _make_submitted_workflow_contract()
        contract["prompt_id"] = "fake-prompt-id"
        with open(control_dir / "submitted_workflow_contract.json", "w") as f:
            json.dump(contract, f)

        result = evaluate_generation_gate(blocked_project)
        assert result["contract_valid"] is False
        assert any(b["type"] == "invalid_workflow_contract" for b in result["blockers"])

    def test_contract_with_generated_assets_invalid(self, blocked_project):
        """Contract listing generated assets must be rejected."""
        control_dir = Path(blocked_project) / "output" / "control" / "workflow_assets"
        contract = _make_submitted_workflow_contract()
        contract["generated_assets"] = ["output/assets/fake.png"]
        with open(control_dir / "submitted_workflow_contract.json", "w") as f:
            json.dump(contract, f)

        result = evaluate_generation_gate(blocked_project)
        assert result["contract_valid"] is False
        assert any(b["type"] == "invalid_workflow_contract" for b in result["blockers"])

    def test_evaluation_forbidden_flags(self, blocked_project):
        """Gate evaluation must never claim generation performed."""
        result = evaluate_generation_gate(blocked_project)
        assert result["generation_can_be_authorized"] is False
        assert result["generation_can_execute_now"] is False
        assert result["comfyui_submit_allowed"] is False
