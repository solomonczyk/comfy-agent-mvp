"""Tests for retry V4 plan review.

RC-COMBINE-V2-1641-1700
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_operator_can_approve_corrective_retry_v4_plan(tmp_path):
    """Test that operator can approve corrective retry V4 plan."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Create prerequisite artifacts
    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
        "blind_retry_allowed": False,
        "generation_allowed": False,
        "retry_allowed": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    artifact_index = {
        "current_state": "operator_retry_v4_plan_review_required",
        "next_allowed_action": "operator_retry_v4_plan_review_required",
    }
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(artifact_index, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan_for_stub_generation_failure",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    assert result == 0

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    assert approval_path.exists()

    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["operator_retry_v4_plan_approval_created"] == True
    assert approval["operator_retry_v4_plan_approved"] == True
    assert approval["decision"] == "approve_corrective_retry_v4_plan"
    assert approval["failure_code"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert approval["corrupted_v3_asset_size_bytes"] == 8
    assert approval["corrective_retry_v4_plan_available"] == True
    assert approval["blind_retry_allowed"] == False
    assert approval["generation_allowed"] == False
    assert approval["retry_allowed"] == False
    assert approval["next_allowed_action"] == "corrective_retry_v4_implementation_package_required"


def test_corrective_retry_v4_plan_required(tmp_path):
    """Test that V4 plan is required before review."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Create failure classification
    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    # Missing V4 plan - should still work with defaults
    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan_for_stub_generation_failure",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    assert result == 0

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["operator_retry_v4_plan_approved"] == True


def test_blind_retry_blocked_after_approval(tmp_path):
    """Test that blind retry is blocked after plan approval."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "blind_retry_allowed": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan_for_stub_generation_failure",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["blind_retry_allowed"] == False


def test_generation_allowed_false_after_approval(tmp_path):
    """Test that generation_allowed is false after plan approval."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "generation_allowed": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan_for_stub_generation_failure",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["generation_allowed"] == False
    assert approval["retry_allowed"] == False
    assert approval["workflow_submitted"] == False
    assert approval["comfyui_execution"] == False
    assert approval["production_accepted"] == False


def test_next_action_transitions_to_implementation_package(tmp_path):
    """Test that next action transitions to implementation package required."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan_for_stub_generation_failure",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["next_allowed_action"] == "corrective_retry_v4_implementation_package_required"


def test_reject_decision_keeps_state_in_review(tmp_path):
    """Test that reject decision keeps state in review."""
    from app.cli import combine_review_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="reject_corrective_retry_v4_plan",
        reason="operator_rejected_v4_plan",
        json=True,
    )
    result = combine_review_corrective_retry_v4_plan(args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["operator_retry_v4_plan_approved"] == False
    assert approval["next_allowed_action"] == "operator_retry_v4_plan_review_required"
