"""Tests for combine retry V3 plan review.

RC-COMBINE-V2-1221-1280 — Test corrective retry V3 plan review.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse


def test_combine_review_corrective_retry_v3_plan_approve(tmp_path):
    """Test approving corrective retry V3 plan."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required v3 plan
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "required_corrections": {
            "prompt_correction_required": True,
            "workflow_correction_required": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_corrective_retry_v3_plan",
        reason="operator_approved_retry_v3_plan_after_blur_and_low_contrast_failure",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert success
    assert result == 0
    
    # Verify approval artifact created
    approval_path = control_dir / "combine_v2_operator_retry_v3_plan_approval.json"
    assert approval_path.exists()
    
    with open(approval_path, 'r') as f:
        approval = json.load(f)
    
    assert approval["operator_decision"] == "approve_corrective_retry_v3_plan"
    assert approval["operator_retry_v3_plan_approved"] == True
    assert approval["corrective_retry_v3_plan_available"] == True
    assert approval["generation_allowed"] == False
    assert approval["retry_allowed"] == False
    assert approval["next_allowed_action"] == "corrective_retry_v3_implementation_package_required"


def test_combine_review_corrective_retry_v3_plan_reject(tmp_path):
    """Test rejecting corrective retry V3 plan."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required v3 plan
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="reject_corrective_retry_v3_plan",
        reason="plan_insufficient",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert success
    assert result == 0
    
    # Verify approval artifact created
    approval_path = control_dir / "combine_v2_operator_retry_v3_plan_approval.json"
    assert approval_path.exists()
    
    with open(approval_path, 'r') as f:
        approval = json.load(f)
    
    assert approval["operator_decision"] == "reject_corrective_retry_v3_plan"
    assert approval["operator_retry_v3_plan_approved"] == False
    assert approval["next_allowed_action"] == "operator_retry_v3_plan_review_required"


def test_combine_review_corrective_retry_v3_plan_missing_plan(tmp_path):
    """Test error when v3 plan is missing."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure without v3 plan
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_corrective_retry_v3_plan",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert failure
    assert result == 1


def test_combine_review_corrective_retry_v3_plan_invalid_decision(tmp_path):
    """Test error with invalid decision."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required v3 plan
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    # Create args with invalid decision
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="invalid_decision",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert failure
    assert result == 1


def test_operator_retry_v3_plan_review_recorded(tmp_path):
    """Test that operator retry v3 plan review is recorded in artifact index."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required v3 plan
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_corrective_retry_v3_plan",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifact index updated
    artifact_index_path = control_dir / "artifact_index.json"
    assert artifact_index_path.exists()
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["operator_retry_v3_plan_approved"] == True
    assert artifact_index["operator_retry_v3_plan_decision"] == "approve_corrective_retry_v3_plan"
    assert artifact_index["generation_allowed"] == False
    assert artifact_index["retry_allowed"] == False


def test_operator_can_approve_corrective_retry_v3_plan(tmp_path):
    """Test that operator can approve corrective retry v3 plan."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required v3 plan
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_corrective_retry_v3_plan",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert success
    assert result == 0
    
    # Verify approval
    approval_path = control_dir / "combine_v2_operator_retry_v3_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)
    
    assert approval["operator_retry_v3_plan_approved"] == True
    assert approval["next_allowed_action"] == "corrective_retry_v3_implementation_package_required"


def test_corrective_retry_v3_plan_required(tmp_path):
    """Test that corrective retry v3 plan is required before review."""
    from app.cli import combine_review_corrective_retry_v3_plan
    
    # Setup project structure without v3 plan
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_corrective_retry_v3_plan",
        reason="test",
        json=True,
    )
    
    # Run command should fail
    result = combine_review_corrective_retry_v3_plan(args)
    
    # Assert failure
    assert result == 1
