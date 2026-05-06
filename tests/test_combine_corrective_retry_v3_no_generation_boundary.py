"""Tests for combine corrective retry V3 no generation boundary.

RC-COMBINE-V2-1221-1280 — Test that corrective retry V3 implementation package
does NOT trigger generation, retry, visual QA rerun, assembly, or downstream.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse


def test_no_generation_boundary_in_implementation_package(tmp_path):
    """Test that implementation package has generation_allowed=False."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    approval = {
        "operator_retry_v3_plan_approved": True,
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_operator_retry_v3_plan_approval.json", 'w') as f:
        json.dump(approval, f)
    
    v3_plan = {"source_asset": "output/assets/test.png", "failure_basis": ["blur_detected", "low_contrast"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    for plan_name in ["sampler_recipe", "prompt", "workflow_quality"]:
        plan = {"recommended_changes": {}, f"{plan_name.split('_')[0]}_elements_to_review": []}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{plan_name}_plan.json", 'w') as f:
            json.dump(plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation boundary
    package_path = control_dir / "combine_v2_corrective_retry_v3_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)
    
    assert package["generation_allowed"] == False
    assert package["retry_allowed"] == False
    assert package["workflow_submitted"] == False
    assert package["comfyui_execution"] == False
    assert package["downstream_executed"] == False
    assert package["production_accepted"] == False


def test_no_generation_boundary_in_validation(tmp_path):
    """Test that validation has generation_allowed=False."""
    from app.cli import combine_validate_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "patches": {
            "sampler_recipe_patch_created": True,
            "prompt_quality_patch_created": True,
            "workflow_quality_patch_created": True,
            "contrast_blur_correction_patch_created": True,
            "conditioning_chain_review_patch_created": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create all patches
    for patch_name in ["sampler_recipe", "prompt_quality", "workflow_quality", "contrast_blur", "conditioning_chain"]:
        patch = {"patch_type": f"corrective_retry_v3_{patch_name}_patch", "patch_created": True}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{patch_name}_patch.json", 'w') as f:
            json.dump(patch, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_validate_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation boundary
    validation_path = control_dir / "combine_v2_corrective_retry_v3_pre_submit_validation.json"
    with open(validation_path, 'r') as f:
        validation = json.load(f)
    
    assert validation["generation_allowed"] == False
    assert validation["retry_allowed"] == False


def test_no_generation_boundary_in_auth_request(tmp_path):
    """Test that authorization request has generation_allowed=False."""
    from app.cli import combine_validate_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "patches": {
            "sampler_recipe_patch_created": True,
            "prompt_quality_patch_created": True,
            "workflow_quality_patch_created": True,
            "contrast_blur_correction_patch_created": True,
            "conditioning_chain_review_patch_created": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create all patches
    for patch_name in ["sampler_recipe", "prompt_quality", "workflow_quality", "contrast_blur", "conditioning_chain"]:
        patch = {"patch_type": f"corrective_retry_v3_{patch_name}_patch", "patch_created": True}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{patch_name}_patch.json", 'w') as f:
            json.dump(patch, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_validate_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify no generation boundary in auth request
    auth_request_path = control_dir / "combine_v2_operator_retry_v3_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["generation_allowed"] == False
    assert auth_request["retry_allowed"] == False
    assert auth_request["workflow_submitted"] == False
    assert auth_request["comfyui_execution"] == False
    assert auth_request["downstream_executed"] == False
    assert auth_request["production_accepted"] == False


def test_no_generation_boundary_in_all_patches(tmp_path):
    """Test that all patches have generation_allowed=False."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    approval = {
        "operator_retry_v3_plan_approved": True,
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_operator_retry_v3_plan_approval.json", 'w') as f:
        json.dump(approval, f)
    
    v3_plan = {"source_asset": "output/assets/test.png", "failure_basis": ["blur_detected", "low_contrast"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    for plan_name in ["sampler_recipe", "prompt", "workflow_quality"]:
        plan = {"recommended_changes": {}, f"{plan_name.split('_')[0]}_elements_to_review": []}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{plan_name}_plan.json", 'w') as f:
            json.dump(plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify all patches have generation_allowed=False
    patch_files = [
        "combine_v2_corrective_retry_v3_sampler_recipe_patch.json",
        "combine_v2_corrective_retry_v3_prompt_quality_patch.json",
        "combine_v2_corrective_retry_v3_workflow_quality_patch.json",
        "combine_v2_corrective_retry_v3_contrast_blur_patch.json",
        "combine_v2_corrective_retry_v3_conditioning_chain_patch.json",
    ]
    
    for patch_file in patch_files:
        patch_path = control_dir / patch_file
        with open(patch_path, 'r') as f:
            patch = json.load(f)
        assert patch["generation_allowed"] == False


def test_no_generation_boundary_in_artifact_index(tmp_path):
    """Test that artifact index has generation_allowed=False."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    approval = {
        "operator_retry_v3_plan_approved": True,
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_operator_retry_v3_plan_approval.json", 'w') as f:
        json.dump(approval, f)
    
    v3_plan = {"source_asset": "output/assets/test.png", "failure_basis": ["blur_detected", "low_contrast"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    for plan_name in ["sampler_recipe", "prompt", "workflow_quality"]:
        plan = {"recommended_changes": {}, f"{plan_name.split('_')[0]}_elements_to_review": []}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{plan_name}_plan.json", 'w') as f:
            json.dump(plan, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify artifact index has no generation
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["generation_allowed"] == False
    assert artifact_index["retry_allowed"] == False
    assert artifact_index["workflow_submitted"] == False
    assert artifact_index["comfyui_execution"] == False
    assert artifact_index["downstream_executed"] == False
    assert artifact_index["production_accepted"] == False


def test_no_generation_boundary_stops_at_auth_required(tmp_path):
    """Test that process stops at operator_retry_v3_generation_authorization_required."""
    from app.cli import combine_validate_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "patches": {
            "sampler_recipe_patch_created": True,
            "prompt_quality_patch_created": True,
            "workflow_quality_patch_created": True,
            "contrast_blur_correction_patch_created": True,
            "conditioning_chain_review_patch_created": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create all patches
    for patch_name in ["sampler_recipe", "prompt_quality", "workflow_quality", "contrast_blur", "conditioning_chain"]:
        patch = {"patch_type": f"corrective_retry_v3_{patch_name}_patch", "patch_created": True}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{patch_name}_patch.json", 'w') as f:
            json.dump(patch, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_validate_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify stops at auth required
    auth_request_path = control_dir / "combine_v2_operator_retry_v3_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["stage"] == "operator_retry_v3_generation_authorization_required"
    assert auth_request["next_allowed_action"] == "operator_retry_v3_generation_authorization_required"
    assert auth_request["operator_review_required"] == True


def test_no_generation_boundary_max_one_generation(tmp_path):
    """Test that max_generations_allowed is set to 1."""
    from app.cli import combine_validate_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "patches": {
            "sampler_recipe_patch_created": True,
            "prompt_quality_patch_created": True,
            "workflow_quality_patch_created": True,
            "contrast_blur_correction_patch_created": True,
            "conditioning_chain_review_patch_created": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create all patches
    for patch_name in ["sampler_recipe", "prompt_quality", "workflow_quality", "contrast_blur", "conditioning_chain"]:
        patch = {"patch_type": f"corrective_retry_v3_{patch_name}_patch", "patch_created": True}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{patch_name}_patch.json", 'w') as f:
            json.dump(patch, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_validate_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify max_generations_allowed is 1
    auth_request_path = control_dir / "combine_v2_operator_retry_v3_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["max_generations_allowed"] == 1


def test_no_generation_boundary_blind_retry_not_allowed(tmp_path):
    """Test that blind_retry_allowed is False."""
    from app.cli import combine_validate_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create implementation package
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
        "patches": {
            "sampler_recipe_patch_created": True,
            "prompt_quality_patch_created": True,
            "workflow_quality_patch_created": True,
            "contrast_blur_correction_patch_created": True,
            "conditioning_chain_review_patch_created": True,
        },
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create all patches
    for patch_name in ["sampler_recipe", "prompt_quality", "workflow_quality", "contrast_blur", "conditioning_chain"]:
        patch = {"patch_type": f"corrective_retry_v3_{patch_name}_patch", "patch_created": True}
        with open(control_dir / f"combine_v2_corrective_retry_v3_{patch_name}_patch.json", 'w') as f:
            json.dump(patch, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_validate_corrective_retry_v3_implementation_package(args)
    
    # Assert success
    assert result == 0
    
    # Verify blind_retry_allowed is False
    auth_request_path = control_dir / "combine_v2_operator_retry_v3_generation_authorization_request.json"
    with open(auth_request_path, 'r') as f:
        auth_request = json.load(f)
    
    assert auth_request["blind_retry_allowed"] == False
