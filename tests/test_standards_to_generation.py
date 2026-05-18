"""Tests for Standards to Fresh Visual Controlled Generation.

RC-COMBINE-V2-STANDARDS-TO-FRESH-VISUAL-CONTROLLED-GENERATION-001
"""

import json
from pathlib import Path
import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"


def test_preflight_state_report_exists():
    """Test that preflight state report exists."""
    report = CONTROL_DIR / "standards_to_generation" / "preflight_state_report.json"
    assert report.exists(), "Preflight state report must exist"
    data = json.loads(report.read_text())
    assert data["preflight_passed"] is True
    assert data["standards_pack_valid"] is True


def test_standards_integration_complete():
    """Test that standards integration is complete."""
    report = CONTROL_DIR / "standards_integration" / "standards_integration_validation_report.json"
    assert report.exists(), "Standards integration validation report must exist"
    data = json.loads(report.read_text())
    assert data["valid"] is True


def test_script_supervisor_artifacts_complete():
    """Test that Script Supervisor artifacts are complete."""
    contract = CONTROL_DIR / "script_supervisor" / "script_supervisor_agent_contract.json"
    assert contract.exists(), "Script Supervisor contract must exist"
    data = json.loads(contract.read_text())
    assert data["role"] == "script_supervisor"
    assert "generation" in data["forbidden_actions"]


def test_corrective_plan_validation():
    """Test that corrective plan is validated."""
    report = CONTROL_DIR / "fresh_visual_corrective_generation" / "corrective_plan_validation_report.json"
    assert report.exists(), "Corrective plan validation report must exist"
    data = json.loads(report.read_text())
    assert data["validation_status"] == "passed"
    assert data["ready_for_generation"] is True


def test_generation_gate_created():
    """Test that generation gate is created."""
    gate = CONTROL_DIR / "fresh_visual_corrective_generation" / "corrective_generation_gate_package.json"
    assert gate.exists(), "Generation gate package must exist"
    data = json.loads(gate.read_text())
    assert data["generation_authorized"] is True
    assert data["max_generations"] == 1
    assert data["blind_retry_allowed"] is False


def test_generation_preflight_passed():
    """Test that generation preflight passed."""
    report = CONTROL_DIR / "fresh_visual_corrective_generation" / "generation_preflight_report.json"
    assert report.exists(), "Generation preflight report must exist"
    data = json.loads(report.read_text())
    assert data["preflight_passed"] is True


def test_generation_executed_once():
    """Test that exactly one generation was executed."""
    report = CONTROL_DIR / "fresh_visual_corrective_generation" / "generation_execution_report.json"
    assert report.exists(), "Generation execution report must exist"
    data = json.loads(report.read_text())
    assert data["generation_count"] == 1
    assert data["max_generations"] == 1
    assert data["second_generation_attempted"] is False
    assert data["blind_retry_attempted"] is False


def test_generated_asset_manifest():
    """Test that generated asset manifest exists with real asset."""
    manifest = CONTROL_DIR / "fresh_visual_corrective_generation" / "generated_asset_manifest.json"
    assert manifest.exists(), "Generated asset manifest must exist"
    data = json.loads(manifest.read_text())
    assert data["generated_assets_count"] == 1
    assert data["assets"][0]["stub_asset"] is False


def test_state_updated():
    """Test that state is updated to operator_visual_review_required."""
    state = CONTROL_DIR / "state.json"
    assert state.exists(), "State file must exist"
    data = json.loads(state.read_text())
    assert data["current_state"] == "operator_visual_review_required"
    assert data["generation_count"] == 1
    assert data["generation_performed"] is True


def test_forbidden_actions_enforced():
    """Test that forbidden actions are enforced."""
    result = CONTROL_DIR / "fresh_visual_corrective_generation" / "generation_result_review.json"
    assert result.exists(), "Generation result review must exist"
    data = json.loads(result.read_text())
    assert data["visual_qa_acceptance_executed"] is False
    assert data["assembly_executed"] is False
    assert data["downstream_executed"] is False
    assert data["production_accepted"] is False


def test_stop_after_generation():
    """Test that stop after generation policy is enforced."""
    policy = CONTROL_DIR / "fresh_visual_corrective_generation" / "corrective_generation_stop_policy.json"
    assert policy.exists(), "Stop policy must exist"
    data = json.loads(policy.read_text())
    assert data["next_state_after_stop"] == "operator_visual_review_required"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
