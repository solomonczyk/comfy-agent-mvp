"""Tests for combine corrective retry V4 output collector audit."""

import json
import pytest
from pathlib import Path
import argparse


def test_output_collector_audit_detects_stub_generation(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_output_collector
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": True, "collector_reliability_guard_preserved": True, "output_path_contract_preserved": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"], "stub_asset": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "pending"}, {"event": "comfyui_execution", "stub": True}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    stub_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    stub_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_output_collector(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_output_collector_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["stub_generation_detected"] == True
    assert audit["failure_mode"] == "stub_generation_layer"
    assert audit["collector_failure_confirmed"] == True


def test_output_collector_audit_detects_output_collection_failure(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_output_collector
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False, "collector_reliability_guard_preserved": True, "output_path_contract_preserved": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    outputs_manifest = {"generated_assets": ["output/assets/shot02_v4_20260506_120000_000.png"]}
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    generation_trace = {"events": [{"event": "output_collection", "status": "pending"}]}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    post_submit_validation = {"validation_passed": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_output_collector(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_output_collector_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["output_collection_status"] == "pending"
    assert audit["failure_mode"] == "output_collection_not_executed"


def test_output_collector_audit_detects_stub_asset(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_output_collector
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False, "collector_reliability_guard_preserved": True, "output_path_contract_preserved": True}
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
    result = combine_audit_corrective_retry_v4_output_collector(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_output_collector_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["stub_asset_detected"] == True
    assert audit["v4_asset_corrupted"] == True
    assert audit["v4_asset_size_bytes"] < 1024


def test_output_collector_audit_post_submit_validation_failure(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_output_collector
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False, "collector_reliability_guard_preserved": True, "output_path_contract_preserved": True}
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
    
    valid_asset = assets_dir / "shot02_v4_20260506_120000_000.png"
    valid_asset.write_bytes(b'\x89PNG\r\n\x1a\n' + b'\x00' * 5000)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_output_collector(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_output_collector_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["post_submit_validation_passed"] == False
    assert audit["failure_mode"] == "post_submit_validation_failed"
