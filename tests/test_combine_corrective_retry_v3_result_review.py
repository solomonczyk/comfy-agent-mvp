"""Tests for combine corrective retry V3 result review.

RC-COMBINE-V2-1281-1340 — Test result review after one controlled retry V3 generation.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_review_corrective_retry_v3_result_success_branch(tmp_path):
    """Test result review with success branch."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with assets
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest with assets
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify result review artifact
    review_path = control_dir / "combine_v2_corrective_retry_v3_result_review.json"
    assert review_path.exists()
    
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["branch_selected"] == "success"
    assert result_review["generated_assets_count"] == 1
    assert result_review["result_review_executed"] == True
    assert result_review["next_allowed_action"] == "corrective_retry_v3_visual_qa_preflight_required"


def test_combine_review_corrective_retry_v3_result_failed_collection_branch(tmp_path):
    """Test result review with failed collection branch."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result without assets
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest with zero assets
    outputs_manifest = {
        "asset_count": 0,
        "generated_assets": [],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify result review artifact
    review_path = control_dir / "combine_v2_corrective_retry_v3_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["branch_selected"] == "failed_collection"
    assert result_review["generated_assets_count"] == 0
    assert result_review["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    assert result_review["result_review_executed"] == True
    assert result_review["next_allowed_action"] == "corrective_retry_v3_result_review_required"


def test_result_review_missing_generation_result(tmp_path):
    """Test error when generation result is missing."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args without generation result
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert failure
    assert result == 1


def test_result_review_updates_artifact_index(tmp_path):
    """Test that result review updates artifact index."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifact index updated
    artifact_index_path = control_dir / "artifact_index.json"
    assert artifact_index_path.exists()
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["corrective_retry_v3_result_review_executed"] == True
    assert artifact_index["branch_selected"] == "success"
    assert artifact_index["generated_assets_count"] == 1


def test_result_review_no_visual_qa(tmp_path):
    """Test that visual QA is not executed during result review."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify visual QA not executed
    review_path = control_dir / "combine_v2_corrective_retry_v3_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["visual_qa_executed"] == False


def test_result_review_no_assembly(tmp_path):
    """Test that assembly is not executed during result review."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify assembly not executed
    review_path = control_dir / "combine_v2_corrective_retry_v3_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["assembly_executed"] == False
    assert result_review["downstream_executed"] == False
    assert result_review["production_accepted"] == False


def test_result_review_generation_not_performed(tmp_path):
    """Test result review when generation was not performed."""
    from app.cli import combine_review_corrective_retry_v3_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with generation_performed=False
    generation_result = {
        "generation_performed": False,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest with zero assets
    outputs_manifest = {
        "asset_count": 0,
        "generated_assets": [],
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
    result = combine_review_corrective_retry_v3_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify failed collection branch
    review_path = control_dir / "combine_v2_corrective_retry_v3_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["branch_selected"] == "failed_collection"
    assert result_review["generated_assets_count"] == 0
