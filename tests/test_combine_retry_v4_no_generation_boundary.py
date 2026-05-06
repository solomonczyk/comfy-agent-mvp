"""Tests for retry V4 no-generation boundary.

RC-COMBINE-V2-1641-1700
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_blind_retry_blocked(tmp_path):
    """Test that blind retry is blocked in V4."""
    from app.cli import combine_review_corrective_retry_v4_plan
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "blind_retry_allowed": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    review_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan",
        json=True,
    )
    combine_review_corrective_retry_v4_plan(review_args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["blind_retry_allowed"] == False


def test_generation_allowed_false(tmp_path):
    """Test that generation_allowed is false throughout V4 flow."""
    from app.cli import combine_review_corrective_retry_v4_plan
    from app.cli import combine_build_corrective_retry_v4_implementation_package

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

    review_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan",
        json=True,
    )
    combine_review_corrective_retry_v4_plan(review_args)

    approval_path = control_dir / "combine_v2_operator_retry_v4_plan_approval.json"
    with open(approval_path, 'r') as f:
        approval = json.load(f)

    assert approval["generation_allowed"] == False

    # Build implementation package
    build_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(build_args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["generation_allowed"] == False


def test_retry_allowed_false(tmp_path):
    """Test that retry_allowed is false throughout V4 flow."""
    from app.cli import combine_review_corrective_retry_v4_plan
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "retry_allowed": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    review_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        decision="approve_corrective_retry_v4_plan",
        reason="operator_approved_v4_plan",
        json=True,
    )
    combine_review_corrective_retry_v4_plan(review_args)

    build_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(build_args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["retry_allowed"] == False


def test_workflow_submitted_false(tmp_path):
    """Test that workflow_submitted is false."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["workflow_submitted"] == False


def test_comfyui_execution_false(tmp_path):
    """Test that comfyui_execution is false."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["comfyui_execution"] == False


def test_visual_qa_not_executed(tmp_path):
    """Test that visual QA is not executed."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    auth_request_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)

    assert auth_request["generation_allowed"] == False
    assert auth_request["retry_allowed"] == False
    assert auth_request["workflow_submitted"] == False
    assert auth_request["comfyui_execution"] == False


def test_assembly_not_executed(tmp_path):
    """Test that assembly is not executed."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["production_accepted"] == False


def test_downstream_not_executed(tmp_path):
    """Test that downstream is not executed."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    auth_request_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)

    assert auth_request["production_accepted"] == False


def test_production_accepted_false(tmp_path):
    """Test that production_accepted is false."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["production_accepted"] == False


def test_hard_boundary_enforced(tmp_path):
    """Test that hard boundary is enforced across all artifacts."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    plan_approval = {"operator_retry_v4_plan_approved": True}
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

    v4_plan = {"corrective_retry_v4_plan_created": True}
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {"failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION"}
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(args)

    # Check all artifacts enforce hard boundary
    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["generation_allowed"] == False
    assert package["retry_allowed"] == False
    assert package["workflow_submitted"] == False
    assert package["comfyui_execution"] == False
    assert package["production_accepted"] == False

    auth_request_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)

    assert auth_request["generation_allowed"] == False
    assert auth_request["retry_allowed"] == False
    assert auth_request["workflow_submitted"] == False
    assert auth_request["comfyui_execution"] == False
    assert auth_request["production_accepted"] == False
