"""Tests for combine corrective retry V3 visual QA preflight.

RC-COMBINE-V2-1341-1400 — Test visual QA preflight for retry V3 asset.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_run_corrective_retry_v3_visual_qa_preflight_resolves_asset(tmp_path):
    """Test that preflight resolves asset from manifest."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest with asset
    outputs_manifest = {
        "generated_assets": ["output/assets/retry_v3_generated_1234567890_00001_.png"],
        "asset_count": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create stub asset file
    asset_path = assets_dir / "retry_v3_generated_1234567890_00001_.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert success
    assert result == 0
    
    # Verify preflight artifact
    preflight_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json"
    assert preflight_path.exists()
    
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["source_asset_resolved_from_manifest"] == True
    assert preflight["source_asset"] == "output/assets/retry_v3_generated_1234567890_00001_.png"
    assert preflight["manifest_generated_assets_count"] == 1


def test_visual_qa_preflight_requires_manifest_asset(tmp_path):
    """Test that preflight requires manifest asset."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest with zero assets
    outputs_manifest = {
        "generated_assets": [],
        "asset_count": 0,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert failure
    assert result == 1


def test_visual_qa_preflight_requires_filesystem_asset(tmp_path):
    """Test that preflight requires filesystem asset."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest with asset but don't create file
    outputs_manifest = {
        "generated_assets": ["output/assets/retry_v3_generated_1234567890_00001_.png"],
        "asset_count": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert success (preflight should complete but mark asset as not readable)
    assert result == 0
    
    # Verify preflight
    preflight_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["filesystem_asset_exists"] == False
    assert preflight["asset_readable"] == False
    assert preflight["visual_qa_entry_allowed"] == False


def test_collector_manifest_consistency_checked(tmp_path):
    """Test that collector manifest consistency is checked."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest with canonical path
    outputs_manifest = {
        "generated_assets": ["output/assets/retry_v3_generated_1234567890_00001_.png"],
        "asset_count": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
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
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert success
    assert result == 0
    
    # Verify manifest consistency checked
    preflight_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["manifest_references_canonical_project_asset"] == True
    assert preflight["collector_manifest_consistent"] == True
    assert preflight["collector_reliability_guard_preserved"] == True


def test_visual_qa_preflight_no_generation(tmp_path):
    """Test that preflight does not perform generation."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest
    outputs_manifest = {
        "generated_assets": ["output/assets/retry_v3_generated_1234567890_00001_.png"],
        "asset_count": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
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
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation
    preflight_path = control_dir / "combine_v2_corrective_retry_v3_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["generation_performed"] == False
    assert preflight["comfyui_execution"] == False
    assert preflight["retry_attempted"] == False


def test_visual_qa_preflight_updates_artifact_index(tmp_path):
    """Test that preflight updates artifact index."""
    from app.cli import combine_run_corrective_retry_v3_visual_qa_preflight
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create outputs manifest
    outputs_manifest = {
        "generated_assets": ["output/assets/retry_v3_generated_1234567890_00001_.png"],
        "asset_count": 1,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
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
    result = combine_run_corrective_retry_v3_visual_qa_preflight(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifact index updated
    artifact_index_path = control_dir / "artifact_index.json"
    assert artifact_index_path.exists()
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["visual_qa_preflight_executed"] == True
    assert artifact_index["source_asset"] == "output/assets/retry_v3_generated_1234567890_00001_.png"
    assert artifact_index["visual_qa_entry_allowed"] == True
