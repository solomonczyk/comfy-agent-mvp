"""Tests for retry V4 plan review packet.

RC-COMBINE-V2-1581-1640
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_operator_plan_review_packet_created(tmp_path):
    """Test that operator plan review packet is created."""
    from app.cli import combine_build_retry_v4_plan_review_packet

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    # Create prerequisite artifacts
    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "retry_v4_requires_operator_plan_review": True,
        "blind_retry_allowed": False,
        "required_corrections": {
            "stub_asset_guard_required": True,
            "post_submit_image_readability_validation_required": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    stub_fix_plan = {
        "fix_strategy": "prevent_stub_asset_acceptance",
        "fix_components": {
            "stub_asset_guard": {
                "threshold_bytes": 1024,
            },
        },
    }
    with open(control_dir / "combine_v2_retry_v4_stub_generation_fix_plan.json", 'w') as f:
        json.dump(stub_fix_plan, f)

    validation_policy = {
        "validation_rules": {
            "asset_size_validation": {
                "minimum_bytes": 1024,
            },
            "image_readability_validation": {
                "enabled": True,
            },
        },
    }
    with open(control_dir / "combine_v2_retry_v4_output_validation_policy.json", 'w') as f:
        json.dump(validation_policy, f)

    no_stub_guard = {
        "guard_rules": {
            "size_threshold": 1024,
            "reject_below_threshold": True,
        },
    }
    with open(control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json", 'w') as f:
        json.dump(no_stub_guard, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_build_retry_v4_plan_review_packet(args)

    assert result == 0

    review_packet_path = control_dir / "combine_v2_retry_v4_operator_plan_review_packet.json"
    assert review_packet_path.exists()

    with open(review_packet_path, 'r') as f:
        review_packet = json.load(f)

    assert review_packet["packet_type"] == "retry_v4_operator_plan_review_packet"
    assert review_packet["failure_summary"]["failure_code"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert review_packet["failure_summary"]["corrupted_v3_asset_size_bytes"] == 8
    assert review_packet["v4_plan_summary"]["blind_retry_allowed"] == False
    assert review_packet["v4_plan_summary"]["retry_v4_requires_operator_plan_review"] == True


def test_blind_retry_blocked(tmp_path):
    """Test that blind retry is blocked in review packet."""
    from app.cli import combine_build_retry_v4_plan_review_packet

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "failure_basis": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "retry_v4_requires_operator_plan_review": True,
        "blind_retry_allowed": False,
        "required_corrections": {},
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    stub_fix_plan = {"fix_strategy": "prevent_stub_asset_acceptance", "fix_components": {}}
    with open(control_dir / "combine_v2_retry_v4_stub_generation_fix_plan.json", 'w') as f:
        json.dump(stub_fix_plan, f)

    validation_policy = {"validation_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_output_validation_policy.json", 'w') as f:
        json.dump(validation_policy, f)

    no_stub_guard = {"guard_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json", 'w') as f:
        json.dump(no_stub_guard, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_build_retry_v4_plan_review_packet(args)

    review_packet_path = control_dir / "combine_v2_retry_v4_operator_plan_review_packet.json"
    with open(review_packet_path, 'r') as f:
        review_packet = json.load(f)

    assert review_packet["v4_plan_summary"]["blind_retry_allowed"] == False


def test_hard_boundary_enforced(tmp_path):
    """Test that hard boundary is enforced in review packet."""
    from app.cli import combine_build_retry_v4_plan_review_packet

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "retry_v4_requires_operator_plan_review": True,
        "blind_retry_allowed": False,
        "required_corrections": {},
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    stub_fix_plan = {"fix_strategy": "prevent_stub_asset_acceptance", "fix_components": {}}
    with open(control_dir / "combine_v2_retry_v4_stub_generation_fix_plan.json", 'w') as f:
        json.dump(stub_fix_plan, f)

    validation_policy = {"validation_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_output_validation_policy.json", 'w') as f:
        json.dump(validation_policy, f)

    no_stub_guard = {"guard_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json", 'w') as f:
        json.dump(no_stub_guard, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_build_retry_v4_plan_review_packet(args)

    review_packet_path = control_dir / "combine_v2_retry_v4_operator_plan_review_packet.json"
    with open(review_packet_path, 'r') as f:
        review_packet = json.load(f)

    hard_boundary = review_packet["hard_boundary"]
    assert hard_boundary["new_generation"] == False
    assert hard_boundary["new_comfyui_submit"] == False
    assert hard_boundary["retry_submit"] == False
    assert hard_boundary["visual_qa"] == False
    assert hard_boundary["operator_visual_decision"] == False
    assert hard_boundary["assembly"] == False
    assert hard_boundary["audio"] == False
    assert hard_boundary["render"] == False
    assert hard_boundary["downstream"] == False
    assert hard_boundary["production_accepted"] == False


def test_generation_allowed_false(tmp_path):
    """Test that generation_allowed is false."""
    from app.cli import combine_build_retry_v4_plan_review_packet

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    v4_plan = {
        "corrective_retry_v4_plan_created": True,
        "retry_v4_requires_operator_plan_review": True,
        "blind_retry_allowed": False,
        "required_corrections": {},
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_plan.json", 'w') as f:
        json.dump(v4_plan, f)

    failure_classification = {
        "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        "corrupted_v3_asset_size_bytes": 8,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_failure_classification.json", 'w') as f:
        json.dump(failure_classification, f)

    stub_fix_plan = {"fix_strategy": "prevent_stub_asset_acceptance", "fix_components": {}}
    with open(control_dir / "combine_v2_retry_v4_stub_generation_fix_plan.json", 'w') as f:
        json.dump(stub_fix_plan, f)

    validation_policy = {"validation_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_output_validation_policy.json", 'w') as f:
        json.dump(validation_policy, f)

    no_stub_guard = {"guard_rules": {}}
    with open(control_dir / "combine_v2_retry_v4_no_stub_asset_guard.json", 'w') as f:
        json.dump(no_stub_guard, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_build_retry_v4_plan_review_packet(args)

    review_packet_path = control_dir / "combine_v2_retry_v4_operator_plan_review_packet.json"
    with open(review_packet_path, 'r') as f:
        review_packet = json.load(f)

    assert review_packet["generation_allowed"] == False
    assert review_packet["retry_allowed"] == False
    assert review_packet["workflow_submitted"] == False
    assert review_packet["comfyui_execution"] == False
    assert review_packet["visual_qa_executed"] == False
    assert review_packet["assembly_executed"] == False
    assert review_packet["downstream_executed"] == False
    assert review_packet["production_accepted"] == False
