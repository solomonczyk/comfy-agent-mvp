"""Tests for combine corrective retry V3 implementation package.

RC-COMBINE-V2-1221-1280 — Test corrective retry V3 implementation package.
"""

import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import argparse


def test_combine_build_corrective_retry_v3_implementation_package(tmp_path):
    """Test building corrective retry V3 implementation package."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create operator plan approval
    approval = {
        "operator_retry_v3_plan_approved": True,
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_operator_retry_v3_plan_approval.json", 'w') as f:
        json.dump(approval, f)
    
    # Create v3 plan and sub-plans
    v3_plan = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v3_plan.json", 'w') as f:
        json.dump(v3_plan, f)
    
    sampler_plan = {"recommended_changes": {}, "sampler_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_plan.json", 'w') as f:
        json.dump(sampler_plan, f)
    
    prompt_plan = {"recommended_changes": {}, "prompt_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_prompt_plan.json", 'w') as f:
        json.dump(prompt_plan, f)
    
    workflow_plan = {"recommended_changes": {}, "workflow_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_workflow_quality_plan.json", 'w') as f:
        json.dump(workflow_plan, f)
    
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
    
    # Verify all patch files created
    assert (control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_patch.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v3_prompt_quality_patch.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v3_workflow_quality_patch.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v3_contrast_blur_patch.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v3_conditioning_chain_patch.json").exists()
    assert (control_dir / "combine_v2_corrective_retry_v3_implementation_package.json").exists()


def test_implementation_package_created(tmp_path):
    """Test that implementation package manifest is created correctly."""
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
    
    # Verify package manifest
    package_path = control_dir / "combine_v2_corrective_retry_v3_implementation_package.json"
    with open(package_path, 'r') as f:
        package = json.load(f)
    
    assert package["package_type"] == "corrective_retry_v3_implementation_package"
    assert package["operator_retry_v3_plan_approved"] == True
    assert package["blind_retry_allowed"] == False
    assert package["generation_allowed"] == False
    assert package["retry_allowed"] == False
    assert package["patches"]["sampler_recipe_patch_created"] == True
    assert package["patches"]["prompt_quality_patch_created"] == True
    assert package["patches"]["workflow_quality_patch_created"] == True
    assert package["patches"]["contrast_blur_correction_patch_created"] == True
    assert package["patches"]["conditioning_chain_review_patch_created"] == True
    assert package["next_allowed_action"] == "operator_retry_v3_generation_authorization_required"


def test_sampler_recipe_patch_created(tmp_path):
    """Test that sampler recipe patch is created."""
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
    
    sampler_plan = {"recommended_changes": {"steps": 30}, "sampler_elements_to_review": ["steps"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_plan.json", 'w') as f:
        json.dump(sampler_plan, f)
    
    prompt_plan = {"recommended_changes": {}, "prompt_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_prompt_plan.json", 'w') as f:
        json.dump(prompt_plan, f)
    
    workflow_plan = {"recommended_changes": {}, "workflow_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_workflow_quality_plan.json", 'w') as f:
        json.dump(workflow_plan, f)
    
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
    
    # Verify sampler patch
    patch_path = control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_patch.json"
    with open(patch_path, 'r') as f:
        patch = json.load(f)
    
    assert patch["patch_type"] == "corrective_retry_v3_sampler_recipe_patch"
    assert patch["patch_created"] == True
    assert patch["generation_allowed"] == False


def test_prompt_quality_patch_created(tmp_path):
    """Test that prompt quality patch is created."""
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
    
    sampler_plan = {"recommended_changes": {}, "sampler_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_plan.json", 'w') as f:
        json.dump(sampler_plan, f)
    
    prompt_plan = {"recommended_changes": {"add_detail": True}, "prompt_elements_to_review": ["detail"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_prompt_plan.json", 'w') as f:
        json.dump(prompt_plan, f)
    
    workflow_plan = {"recommended_changes": {}, "workflow_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_workflow_quality_plan.json", 'w') as f:
        json.dump(workflow_plan, f)
    
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
    
    # Verify prompt patch
    patch_path = control_dir / "combine_v2_corrective_retry_v3_prompt_quality_patch.json"
    with open(patch_path, 'r') as f:
        patch = json.load(f)
    
    assert patch["patch_type"] == "corrective_retry_v3_prompt_quality_patch"
    assert patch["patch_created"] == True
    assert patch["generation_allowed"] == False


def test_workflow_quality_patch_created(tmp_path):
    """Test that workflow quality patch is created."""
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
    
    sampler_plan = {"recommended_changes": {}, "sampler_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_plan.json", 'w') as f:
        json.dump(sampler_plan, f)
    
    prompt_plan = {"recommended_changes": {}, "prompt_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_prompt_plan.json", 'w') as f:
        json.dump(prompt_plan, f)
    
    workflow_plan = {"recommended_changes": {"cfg_scale": 7.5}, "workflow_elements_to_review": ["cfg"]}
    with open(control_dir / "combine_v2_corrective_retry_v3_workflow_quality_plan.json", 'w') as f:
        json.dump(workflow_plan, f)
    
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
    
    # Verify workflow patch
    patch_path = control_dir / "combine_v2_corrective_retry_v3_workflow_quality_patch.json"
    with open(patch_path, 'r') as f:
        patch = json.load(f)
    
    assert patch["patch_type"] == "corrective_retry_v3_workflow_quality_patch"
    assert patch["patch_created"] == True
    assert patch["generation_allowed"] == False


def test_contrast_blur_patch_created(tmp_path):
    """Test that contrast/blur correction patch is created."""
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
    
    sampler_plan = {"recommended_changes": {}, "sampler_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_sampler_recipe_plan.json", 'w') as f:
        json.dump(sampler_plan, f)
    
    prompt_plan = {"recommended_changes": {}, "prompt_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_prompt_plan.json", 'w') as f:
        json.dump(prompt_plan, f)
    
    workflow_plan = {"recommended_changes": {}, "workflow_elements_to_review": []}
    with open(control_dir / "combine_v2_corrective_retry_v3_workflow_quality_plan.json", 'w') as f:
        json.dump(workflow_plan, f)
    
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
    
    # Verify contrast/blur patch
    patch_path = control_dir / "combine_v2_corrective_retry_v3_contrast_blur_patch.json"
    with open(patch_path, 'r') as f:
        patch = json.load(f)
    
    assert patch["patch_type"] == "corrective_retry_v3_contrast_blur_patch"
    assert patch["patch_created"] == True
    assert patch["target_failures"] == ["blur_detected", "low_contrast"]
    assert patch["corrections"]["increase_sharpening"] == True
    assert patch["corrections"]["adjust_contrast_enhancement"] == True
    assert patch["generation_allowed"] == False


def test_implementation_package_missing_approval(tmp_path):
    """Test error when operator approval is missing."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure without approval
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_implementation_package(args)
    
    # Assert failure
    assert result == 1


def test_implementation_package_not_approved(tmp_path):
    """Test error when plan is not approved."""
    from app.cli import combine_build_corrective_retry_v3_implementation_package
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create approval with not approved
    approval = {
        "operator_retry_v3_plan_approved": False,
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_operator_retry_v3_plan_approval.json", 'w') as f:
        json.dump(approval, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        json=True,
    )
    
    # Run command
    result = combine_build_corrective_retry_v3_implementation_package(args)
    
    # Assert failure
    assert result == 1
