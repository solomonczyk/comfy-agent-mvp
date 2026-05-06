"""Tests for combine assembly preflight V3.

RC-COMBINE-V2-1461-1520 — Test assembly preflight V3.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_assembly_preflight_requires_operator_visual_acceptance(tmp_path):
    """Test that preflight requires operator visual acceptance V3."""
    from app.cli import combine_run_assembly_preflight_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create assembly readiness packet without operator acceptance
    assembly_readiness_packet = {
        "source_asset": "output/assets/test_asset.png",
        "visual_asset_accepted": True,
        "operator_visual_acceptance_confirmed": True,
    }
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'w') as f:
        json.dump(assembly_readiness_packet, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command - should fail due to missing operator acceptance
    result = combine_run_assembly_preflight_v3(args)
    
    # Assert failure
    assert result == 1


def test_assembly_preflight_requires_accepted_v3_asset(tmp_path):
    """Test that preflight requires accepted V3 asset."""
    from app.cli import combine_run_assembly_preflight_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operator acceptance V3
    operator_acceptance = {
        "source_asset": "output/assets/test_asset.png",
        "operator_visual_acceptance_confirmed": True,
        "visual_asset_accepted": True,
    }
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f)
    
    # Create assembly readiness packet with rejected asset
    assembly_readiness_packet = {
        "source_asset": "output/assets/test_asset.png",
        "visual_asset_accepted": False,
        "operator_visual_acceptance_confirmed": True,
    }
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'w') as f:
        json.dump(assembly_readiness_packet, f)
    
    # Create stub asset
    asset_path = assets_dir / "test_asset.png"
    asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_assembly_preflight_v3(args)
    
    # Assert failure
    assert result == 1
    
    # Verify preflight
    preflight_path = control_dir / "combine_v2_assembly_preflight_v3.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["assembly_entry_allowed"] == False
    assert preflight["visual_asset_accepted"] == False


def test_assembly_preflight_requires_existing_readable_asset(tmp_path):
    """Test that preflight requires existing and readable asset."""
    from app.cli import combine_run_assembly_preflight_v3
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operator acceptance V3
    operator_acceptance = {
        "source_asset": "output/assets/test_asset.png",
        "operator_visual_acceptance_confirmed": True,
        "visual_asset_accepted": True,
    }
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f)
    
    # Create assembly readiness packet
    assembly_readiness_packet = {
        "source_asset": "output/assets/test_asset.png",
        "visual_asset_accepted": True,
        "operator_visual_acceptance_confirmed": True,
    }
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'w') as f:
        json.dump(assembly_readiness_packet, f)
    
    # Don't create asset file
    # asset_path = assets_dir / "test_asset.png"
    # asset_path.write_bytes(b"stub image data")
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_assembly_preflight_v3(args)
    
    # Assert failure
    assert result == 1
    
    # Verify preflight
    preflight_path = control_dir / "combine_v2_assembly_preflight_v3.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["assembly_entry_allowed"] == False
    assert preflight["source_asset_exists"] == False


def test_assembly_preflight_success_with_valid_asset(tmp_path):
    """Test that preflight succeeds with valid asset."""
    from app.cli import combine_run_assembly_preflight_v3
    from PIL import Image
    import io
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operator acceptance V3
    operator_acceptance = {
        "source_asset": "output/assets/test_asset.png",
        "operator_visual_acceptance_confirmed": True,
        "visual_asset_accepted": True,
    }
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f)
    
    # Create assembly readiness packet
    assembly_readiness_packet = {
        "source_asset": "output/assets/test_asset.png",
        "visual_asset_accepted": True,
        "operator_visual_acceptance_confirmed": True,
    }
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'w') as f:
        json.dump(assembly_readiness_packet, f)
    
    # Create valid image asset
    img = Image.new('RGB', (100, 100), color='red')
    asset_path = assets_dir / "test_asset.png"
    img.save(asset_path)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_assembly_preflight_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify preflight
    preflight_path = control_dir / "combine_v2_assembly_preflight_v3.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["assembly_entry_allowed"] == True
    assert preflight["source_asset_exists"] == True
    assert preflight["source_asset_readable"] == True
    assert preflight["source_asset_sha256_present"] == True
    assert preflight["source_asset_dimensions_valid"] == True
    assert preflight["next_allowed_action"] == "assembly_plan_required"


def test_assembly_preflight_no_generation(tmp_path):
    """Test that preflight does not perform generation."""
    from app.cli import combine_run_assembly_preflight_v3
    from PIL import Image
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operator acceptance V3
    operator_acceptance = {
        "source_asset": "output/assets/test_asset.png",
        "operator_visual_acceptance_confirmed": True,
        "visual_asset_accepted": True,
    }
    with open(control_dir / "combine_v2_operator_visual_acceptance_v3.json", 'w') as f:
        json.dump(operator_acceptance, f)
    
    # Create assembly readiness packet
    assembly_readiness_packet = {
        "source_asset": "output/assets/test_asset.png",
        "visual_asset_accepted": True,
        "operator_visual_acceptance_confirmed": True,
    }
    with open(control_dir / "combine_v2_assembly_readiness_packet_v3.json", 'w') as f:
        json.dump(assembly_readiness_packet, f)
    
    # Create valid image asset
    img = Image.new('RGB', (100, 100), color='red')
    asset_path = assets_dir / "test_asset.png"
    img.save(asset_path)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_run_assembly_preflight_v3(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation
    preflight_path = control_dir / "combine_v2_assembly_preflight_v3.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["generation_performed"] == False
    assert preflight["retry_attempted"] == False
    assert preflight["visual_qa_rerun"] == False
    assert preflight["assembly_executed"] == False
    assert preflight["downstream_executed"] == False
