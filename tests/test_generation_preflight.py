"""
Tests for app/visual_generation/preflight.py
RC-COMBINE-V2-FIRST-CONTROLLED-FRESH-VISUAL-CANDIDATE-001
"""
import json
import pytest
from pathlib import Path
from unittest.mock import patch


@pytest.fixture
def project_root(tmp_path):
    control_dir = tmp_path / "output" / "control"
    strategy_dir = control_dir / "fresh_visual_strategy"
    gate_dir = control_dir / "controlled_visual_generation_gate"
    review_dir = control_dir / "fresh_visual_strategy_operator_review"
    strategy_dir.mkdir(parents=True)
    gate_dir.mkdir(parents=True)
    review_dir.mkdir(parents=True)

    # Strategy readiness
    readiness = {
        "readiness_checklist": {"all_artifacts_valid": True},
        "policy_readiness": {"qa_repairability_gate_active": True},
    }
    (strategy_dir / "fresh_visual_strategy_readiness_report.json").write_text(
        json.dumps(readiness), encoding="utf-8"
    )

    # Operator review proof
    proof = {
        "decision_valid": True,
        "operator_verdict": "accepted_for_controlled_generation_gate_planning",
        "production_accepted": False,
    }
    (review_dir / "operator_review_proof.json").write_text(
        json.dumps(proof), encoding="utf-8"
    )

    # Repairability policy
    rep_policy = {
        "repairability_aware_visual_policy": {"qa_repairability_gate_required": True}
    }
    (strategy_dir / "repairability_aware_visual_policy.json").write_text(
        json.dumps(rep_policy), encoding="utf-8"
    )

    # Workflow
    workflow_data = {"nodes": []}
    workflow_path = control_dir / "workflow.json"
    workflow_path.write_text(json.dumps(workflow_data), encoding="utf-8")
    wf_report = {
        "workflow_selected": True,
        "workflow_file": str(workflow_path),
        "workflow_validation_passed": True,
    }
    (gate_dir / "workflow_selection_report.json").write_text(
        json.dumps(wf_report), encoding="utf-8"
    )

    # Model report
    model_report = {"all_models_available": True}
    (gate_dir / "model_asset_verification_report.json").write_text(
        json.dumps(model_report), encoding="utf-8"
    )

    # Repairability binding
    rep_binding = {"policy_loaded": True}
    (gate_dir / "repairability_policy_binding.json").write_text(
        json.dumps(rep_binding), encoding="utf-8"
    )

    # Negative references
    neg_policy = {
        "negative_reference_policy": {
            "documented_negative_references": {"defect_1": {}, "defect_2": {}}
        }
    }
    (strategy_dir / "negative_reference_policy.json").write_text(
        json.dumps(neg_policy), encoding="utf-8"
    )

    return tmp_path


def test_preflight_blocks_when_comfyui_down(project_root):
    from app.visual_generation.preflight import PreflightValidator

    validator = PreflightValidator(project_root)
    passed, report = validator.validate(comfyui_host="127.0.0.1", comfyui_port=19999)

    assert passed is False
    assert any("ComfyUI" in b for b in report["blockers"])
    blocker_path = (
        project_root
        / "output"
        / "control"
        / "controlled_visual_generation_gate"
        / "generation_preflight_blocker.json"
    )
    assert blocker_path.exists()


def test_preflight_passes_when_all_checks_ok(project_root):
    from app.visual_generation.preflight import PreflightValidator

    validator = PreflightValidator(project_root)
    with patch.object(validator, "_check_comfyui", return_value=True):
        passed, report = validator.validate()

    assert passed is True
    assert report["blockers"] == []
    assert (
        project_root
        / "output"
        / "control"
        / "controlled_visual_generation_gate"
        / "generation_preflight_report.json"
    ).exists()


def test_preflight_blocks_missing_operator_acceptance(project_root):
    from app.visual_generation.preflight import PreflightValidator

    proof_path = (
        project_root
        / "output"
        / "control"
        / "fresh_visual_strategy_operator_review"
        / "operator_review_proof.json"
    )
    proof_path.unlink()

    validator = PreflightValidator(project_root)
    with patch.object(validator, "_check_comfyui", return_value=True):
        passed, report = validator.validate()

    assert passed is False
    assert any("operator_strategy_acceptance" in b for b in report["blockers"])


def test_preflight_blocks_missing_models(project_root):
    from app.visual_generation.preflight import PreflightValidator

    model_report_path = (
        project_root
        / "output"
        / "control"
        / "controlled_visual_generation_gate"
        / "model_asset_verification_report.json"
    )
    model_report_path.write_text(
        json.dumps({"all_models_available": False}), encoding="utf-8"
    )

    validator = PreflightValidator(project_root)
    with patch.object(validator, "_check_comfyui", return_value=True):
        passed, report = validator.validate()

    assert passed is False
    assert any("models" in b for b in report["blockers"])


def test_preflight_report_locked_fields(project_root):
    from app.visual_generation.preflight import PreflightValidator

    validator = PreflightValidator(project_root)
    with patch.object(validator, "_check_comfyui", return_value=True):
        _, report = validator.validate()

    assert report["checks"]["generation_count_before_run"] == 0
    assert report["checks"]["max_generations"] == 1
