"""
RC-COMBINE-V2-1101-1160 — Tests for Corrective Retry V2 Visual QA Preflight

Tests for visual QA preflight on corrective retry v2 asset:
- Verifies manifest has asset records
- Verifies asset exists on filesystem
- Verifies asset is readable
- Checks manifest vs filesystem consistency
- Blocks entry to visual QA if preflight fails
"""

import json
import pytest
from pathlib import Path
from PIL import Image
from app.cli import combine_run_corrective_retry_v2_visual_qa_preflight
import argparse


@pytest.fixture
def temp_project_root_with_asset(tmp_path: Path):
    """Create a temporary project root with generation result and asset."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with assets
    generation_result = {
        "stage": "corrective_retry_generate_assets_v2",
        "requested_shot_id": "shot02",
        "generated_assets": ["output/assets/asset1.png"],
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_corrective_retry_v2_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create a dummy asset
    img = Image.new('RGB', (1024, 1024), color='white')
    img.save(assets_dir / "asset1.png")
    
    return tmp_path


@pytest.fixture
def temp_project_root_missing_asset(tmp_path: Path):
    """Create a temporary project root with generation result but missing asset."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with assets
    generation_result = {
        "stage": "corrective_retry_generate_assets_v2",
        "requested_shot_id": "shot02",
        "generated_assets": ["output/assets/asset1.png"],
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_corrective_retry_v2_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # No asset created
    return tmp_path


def test_visual_qa_preflight_success(temp_project_root_with_asset: Path):
    """Test visual QA preflight with existing asset (success)."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["visual_qa_entry_allowed"] is True
    assert preflight["filesystem_asset_exists"] is True
    assert preflight["asset_readable"] is True
    assert preflight["manifest_generated_assets_count"] == 1
    assert preflight["collector_manifest_consistent"] is True


def test_visual_qa_preflight_blocks_missing_asset(temp_project_root_missing_asset: Path):
    """Test visual QA preflight blocks entry when asset is missing."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_missing_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_missing_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["visual_qa_entry_allowed"] is False
    assert preflight["filesystem_asset_exists"] is False
    assert preflight["collector_manifest_consistent"] is False


def test_visual_qa_preflight_no_generation_performed(temp_project_root_with_asset: Path):
    """Test that generation is not performed during preflight."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["generation_performed"] is False
    assert preflight["comfyui_execution"] is False
    assert preflight["retry_attempted"] is False


def test_visual_qa_preflight_no_assembly(temp_project_root_with_asset: Path):
    """Test that assembly is not performed during preflight."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["assembly_executed"] is False


def test_visual_qa_preflight_no_downstream(temp_project_root_with_asset: Path):
    """Test that downstream is not performed during preflight."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["downstream_executed"] is False


def test_visual_qa_preflight_no_production_accepted(temp_project_root_with_asset: Path):
    """Test that production_accepted is false during preflight."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["production_accepted"] is False


def test_visual_qa_preflight_artifact_index_updated(temp_project_root_with_asset: Path):
    """Test that artifact index is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["visual_qa_preflight_executed"] is True
    assert artifact_index["visual_qa_entry_allowed"] is True
    assert artifact_index["generation_performed"] is False
    assert artifact_index["assembly_executed"] is False


def test_visual_qa_preflight_episode_ledger_updated(temp_project_root_with_asset: Path):
    """Test that episode ledger is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    
    last_event = ledger[-1]
    assert last_event["event_type"] == "corrective_retry_v2_visual_qa_preflight_completed"
    assert last_event["shot_id"] == "shot02"
    assert last_event["visual_qa_entry_allowed"] is True


def test_visual_qa_preflight_next_action_success(temp_project_root_with_asset: Path):
    """Test that next action is visual_qa when preflight passes."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["next_allowed_action"] == "corrective_retry_v2_visual_qa"


def test_visual_qa_preflight_next_action_blocked(temp_project_root_missing_asset: Path):
    """Test that next action is blocked when preflight fails."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_missing_asset),
        shot_id="shot02",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa_preflight(args)
    assert result == 0
    
    control_dir = temp_project_root_missing_asset / "output" / "control"
    preflight_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_preflight.json"
    with open(preflight_path, 'r') as f:
        preflight = json.load(f)
    
    assert preflight["next_allowed_action"] == "blocked_manual_review"
