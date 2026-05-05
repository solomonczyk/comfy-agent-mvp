"""
RC-COMBINE-V2-1101-1160 — Tests for Corrective Retry V2 Visual QA

Tests for structured visual QA on corrective retry v2 asset:
- Reads asset dimensions and validates minimum short side
- Performs technical checks (blur, brightness, contrast)
- Generates honest QA verdict (qa_passed or qa_failed)
- Creates operator review packet
- Blocks production acceptance without operator visual review
"""

import json
import pytest
from pathlib import Path
from PIL import Image
from app.cli import combine_run_corrective_retry_v2_visual_qa
import argparse


@pytest.fixture
def temp_project_root_with_asset(tmp_path: Path):
    """Create a temporary project root with asset."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a dummy asset with good quality (gradient pattern for variance)
    import numpy as np
    arr = np.zeros((1024, 1024, 3), dtype=np.uint8)
    for i in range(1024):
        arr[i, :, :] = i // 4  # Gradient pattern
    img = Image.fromarray(arr)
    img.save(assets_dir / "asset1.png")
    
    return tmp_path


@pytest.fixture
def temp_project_root_with_low_quality_asset(tmp_path: Path):
    """Create a temporary project root with low quality asset."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a dummy asset with low resolution (below minimum short side)
    img = Image.new('RGB', (256, 256), color='white')
    img.save(assets_dir / "asset1.png")
    
    return tmp_path


def test_visual_qa_success(temp_project_root_with_asset: Path):
    """Test visual QA with good quality asset (qa_passed)."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["qa_verdict"] == "qa_passed"
    assert qa_report["asset_exists"] is True
    assert qa_report["asset_readable"] is True
    assert qa_report["minimum_short_side_valid"] is True


def test_visual_qa_fails_low_quality(temp_project_root_with_low_quality_asset: Path):
    """Test visual QA fails with low quality asset (qa_failed)."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_low_quality_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_low_quality_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["qa_verdict"] == "qa_failed"
    assert qa_report["minimum_short_side_valid"] is False


def test_visual_qa_no_generation_performed(temp_project_root_with_asset: Path):
    """Test that generation is not performed during visual QA."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["generation_performed"] is False
    assert qa_report["comfyui_execution"] is False
    assert qa_report["retry_attempted"] is False


def test_visual_qa_no_assembly(temp_project_root_with_asset: Path):
    """Test that assembly is not performed during visual QA."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["assembly_executed"] is False


def test_visual_qa_no_downstream(temp_project_root_with_asset: Path):
    """Test that downstream is not performed during visual QA."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["downstream_executed"] is False


def test_visual_qa_no_production_accepted(temp_project_root_with_asset: Path):
    """Test that production_accepted is false during visual QA."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["production_accepted"] is False


def test_visual_qa_operator_review_required(temp_project_root_with_asset: Path):
    """Test that operator review is required after visual QA."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    qa_report_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_report.json"
    with open(qa_report_path, 'r') as f:
        qa_report = json.load(f)
    
    assert qa_report["operator_review_required"] is True
    assert qa_report["next_allowed_action"] == "operator_visual_review"


def test_visual_qa_creates_operator_review_packet(temp_project_root_with_asset: Path):
    """Test that operator review packet is created."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    review_packet_path = control_dir / "combine_v2_corrective_retry_v2_operator_review_packet.json"
    assert review_packet_path.exists()
    
    with open(review_packet_path, 'r') as f:
        review_packet = json.load(f)
    
    assert review_packet["stage"] == "operator_visual_review"
    assert review_packet["operator_review_required"] is True
    assert review_packet["assembly_allowed"] is False
    assert review_packet["downstream_blocked"] is True


def test_visual_qa_creates_failure_audit_on_failure(temp_project_root_with_low_quality_asset: Path):
    """Test that failure audit is created when QA fails."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_low_quality_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_low_quality_asset / "output" / "control"
    failure_audit_path = control_dir / "combine_v2_corrective_retry_v2_failure_audit.json"
    assert failure_audit_path.exists()
    
    with open(failure_audit_path, 'r') as f:
        failure_audit = json.load(f)
    
    assert failure_audit["qa_verdict"] == "qa_failed"
    assert failure_audit["recommended_action"] == "operator_visual_review"


def test_visual_qa_artifact_index_updated(temp_project_root_with_asset: Path):
    """Test that artifact index is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["visual_qa_executed"] is True
    assert artifact_index["operator_review_required"] is True
    assert artifact_index["generation_performed"] is False
    assert artifact_index["assembly_executed"] is False


def test_visual_qa_episode_ledger_updated(temp_project_root_with_asset: Path):
    """Test that episode ledger is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_asset),
        shot_id="shot02",
        asset="asset1.png",
        json=True
    )
    
    result = combine_run_corrective_retry_v2_visual_qa(args)
    assert result == 0
    
    control_dir = temp_project_root_with_asset / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    
    last_event = ledger[-1]
    assert last_event["event_type"] == "corrective_retry_v2_visual_qa_completed"
    assert last_event["shot_id"] == "shot02"
    assert last_event["operator_review_required"] is True
