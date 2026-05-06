"""Tests for combine corrective retry V4 workflow submit audit."""

import json
import pytest
from pathlib import Path
import argparse


def test_workflow_submit_audit_detects_stub_workflow(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_workflow_submit
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    implementation_package = {"real_workflow_included": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(implementation_package, f)
    
    generation_trace = {"workflow": {"nodes": [{"class_type": "KSampler"}]}}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_workflow_submit(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["workflow_stubbed"] == True
    assert audit["stub_or_fallback_workflow_detected"] == True
    assert audit["workflow_is_minimal"] == True


def test_workflow_submit_audit_detects_minimal_workflow(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_workflow_submit
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    implementation_package = {"real_workflow_included": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(implementation_package, f)
    
    generation_trace = {"workflow": {"nodes": [{"class_type": "KSampler"}, {"class_type": "SaveImage"}]}}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_workflow_submit(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["workflow_node_count"] == 2
    assert audit["workflow_is_minimal"] == True
    assert audit["stub_or_fallback_workflow_detected"] == True


def test_workflow_submit_audit_saveimage_not_configured(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_workflow_submit
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    implementation_package = {"real_workflow_included": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(implementation_package, f)
    
    generation_trace = {"workflow": {"nodes": [{"class_type": "KSampler"}, {"class_type": "EmptyLatentImage"}]}}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_workflow_submit(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["saveimage_configured"] == False
    assert audit["workflow_is_minimal"] == True


def test_workflow_submit_audit_saveimage_default_prefix(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_workflow_submit
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    implementation_package = {"real_workflow_included": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(implementation_package, f)
    
    generation_trace = {"workflow": {"nodes": [{"class_type": "KSampler"}, {"class_type": "SaveImage", "inputs": {"filename_prefix": "ComfyUI"}}]}}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_workflow_submit(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["saveimage_configured"] == True
    assert audit["saveimage_output_prefix"] == "ComfyUI"


def test_workflow_submit_audit_valid_workflow(tmp_path):
    from app.cli import combine_audit_corrective_retry_v4_workflow_submit
    
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    generation_result = {"stub_generation": False}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    implementation_package = {"real_workflow_included": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(implementation_package, f)
    
    nodes = [
        {"class_type": "EmptyLatentImage"},
        {"class_type": "CLIPTextEncode"},
        {"class_type": "KSampler"},
        {"class_type": "VAEDecode"},
        {"class_type": "SaveImage", "inputs": {"filename_prefix": "shot02_v4"}}
    ]
    generation_trace = {"workflow": {"nodes": nodes}}
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_trace.json", 'w') as f:
        json.dump(generation_trace, f)
    
    args = argparse.Namespace(project_root=str(project_root), shot_id="shot02", json=True)
    result = combine_audit_corrective_retry_v4_workflow_submit(args)
    
    assert result == 0
    audit_path = control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json"
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["workflow_stubbed"] == False
    assert audit["real_workflow_in_package"] == True
    assert audit["workflow_node_count"] == 5
    assert audit["workflow_is_minimal"] == False
    assert audit["stub_or_fallback_workflow_detected"] == False
