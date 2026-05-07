"""Tests for combine corrective retry V4 result validation.

RC-COMBINE-V2-1701-1760 — Test result review with post-submit validation after one controlled retry V4 generation.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_review_corrective_retry_v4_result_success_branch(tmp_path):
    """Test result review with success branch (all validations pass)."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest with assets
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with all checks passing
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify result review artifact
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    assert review_path.exists()
    
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["branch_selected"] == "success"
    assert result_review["generated_assets_count"] == 1
    assert result_review["manifest_success_policy_passed"] == True
    assert result_review["failure_code"] is None
    assert result_review["result_review_executed"] == True
    assert result_review["next_allowed_action"] == "corrective_retry_v4_visual_qa_preflight_required"


def test_combine_review_corrective_retry_v4_result_failed_branch(tmp_path):
    """Test result review with failed branch (stub asset detected)."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest with assets
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with stub asset detected
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": False,
        "asset_size_bytes_gt_1024": False,
        "sha256_present": False,
        "stub_asset_detected": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify result review artifact
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["branch_selected"] == "failed"
    assert result_review["generated_assets_count"] == 1
    assert result_review["manifest_success_policy_passed"] == False
    assert result_review["failure_code"] == "CORRECTIVE_RETRY_V4_OUTPUT_VALIDATION_FAILED"
    assert result_review["result_review_executed"] == True
    assert result_review["next_allowed_action"] == "corrective_retry_v4_result_reconciliation_required"


def test_result_review_missing_generation_result(tmp_path):
    """Test error when generation result is missing."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args without generation result
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert failure
    assert result == 1


def test_stub_asset_guard_enforced_in_review(tmp_path):
    """Test that stub asset guard is enforced in result review."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with stub asset detected
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": False,
        "asset_size_bytes_gt_1024": False,
        "sha256_present": False,
        "stub_asset_detected": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify stub asset guard enforced
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["stub_asset_detected"] == True
    assert result_review["manifest_success_policy_passed"] == False


def test_asset_size_validation_failed(tmp_path):
    """Test that asset size validation failure is detected."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with size check failed
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": False,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify size validation failure detected
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["asset_size_bytes_gt_1024"] == False
    assert result_review["manifest_success_policy_passed"] == False


def test_sha256_validation_failed(tmp_path):
    """Test that SHA256 validation failure is detected."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with SHA256 missing
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": False,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify SHA256 validation failure detected
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["sha256_present"] == False
    assert result_review["manifest_success_policy_passed"] == False


def test_result_review_updates_artifact_index(tmp_path):
    """Test that result review updates artifact index."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation with all checks passing
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifact index updated
    artifact_index_path = control_dir / "artifact_index.json"
    assert artifact_index_path.exists()
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["corrective_retry_v4_result_review_executed"] == True
    assert artifact_index["branch_selected"] == "success"
    assert artifact_index["generated_assets_count"] == 1
    assert artifact_index["manifest_success_policy_passed"] == True


def test_result_review_no_visual_qa(tmp_path):
    """Test that visual QA is not executed during result review."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify visual QA not executed
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["visual_qa_executed"] == False


def test_result_review_no_assembly(tmp_path):
    """Test that assembly is not executed during result review."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify assembly not executed
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["assembly_executed"] == False
    assert result_review["downstream_executed"] == False
    assert result_review["production_accepted"] == False


def test_result_review_production_accepted_false(tmp_path):
    """Test that production_accepted is false in result review."""
    from app.cli import combine_review_corrective_retry_v4_result
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result
    generation_result = {
        "generation_performed": True,
        "retry_attempted": True,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    # Create outputs manifest
    outputs_manifest = {
        "asset_count": 1,
        "generated_assets": ["output/assets/generated_00001_.png"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump(outputs_manifest, f)
    
    # Create post-submit validation
    post_submit_validation = {
        "asset_exists": True,
        "asset_readable": True,
        "asset_size_bytes_gt_1024": True,
        "sha256_present": True,
        "stub_asset_detected": False,
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump(post_submit_validation, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_review_corrective_retry_v4_result(args)
    
    # Assert success
    assert result == 0
    
    # Verify production_accepted is false
    review_path = control_dir / "combine_v2_corrective_retry_v4_result_review.json"
    with open(review_path, 'r') as f:
        result_review = json.load(f)
    
    assert result_review["production_accepted"] == False


# ── RC-COMBINE-V2-2481-2540: V4 result → preflight linkage ──────────────────

def test_v4_result_review_next_action_leads_to_preflight(tmp_path):
    """Successful V4 result review sets next_allowed_action to preflight stage."""
    from app.cli import combine_review_corrective_retry_v4_result

    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)

    with open(control_dir / "combine_v2_corrective_retry_v4_generation_result.json", 'w') as f:
        json.dump({"generation_performed": True, "retry_attempted": True}, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump({"asset_count": 1, "generated_assets": ["output/assets/x.png"]}, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_post_submit_validation.json", 'w') as f:
        json.dump({"asset_exists": True, "asset_readable": True, "asset_size_bytes_gt_1024": True,
                   "sha256_present": True, "stub_asset_detected": False}, f)

    result = combine_review_corrective_retry_v4_result(argparse.Namespace(
        project_root=str(project_root), shot_id="shot02", json=True))
    assert result == 0

    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json") as f:
        review = json.load(f)
    assert review["next_allowed_action"] == "corrective_retry_v4_visual_qa_preflight_required"


def test_v4_preflight_accepts_canonical_asset_from_result_review(tmp_path):
    """V4 preflight succeeds when manifest points at the canonical V4 shot02 asset."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa

    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"Z" * 8192)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump({
            "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
            "asset_count": 1,
        }, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", 'w') as f:
        json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)

    result = combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
        project_root=str(project_root), shot_id="shot02", json=True))
    assert result == 0


def test_v4_preflight_coupling_guard_full_visual_qa_not_triggered(tmp_path):
    """Preflight does not couple into full Visual QA verdict (no verdict artifact created)."""
    from app.cli import combine_preflight_corrective_retry_v4_visual_qa

    project_root = tmp_path / "project"
    control_dir = project_root / "output" / "control"
    assets_dir = project_root / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)

    (assets_dir / "combine_v2_corrective_retry_v4_shot02_00001_.png").write_bytes(b"Z" * 8192)
    with open(control_dir / "combine_v2_corrective_retry_v4_outputs_manifest.json", 'w') as f:
        json.dump({
            "generated_assets": ["output/assets/combine_v2_corrective_retry_v4_shot02_00001_.png"],
            "asset_count": 1,
        }, f)
    with open(control_dir / "combine_v2_corrective_retry_v4_result_review.json", 'w') as f:
        json.dump({"branch_selected": "success", "manifest_success_policy_passed": True}, f)

    combine_preflight_corrective_retry_v4_visual_qa(argparse.Namespace(
        project_root=str(project_root), shot_id="shot02", json=True))

    verdict_path = control_dir / "combine_v2_corrective_retry_v4_visual_qa_verdict.json"
    assert not verdict_path.exists(), "BLOCKER: preflight must not couple into full Visual QA verdict"
