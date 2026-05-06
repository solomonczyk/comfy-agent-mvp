"""Tests for combine corrective retry V4 generation authorization.

RC-COMBINE-V2-1701-1760 — Test operator authorization for one controlled retry V4 generation.
"""

import json
import pytest
from pathlib import Path
import argparse


def test_combine_authorize_corrective_retry_v4_generation_approve(tmp_path):
    """Test approving one corrective retry V4 generation."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required implementation package
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
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    # Create authorization request
    auth_request = {
        "request_type": "operator_retry_v4_generation_authorization_request",
        "operator_review_required": True,
    }
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="operator_approved_one_retry_v4_generation_after_implementation_package_review",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert success
    assert result == 0
    
    # Verify authorization artifact created
    auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
    assert auth_path.exists()
    
    with open(auth_path, 'r') as f:
        authorization = json.load(f)
    
    assert authorization["operator_decision"] == "approve_one_corrective_retry_v4_generation"
    assert authorization["operator_retry_v4_generation_authorized"] == True
    assert authorization["corrective_retry_v4_implementation_package_available"] == True
    assert authorization["max_generations"] == 1
    assert authorization["generation_allowed"] == True
    assert authorization["retry_allowed"] == True
    assert authorization["next_allowed_action"] == "corrective_retry_v4_generate_assets"


def test_combine_authorize_corrective_retry_v4_generation_reject(tmp_path):
    """Test rejecting corrective retry V4 generation."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    auth_request = {"operator_review_required": True}
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="reject_corrective_retry_v4_generation",
        reason="operator_rejected_retry_v4_generation",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert success
    assert result == 0
    
    # Verify authorization
    auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
    with open(auth_path, 'r') as f:
        authorization = json.load(f)
    
    assert authorization["operator_decision"] == "reject_corrective_retry_v4_generation"
    assert authorization["operator_retry_v4_generation_authorized"] == False
    assert authorization["generation_allowed"] == False
    assert authorization["retry_allowed"] == False
    assert authorization["next_allowed_action"] == "operator_retry_v4_generation_authorization_required"


def test_combine_authorize_corrective_retry_v4_generation_missing_package(tmp_path):
    """Test error when implementation package is missing."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure without package
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert failure
    assert result == 1


def test_combine_authorize_corrective_retry_v4_generation_invalid_decision(tmp_path):
    """Test error with invalid decision."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    package = {"source_asset": "test.png", "failure_basis": []}
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    auth_request = {}
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args with invalid decision
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="invalid_decision",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert failure
    assert result == 1


def test_operator_can_authorize_one_corrective_retry_v4_generation(tmp_path):
    """Test that operator can authorize exactly one generation."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected", "low_contrast"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    auth_request = {"operator_review_required": True}
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="operator_approved_one_retry_v4_generation",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert success
    assert result == 0
    
    # Verify max_generations is 1
    auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
    with open(auth_path, 'r') as f:
        authorization = json.load(f)
    
    assert authorization["max_generations"] == 1


def test_implementation_package_required(tmp_path):
    """Test that implementation package is required for authorization."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure without package
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert failure
    assert result == 1


def test_max_generations_enforced_as_one(tmp_path):
    """Test that max_generations is enforced as 1."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    auth_request = {}
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert success
    assert result == 0
    
    # Verify max_generations is 1
    auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
    with open(auth_path, 'r') as f:
        authorization = json.load(f)
    
    assert authorization["max_generations"] == 1


def test_authorization_no_downstream_boundary(tmp_path):
    """Test that authorization respects no downstream boundary."""
    from app.cli import combine_authorize_corrective_retry_v4_generation
    
    # Setup project structure
    project_root = tmp_path / "project"
    project_root.mkdir()
    control_dir = project_root / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create required files
    package = {
        "source_asset": "output/assets/test.png",
        "failure_basis": ["blur_detected"],
    }
    with open(control_dir / "combine_v2_corrective_retry_v4_implementation_package.json", 'w') as f:
        json.dump(package, f)
    
    auth_request = {}
    with open(control_dir / "combine_v2_operator_retry_v4_generation_authorization_request.json", 'w') as f:
        json.dump(auth_request, f)
    
    # Create args
    args = argparse.Namespace(
        project_root=str(project_root),
        shot_id="shot02",
        decision="approve_one_corrective_retry_v4_generation",
        reason="test",
        json=True,
    )
    
    # Run command
    result = combine_authorize_corrective_retry_v4_generation(args)
    
    # Assert success
    assert result == 0
    
    # Verify no downstream operations allowed
    auth_path = control_dir / "combine_v2_operator_retry_v4_generation_authorization.json"
    with open(auth_path, 'r') as f:
        authorization = json.load(f)
    
    assert authorization["visual_qa_executed"] == False
    assert authorization["assembly_executed"] == False
    assert authorization["downstream_executed"] == False
    assert authorization["production_accepted"] == False
