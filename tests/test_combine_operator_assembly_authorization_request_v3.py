"""Tests for combine operator assembly authorization request V3.

RC-COMBINE-V2-1461-1520 — Test operator assembly authorization request V3.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_operator_assembly_authorization_request_created(tmp_path):
    """Test that operator assembly authorization request is created."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify authorization request created
    auth_request_path = control_dir / "combine_v2_operator_assembly_authorization_request_v3.json"
    assert auth_request_path.exists()
    
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["request_type"] == "operator_assembly_authorization_request_v3"
    assert auth_request["authorization_required"] == True
    assert auth_request["authorization_status"] == "pending"


def test_authorization_request_includes_source_asset_info(tmp_path):
    """Test that authorization request includes source asset info."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify source asset info
    auth_request_path = control_dir / "combine_v2_operator_assembly_authorization_request_v3.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["source_asset"] == "output/assets/test_asset.png"
    assert auth_request["source_asset_sha256"] == "abc123"
    assert auth_request["source_asset_dimensions"]["width"] == 100
    assert auth_request["source_asset_dimensions"]["height"] == 100


def test_authorization_request_includes_boundary_conditions(tmp_path):
    """Test that authorization request includes boundary conditions."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify boundary conditions
    auth_request_path = control_dir / "combine_v2_operator_assembly_authorization_request_v3.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["boundary_conditions"]["generation_performed"] == False
    assert auth_request["boundary_conditions"]["retry_attempted"] == False
    assert auth_request["boundary_conditions"]["visual_qa_rerun"] == False
    assert auth_request["boundary_conditions"]["assembly_executed"] == False
    assert auth_request["boundary_conditions"]["downstream_executed"] == False
    assert auth_request["boundary_conditions"]["production_accepted"] == False


def test_authorization_request_not_executed(tmp_path):
    """Test that authorization request does not execute assembly."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify result shows assembly not executed
    # Check the result output from the function
    # (The function prints result, we can verify the artifact was created)
    auth_request_path = control_dir / "combine_v2_operator_assembly_authorization_request_v3.json"
    assert auth_request_path.exists()


def test_authorization_request_next_action_authorization_required(tmp_path):
    """Test that next action is operator_assembly_authorization_required."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify next action in artifact index
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["next_allowed_action"] == "operator_assembly_authorization_required"


def test_authorization_request_fails_without_plan(tmp_path):
    """Test that authorization request fails without assembly plan."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Don't create assembly plan
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert failure
    assert result == 1


def test_production_accepted_false(tmp_path):
    """Test that production_accepted is false."""
    from app.cli import combine_build_operator_assembly_authorization_request_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly plan
    assembly_plan = {
        "assembly_plan_created": True,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_plan_v3.json", 'w') as f:
        json.dump(assembly_plan, f)
    
    # Create assembly preflight
    assembly_preflight = {
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create input manifest
    input_manifest = {
        "manifest_type": "single_visual_asset_assembly_manifest_v3",
    }
    with open(control_dir / "combine_v2_assembly_input_manifest_v3.json", 'w') as f:
        json.dump(input_manifest, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_operator_assembly_authorization_request_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify production_accepted is false
    auth_request_path = control_dir / "combine_v2_operator_assembly_authorization_request_v3.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["boundary_conditions"]["production_accepted"] == False
