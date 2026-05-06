"""Tests for retry V4 stub generation guard.

RC-COMBINE-V2-1581-1640
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_stub_generation_fix_plan_created(tmp_path):
    """Test that stub generation fix plan is created."""
    from app.cli import combine_build_retry_v4_stub_generation_fix_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Create V4 plan and failure classification as prerequisites
    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
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
        json=True,
    )
    result = combine_build_retry_v4_stub_generation_fix_plan(args)

    assert result == 0

    stub_fix_plan_path = control_dir / "combine_v2_retry_v4_stub_generation_fix_plan.json"
    assert stub_fix_plan_path.exists()

    with open(stub_fix_plan_path, 'r') as f:
        stub_fix_plan = json.load(f)

    assert stub_fix_plan["plan_type"] == "retry_v4_stub_generation_fix_plan"
    assert stub_fix_plan["failure_basis"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert stub_fix_plan["fix_strategy"] == "prevent_stub_asset_acceptance"
    assert stub_fix_plan["generation_allowed"] == False
    assert stub_fix_plan["retry_allowed"] == False


def test_output_validation_policy_created(tmp_path):
    """Test that output validation policy is created."""
    from app.cli import combine_build_retry_v4_stub_generation_fix_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
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
        json=True,
    )
    result = combine_build_retry_v4_stub_generation_fix_plan(args)

    validation_policy_path = control_dir / "combine_v2_retry_v4_output_validation_policy.json"
    assert validation_policy_path.exists()

    with open(validation_policy_path, 'r') as f:
        validation_policy = json.load(f)

    assert validation_policy["policy_type"] == "retry_v4_output_validation_policy"
    assert validation_policy["validation_rules"]["asset_size_validation"]["minimum_bytes"] == 1024
    assert validation_policy["validation_rules"]["asset_size_validation"]["reject_below_threshold"] == True
    assert validation_policy["generation_allowed"] == False


def test_no_stub_asset_guard_created(tmp_path):
    """Test that no-stub-asset guard is created."""
    from app.cli import combine_build_retry_v4_stub_generation_fix_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
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
        json=True,
    )
    result = combine_build_retry_v4_stub_generation_fix_plan(args)

    no_stub_guard_path = control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json"
    assert no_stub_guard_path.exists()

    with open(no_stub_guard_path, 'r') as f:
        no_stub_guard = json.load(f)

    assert no_stub_guard["guard_type"] == "retry_v4_no_stub_asset_guard"
    assert no_stub_guard["guard_rules"]["size_threshold"] == 1024
    assert no_stub_guard["guard_rules"]["reject_below_threshold"] == True
    assert no_stub_guard["detection_criteria"]["stub_file_size_bytes"] == 8
    assert no_stub_guard["generation_allowed"] == False


def test_stub_asset_size_8_bytes_detected(tmp_path):
    """Test that 8-byte stub asset is detected."""
    from app.cli import combine_build_retry_v4_stub_generation_fix_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
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
        json=True,
    )
    result = combine_build_retry_v4_stub_generation_fix_plan(args)

    no_stub_guard_path = control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json"
    with open(no_stub_guard_path, 'r') as f:
        no_stub_guard = json.load(f)

    assert no_stub_guard["detection_criteria"]["stub_file_size_bytes"] == 8
