"""
RC-COMBINE-V2-1101-1160 — Tests for Collector Reliability Guard

Tests for collector reliability guard validation:
- Prohibits manifest being success/empty when assets exist on disk
- Requires failed collection to trigger filesystem scan
- Requires success branch to have manifest asset records
- Enforces manifest asset record requirements (path, exists, readable, width, height, size_bytes, sha256)
- Allows manual reconciliation only as recovery
- Requires future collectors to auto-reconcile
"""

import json
import pytest
from pathlib import Path
from app.cli import combine_validate_collector_reliability_guard
import argparse


@pytest.fixture
def temp_project_root_with_manifest_and_assets(tmp_path: Path):
    """Create a temporary project root with manifest and assets."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create manifest with asset records
    manifest = {
        "status": "success",
        "generated_assets": [
            {
                "path": "output/assets/asset1.png",
                "exists": True,
                "readable": True,
                "width": 1024,
                "height": 1024,
                "size_bytes": 1000,
                "sha256": "abc123"
            }
        ]
    }
    with open(control_dir / "combine_v2_generation_manifest.json", 'w') as f:
        json.dump(manifest, f)
    
    # Create dummy asset
    from PIL import Image
    img = Image.new('RGB', (1024, 1024), color='white')
    img.save(assets_dir / "asset1.png")
    
    return tmp_path


@pytest.fixture
def temp_project_root_empty_manifest_with_assets(tmp_path: Path):
    """Create a temporary project root with empty manifest but assets exist (forbidden)."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty manifest (forbidden when assets exist)
    manifest = {
        "status": "success",
        "generated_assets": []
    }
    with open(control_dir / "combine_v2_generation_manifest.json", 'w') as f:
        json.dump(manifest, f)
    
    # Create dummy asset
    from PIL import Image
    img = Image.new('RGB', (1024, 1024), color='white')
    img.save(assets_dir / "asset1.png")
    
    return tmp_path


@pytest.fixture
def temp_project_root_failed_manifest_no_assets(tmp_path: Path):
    """Create a temporary project root with failed manifest and no assets."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create failed manifest
    manifest = {
        "status": "failed",
        "generated_assets": []
    }
    with open(control_dir / "combine_v2_generation_manifest.json", 'w') as f:
        json.dump(manifest, f)
    
    # No assets created
    
    return tmp_path


def test_collector_guard_success(temp_project_root_with_manifest_and_assets: Path):
    """Test collector guard validation with valid manifest and assets."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["collector_reliability_guard_created"] is True
    assert guard["manifest_empty_while_filesystem_assets_exist_is_forbidden"] is True
    assert guard["success_branch_requires_manifest_asset_records"] is True


def test_collector_guard_blocks_empty_manifest(temp_project_root_empty_manifest_with_assets: Path):
    """Test collector guard blocks empty manifest with existing assets."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_empty_manifest_with_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_empty_manifest_with_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["manifest_empty_while_filesystem_assets_exist_is_forbidden"] is False
    assert guard["filesystem_assets_count"] == 1
    assert guard["manifest_assets_count"] == 0


def test_collector_guard_requires_filesystem_scan_on_failure(temp_project_root_failed_manifest_no_assets: Path):
    """Test collector guard requires filesystem scan on failed collection."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_failed_manifest_no_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_failed_manifest_no_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["failed_collection_requires_filesystem_scan"] is True


def test_collector_guard_manifest_asset_records_required(temp_project_root_with_manifest_and_assets: Path):
    """Test that manifest asset records have required fields."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["manifest_asset_records_require"] == [
        "path",
        "exists",
        "readable",
        "width",
        "height",
        "size_bytes",
        "sha256"
    ]
    assert guard["manifest_asset_records_valid"] is True


def test_collector_guard_manual_reconciliation_only_as_recovery(temp_project_root_with_manifest_and_assets: Path):
    """Test that manual reconciliation is allowed only as recovery."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["manual_reconciliation_allowed_only_as_recovery"] is True


def test_collector_guard_future_collectors_auto_reconcile(temp_project_root_with_manifest_and_assets: Path):
    """Test that future collectors must auto-reconcile."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    guard_path = control_dir / "combine_v2_collector_reliability_guard.json"
    with open(guard_path, 'r') as f:
        guard = json.load(f)
    
    assert guard["future_collectors_must_auto_reconcile"] is True


def test_collector_guard_validation_created(temp_project_root_with_manifest_and_assets: Path):
    """Test that validation result is created."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    validation_path = control_dir / "combine_v2_collector_reliability_validation.json"
    assert validation_path.exists()
    
    with open(validation_path, 'r') as f:
        validation = json.load(f)
    
    assert validation["guard_created"] is True
    assert validation["validation_passed"] is True


def test_collector_guard_artifact_index_updated(temp_project_root_with_manifest_and_assets: Path):
    """Test that artifact index is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["collector_reliability_guard_created"] is True
    assert artifact_index["collector_reliability_guard_validation_passed"] is True


def test_collector_guard_episode_ledger_updated(temp_project_root_with_manifest_and_assets: Path):
    """Test that episode ledger is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_manifest_and_assets),
        json=True
    )
    
    result = combine_validate_collector_reliability_guard(args)
    assert result == 0
    
    control_dir = temp_project_root_with_manifest_and_assets / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    
    last_event = ledger[-1]
    assert last_event["event_type"] == "collector_reliability_guard_validated"
    assert last_event["guard_created"] is True
