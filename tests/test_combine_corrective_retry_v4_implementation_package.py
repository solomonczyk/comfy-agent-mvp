"""Tests for corrective retry V4 implementation package.

RC-COMBINE-V2-1641-1700
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_implementation_package_created(tmp_path):
    """Test that implementation package is created."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Create prerequisite artifacts
    plan_approval = {
        "operator_retry_v4_plan_approved": True,
        "decision": "approve_corrective_retry_v4_plan",
    }
    with open(control_dir / "combine_v2_operator_retry_v4_plan_approval.json", 'w') as f:
        json.dump(plan_approval, f)

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

    artifact_index = {
        "current_state": "corrective_retry_v4_implementation_package_required",
    }
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(artifact_index, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_build_corrective_retry_v4_implementation_package(args)

    assert result == 0

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    assert package_path.exists()

    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["corrective_retry_v4_implementation_package_created"] == True
    assert package["package_type"] == "corrective_retry_v4_implementation_package"
    assert package["failure_basis"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert package["operator_retry_v4_plan_approved"] == True


def test_stub_asset_guard_enabled(tmp_path):
    """Test that stub asset guard is enabled."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    guards = package["guards"]
    assert guards["stub_asset_guard_enabled"] == True
    assert guards["min_asset_size_bytes"] == 1024


def test_post_submit_validation_contract_created(tmp_path):
    """Test that post-submit validation contract is created."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    post_submit_path = control_dir / "combine_v2_retry_v4_post_submit_validation_contract.json"
    assert post_submit_path.exists()

    with open(post_submit_path, 'r') as f:
        contract = json.load(f)

    assert contract["contract_type"] == "retry_v4_post_submit_validation_contract"
    assert contract["validation_rules"]["image_readability_validation"]["enabled"] == True


def test_manifest_success_policy_requires_readable_image(tmp_path):
    """Test that manifest success policy requires readable image."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    manifest_path = control_dir / "combine_v2_retry_v4_manifest_success_policy.json"
    assert manifest_path.exists()

    with open(manifest_path, 'r') as f:
        policy = json.load(f)

    assert policy["policy_type"] == "retry_v4_manifest_success_policy"
    assert policy["success_criteria"]["requires_real_readable_image"] == True
    assert policy["success_criteria"]["requires_valid_sha256"] == True
    assert policy["success_criteria"]["requires_asset_size_gt_1024"] == True


def test_visual_qa_input_guard_created(tmp_path):
    """Test that visual QA input guard is created."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    visual_qa_path = control_dir / "combine_v2_retry_v4_visual_qa_input_guard.json"
    assert visual_qa_path.exists()

    with open(visual_qa_path, 'r') as f:
        guard = json.load(f)

    assert guard["guard_type"] == "retry_v4_visual_qa_input_guard"
    assert guard["guard_rules"]["requires_readable_image"] == True
    assert guard["guard_rules"]["reject_corrupted_asset"] == True
    assert guard["guard_rules"]["reject_stub_asset"] == True


def test_assembly_asset_guard_created(tmp_path):
    """Test that assembly asset guard is created."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    assembly_path = control_dir / "combine_v2_retry_v4_assembly_asset_guard.json"
    assert assembly_path.exists()

    with open(assembly_path, 'r') as f:
        guard = json.load(f)

    assert guard["guard_type"] == "retry_v4_assembly_asset_guard"
    assert guard["guard_rules"]["requires_same_accepted_asset"] == True
    assert guard["guard_rules"]["silent_asset_substitution_forbidden"] == True


def test_operator_retry_v4_generation_authorization_request_created(tmp_path):
    """Test that operator generation authorization request is created."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    auth_request_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json"
    assert auth_request_path.exists()

    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)

    assert auth_request["operator_retry_v4_generation_authorization_request_created"] == True
    assert auth_request["request_type"] == "operator_retry_v4_generation_authorization"
    assert auth_request["implementation_package_created"] == True
    assert auth_request["generation_allowed"] == False
    assert auth_request["retry_allowed"] == False
    assert auth_request["next_allowed_action"] == "operator_retry_v4_generation_authorization_required"


def test_generation_allowed_false(tmp_path):
    """Test that generation_allowed is false in implementation package."""
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
    result = combine_build_corrective_retry_v4_implementation_package(args)

    package_path = control_dir / "combine_v2_corrective_retry_v4_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)

    assert package["generation_allowed"] == False
    assert package["retry_allowed"] == False
    assert package["workflow_submitted"] == False
    assert package["comfyui_execution"] == False
    assert package["production_accepted"] == False


def test_validation_passes_with_complete_package(tmp_path):
    """Test that validation passes with complete package."""
    from app.cli import combine_build_corrective_retry_v4_implementation_package
    from app.cli import combine_validate_corrective_retry_v4_implementation_package

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

    build_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    combine_build_corrective_retry_v4_implementation_package(build_args)

    validate_args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_validate_corrective_retry_v4_implementation_package(validate_args)

    assert result == 0
