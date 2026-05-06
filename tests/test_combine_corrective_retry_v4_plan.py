"""Tests for corrective retry V4 plan creation.

RC-COMBINE-V2-1581-1640
"""

import json
import pytest
from pathlib import Path
import sys
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_v4_plan_creates_failure_classification(tmp_path):
    """Test that V4 plan creates failure classification artifact."""
    from app.cli import combine_create_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    reconciliation_report = {
        "corrupted_v3_asset_path": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png",
        "corrupted_v3_asset_size_bytes": 8,
        "root_cause_analysis": {
            "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        },
        "reconciliation_outcome": {
            "valid_v3_asset_recovered": False,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_corruption_root_cause_report.json", 'w') as f:
        json.dump(reconciliation_report, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_create_corrective_retry_v4_plan(args)

    assert result == 0

    failure_classification_path = control_dir / "combine_v2_corrective_retry_v4_failure_classification.json"
    assert failure_classification_path.exists()

    with open(failure_classification_path, 'r') as f:
        failure_classification = json.load(f)

    assert failure_classification["failure_code"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert failure_classification["corrupted_v3_asset_size_bytes"] == 8
    assert failure_classification["stub_asset_detected"] == True


def test_v4_plan_creates_v4_plan_artifact(tmp_path):
    """Test that V4 plan creates V4 plan artifact with required corrections."""
    from app.cli import combine_create_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    reconciliation_report = {
        "corrupted_v3_asset_path": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png",
        "corrupted_v3_asset_size_bytes": 8,
        "root_cause_analysis": {
            "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        },
        "reconciliation_outcome": {
            "valid_v3_asset_recovered": False,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_corruption_root_cause_report.json", 'w') as f:
        json.dump(reconciliation_report, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_create_corrective_retry_v4_plan(args)

    v4_plan_path = control_dir / "combine_v2_corrective_retry_v4_plan.json"
    assert v4_plan_path.exists()

    with open(v4_plan_path, 'r') as f:
        v4_plan = json.load(f)

    assert v4_plan["corrective_retry_v4_plan_created"] == True
    assert v4_plan["failure_basis"] == "CORRUPTED_V3_ASSET_STUB_GENERATION"
    assert v4_plan["corrupted_v3_asset_size_bytes"] == 8
    assert v4_plan["blind_retry_allowed"] == False
    assert v4_plan["generation_allowed"] == False
    assert v4_plan["retry_allowed"] == False
    assert v4_plan["next_allowed_action"] == "operator_retry_v4_plan_review_required"


def test_v4_plan_required_corrections(tmp_path):
    """Test that V4 plan includes all required corrections."""
    from app.cli import combine_create_corrective_retry_v4_plan

    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    reconciliation_report = {
        "corrupted_v3_asset_path": "output/assets/combine_v2_corrective_retry_v3_generated_1778043247_00001_.png",
        "corrupted_v3_asset_size_bytes": 8,
        "root_cause_analysis": {
            "failure_code": "CORRUPTED_V3_ASSET_STUB_GENERATION",
        },
        "reconciliation_outcome": {
            "valid_v3_asset_recovered": False,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_corruption_root_cause_report.json", 'w') as f:
        json.dump(reconciliation_report, f)

    args = argparse.Namespace(
        project_root=str(tmp_path),
        shot_id="shot02",
        json=True,
    )
    result = combine_create_corrective_retry_v4_plan(args)

    v4_plan_path = control_dir / "combine_v2_corrective_retry_v4_plan.json"
    with open(v4_plan_path, 'r') as f:
        v4_plan = json.load(f)

    required_corrections = v4_plan["required_corrections"]
    assert required_corrections["stub_asset_guard_required"] == True
    assert required_corrections["post_submit_image_readability_validation_required"] == True
    assert required_corrections["manifest_requires_real_readable_image"] == True
    assert required_corrections["visual_qa_requires_readable_image"] == True
    assert required_corrections["assembly_requires_same_accepted_asset"] == True
    assert required_corrections["silent_asset_substitution_forbidden"] == True
    assert required_corrections["result_review_success_requires_asset_size_gt_1024"] == True
    assert required_corrections["sha256_required"] == True
