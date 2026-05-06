"""Tests for combine assembly plan V3.

RC-COMBINE-V2-1461-1520 — Test assembly plan V3.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_assembly_plan_created_after_preflight(tmp_path):
    """Test that assembly plan is created after successful preflight."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight result
    assembly_preflight = {
        "assembly_entry_allowed": True,
        "source_asset": "output/assets/test_asset.png",
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify assembly plan created
    plan_path = control_dir / "combine_v2_assembly_plan_v3.json"
    assert plan_path.exists()
    
    with open(plan_path, 'r') as f:
        plan = json.load(f)
    
    assert plan["assembly_plan_created"] == True
    assert plan["assembly_plan_type"] == "single_visual_asset_assembly_plan_v3"


def test_assembly_input_manifest_created(tmp_path):
    """Test that assembly input manifest is created."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight result
    assembly_preflight = {
        "assembly_entry_allowed": True,
        "source_asset": "output/assets/test_asset.png",
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify input manifest created
    manifest_path = control_dir / "combine_v2_assembly_input_manifest_v3.json"
    assert manifest_path.exists()
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["manifest_type"] == "single_visual_asset_assembly_manifest_v3"
    assert manifest["source_asset"] == "output/assets/test_asset.png"
    assert manifest["source_asset_sha256"] == "abc123"


def test_assembly_plan_requires_operator_authorization(tmp_path):
    """Test that assembly plan requires operator authorization."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight result
    assembly_preflight = {
        "assembly_entry_allowed": True,
        "source_asset": "output/assets/test_asset.png",
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify authorization required
    plan_path = control_dir / "combine_v2_assembly_plan_v3.json"
    with open(plan_path, 'r') as f:
        plan = json.load(f)
    
    assert plan["assembly_requires_operator_authorization"] == True
    assert plan["assembly_allowed"] == False


def test_assembly_plan_not_executed(tmp_path):
    """Test that assembly plan does not execute assembly."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight result
    assembly_preflight = {
        "assembly_entry_allowed": True,
        "source_asset": "output/assets/test_asset.png",
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify assembly not executed
    plan_path = control_dir / "combine_v2_assembly_plan_v3.json"
    with open(plan_path, 'r') as f:
        plan = json.load(f)
    
    assert plan["assembly_executed"] == False
    assert plan["downstream_executed"] == False
    assert plan["production_accepted"] == False


def test_assembly_plan_next_action_authorization_required(tmp_path):
    """Test that next action is operator_assembly_authorization_required."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight result
    assembly_preflight = {
        "assembly_entry_allowed": True,
        "source_asset": "output/assets/test_asset.png",
        "source_asset_sha256": "abc123",
        "source_asset_width": 100,
        "source_asset_height": 100,
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify next action
    plan_path = control_dir / "combine_v2_assembly_plan_v3.json"
    with open(plan_path, 'r') as f:
        plan = json.load(f)
    
    assert plan["next_allowed_action"] == "operator_assembly_authorization_required"


def test_assembly_plan_fails_without_preflight(tmp_path):
    """Test that assembly plan fails without preflight."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Don't create preflight
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert failure
    assert result == 1


def test_assembly_plan_fails_with_failed_preflight(tmp_path):
    """Test that assembly plan fails with failed preflight."""
    from app.cli import combine_build_assembly_plan_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly preflight with entry not allowed
    assembly_preflight = {
        "assembly_entry_allowed": False,
        "source_asset": "output/assets/test_asset.png",
    }
    with open(control_dir / "combine_v2_assembly_preflight_v3.json", 'w') as f:
        json.dump(assembly_preflight, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_assembly_plan_v3(args)
    
    # Assert failure
    assert result == 1
