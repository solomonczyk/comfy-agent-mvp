"""Tests for combine corrective retry V3 operator review packet.

RC-COMBINE-V2-1341-1400 — Test operator review packet creation for retry V3.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_build_corrective_retry_v3_operator_review_packet(tmp_path):
    """Test operator review packet creation."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create visual QA report
    visual_qa_report = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "asset_exists": True,
        "asset_readable": True,
        "width": 1024,
        "height": 1024,
        "sha256_present": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(visual_qa_report, f)
    
    # Create failure audit
    failure_audit = {
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "failures_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_failure_audit.json", 'w') as f:
        json.dump(failure_audit, f)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
        "second_generation_attempted": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert success
    assert result == 0
    
    # Verify operator review packet
    packet_path = control_dir / "combine_v2_corrective_retry_v3_operator_review_packet.json"
    assert packet_path.exists()
    
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert packet["operator_review_packet_created"] == True
    assert packet["source_asset"] == "output/assets/retry_v3_generated_1234567890_00001_.png"
    assert packet["qa_verdict"] == "qa_passed"
    assert packet["operator_review_required"] == True
    assert packet["next_allowed_action"] == "operator_visual_review"


def test_operator_review_packet_includes_boundary_enforcement(tmp_path):
    """Test that operator review packet includes boundary enforcement."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required artifacts
    visual_qa_report = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "asset_exists": True,
        "asset_readable": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(visual_qa_report, f)
    
    failure_audit = {"qa_verdict": "qa_passed", "failure_categories": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_failure_audit.json", 'w') as f:
        json.dump(failure_audit, f)
    
    preflight = {"source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
        "second_generation_attempted": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert success
    assert result == 0
    
    # Verify boundary enforcement
    packet_path = control_dir / "combine_v2_corrective_retry_v3_operator_review_packet.json"
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert packet["boundary_enforcement"]["new_generation"] == False
    assert packet["boundary_enforcement"]["new_comfyui_submit"] == False
    assert packet["boundary_enforcement"]["retry_submit"] == False
    assert packet["boundary_enforcement"]["second_generation_attempt"] == False
    assert packet["boundary_enforcement"]["visual_qa_only"] == True
    assert packet["boundary_enforcement"]["operator_visual_acceptance"] == False
    assert packet["boundary_enforcement"]["assembly"] == False
    assert packet["boundary_enforcement"]["downstream"] == False
    assert packet["boundary_enforcement"]["production_accepted"] == False


def test_operator_review_packet_no_generation(tmp_path):
    """Test that operator review packet shows no generation."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required artifacts
    visual_qa_report = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "asset_exists": True,
        "asset_readable": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(visual_qa_report, f)
    
    failure_audit = {"qa_verdict": "qa_passed", "failure_categories": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_failure_audit.json", 'w') as f:
        json.dump(failure_audit, f)
    
    preflight = {"source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
        "second_generation_attempted": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation in packet
    packet_path = control_dir / "combine_v2_corrective_retry_v3_operator_review_packet.json"
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert packet["generation_performed"] == False
    assert packet["comfyui_execution"] == False
    assert packet["retry_attempted"] == False


def test_operator_review_packet_missing_visual_qa_report(tmp_path):
    """Test error when visual QA report is missing."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args without visual QA report
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert failure
    assert result == 1


def test_operator_review_packet_includes_qa_summary(tmp_path):
    """Test that operator review packet includes QA summary."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required artifacts
    visual_qa_report = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "asset_exists": True,
        "asset_readable": True,
        "width": 1024,
        "height": 1024,
        "sha256_present": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(visual_qa_report, f)
    
    failure_audit = {"qa_verdict": "qa_passed", "failure_categories": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_failure_audit.json", 'w') as f:
        json.dump(failure_audit, f)
    
    preflight = {"source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
        "second_generation_attempted": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert success
    assert result == 0
    
    # Verify QA summary
    packet_path = control_dir / "combine_v2_corrective_retry_v3_operator_review_packet.json"
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert "qa_summary" in packet
    assert packet["qa_summary"]["asset_exists"] == True
    assert packet["qa_summary"]["asset_readable"] == True
    assert packet["qa_summary"]["width"] == 1024
    assert packet["qa_summary"]["height"] == 1024
    assert packet["qa_summary"]["sha256_present"] == True


def test_operator_review_packet_includes_generation_summary(tmp_path):
    """Test that operator review packet includes generation summary."""
    from app.cli import combine_build_corrective_retry_v3_operator_review_packet
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required artifacts
    visual_qa_report = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "qa_verdict": "qa_passed",
        "failure_categories": [],
        "asset_exists": True,
        "asset_readable": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json", 'w') as f:
        json.dump(visual_qa_report, f)
    
    failure_audit = {"qa_verdict": "qa_passed", "failure_categories": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_failure_audit.json", 'w') as f:
        json.dump(failure_audit, f)
    
    preflight = {"source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png"}
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
        "second_generation_attempted": False,
        "max_generations": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_operator_review_packet(args)
    
    # Assert success
    assert result == 0
    
    # Verify generation summary
    packet_path = control_dir / "combine_v2_corrective_retry_v3_operator_review_packet.json"
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert "generation_summary" in packet
    assert packet["generation_summary"]["generation_performed"] == True
    assert packet["generation_summary"]["retry_attempted"] == True
    assert packet["generation_summary"]["second_generation_attempted"] == False
    assert packet["generation_summary"]["max_generations"] == 1
