"""Tests for combine corrective retry V4 result reconciliation."""

import json
import pytest
from pathlib import Path
import argparse


def test_stub_v4_asset_detected(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"], "stub_asset": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["corrupted_manifest_asset_detected"] == True
    assert decision["new_generation_performed"] == False
    assert decision["visual_qa_executed"] == False
    assert decision["assembly_executed"] == False
    assert decision["downstream_executed"] == False
    assert decision["production_accepted"] == False


def test_valid_comfyui_output_recovery_branch_supported(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_corrupted.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    corrupted_asset = assets_dir / "shot02_v4_20260506_120000_corrupted.png"
    corrupted_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    valid_asset = assets_dir / "shot02_v4_20260506_120000_valid.png"
    valid_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 5000)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["valid_v4_asset_recovered"] == True
    assert decision["manifest_repaired"] == True


def test_no_valid_comfyui_output_branch_supported(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_corrupted.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    corrupted_asset = assets_dir / "shot02_v4_20260506_120000_corrupted.png"
    corrupted_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["valid_v4_asset_recovered"] == False
    assert decision["failure_code"] == "CORRECTIVE_RETRY_V4_NO_VALID_COMFYUI_OUTPUT"


def test_invalid_or_fallback_workflow_branch_supported(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["stub_generation_detected"] == True
    assert decision["failure_code"] == "CORRECTIVE_RETRY_V4_WORKFLOW_SUBMIT_INVALID"


def test_manifest_repair_requires_readable_asset(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_corrupted.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    corrupted_asset = assets_dir / "shot02_v4_20260506_120000_corrupted.png"
    corrupted_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    valid_asset = assets_dir / "shot02_v4_20260506_120000_valid.png"
    valid_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 5000)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["manifest_repaired"] == True
    assert decision["recovered_asset_readable"] == True


def test_stub_asset_cannot_be_marked_success(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"], "stub_asset": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["corrupted_manifest_asset_detected"] == True
    assert decision["valid_v4_asset_recovered"] == False
    assert decision["manifest_repaired"] == False
    assert decision["production_accepted"] == False


def test_visual_qa_not_executed(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["visual_qa_executed"] == False


def test_assembly_not_executed(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["assembly_executed"] == False


def test_downstream_not_executed(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["downstream_executed"] == False


def test_production_accepted_false(tmp_path):
    from app.cli import combine_reconcile_corrective_retry_v4_result
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"generation_attempts": 1, "workflow_submitted": True, "comfyui_execution": True, "stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "completed"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_reconcile_corrective_retry_v4_result(args)
    
    assert result == 0
    decision_path = control_dir / "combine_v2_corrective_retry_v4_result_reconciliation_decision.json"
    with open(decision_path, 'r') as f:
        decision = json.load(f)
    
    assert decision["production_accepted"] == False
