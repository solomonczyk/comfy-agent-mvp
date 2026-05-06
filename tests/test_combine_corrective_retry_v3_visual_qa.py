"""Tests for combine corrective retry V3 visual QA.

RC-COMBINE-V2-1341-1400 — Test structured visual QA on retry V3 asset.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_run_corrective_retry_v3_visual_qa_generates_structured_verdict(tmp_path):
    """Test that visual QA generates structured verdict."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify visual QA report
    report_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json"
    assert report_path.exists()
    
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["visual_qa_executed"] == True
    assert report["qa_verdict"] in ["qa_passed", "qa_failed"]
    assert report["operator_review_required"] == True
    assert report["source_asset"] == "output/assets/retry_v3_generated_1234567890_00001_.png"


def test_visual_qa_reads_canonical_project_asset(tmp_path):
    """Test that visual QA reads canonical project asset."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight with canonical asset path
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify asset was read
    report_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["asset_exists"] == True
    assert report["asset_readable"] == True
    assert report["source_asset"] == "output/assets/retry_v3_generated_1234567890_00001_.png"


def test_visual_qa_no_generation(tmp_path):
    """Test that visual QA does not perform generation."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation
    report_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["generation_performed"] == False
    assert report["comfyui_execution"] == False
    assert report["retry_attempted"] == False


def test_visual_qa_no_retry(tmp_path):
    """Test that visual QA does not attempt retry."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify no retry
    report_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["retry_attempted"] == False


def test_visual_qa_no_assembly(tmp_path):
    """Test that visual QA does not execute assembly."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify no assembly
    report_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_report.json"
    with open(report_path, 'r') as f:
        report = json.load(f)
    
    assert report["assembly_executed"] == False
    assert report["downstream_executed"] == False
    assert report["production_accepted"] == False


def test_visual_qa_creates_failure_audit(tmp_path):
    """Test that visual QA creates failure audit."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create preflight
    preflight = {
        "source_asset": "output/assets/retry_v3_generated_1234567890_00001_.png",
        "visual_qa_entry_allowed": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json", 'w') as f:
        json.dump(preflight, f)
    
    # Create stub asset
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert success
    assert result == 0
    
    # Verify failure audit created
    audit_path = control_dir / "combine_v2_corrective_retry_v3_failure_audit.json"
    assert audit_path.exists()
    
    with open(audit_path, 'r') as f:
        audit = json.load(f)
    
    assert audit["qa_verdict"] in ["qa_passed", "qa_failed"]
    assert "failure_categories" in audit


def test_visual_qa_missing_preflight(tmp_path):
    """Test error when preflight is missing."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args without preflight
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa(args)
    
    # Assert failure
    assert result == 1
