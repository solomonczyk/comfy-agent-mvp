"""
RC-COMBINE-V2-1041-1100 — Tests for Corrective Retry Generation Authorization V2

Tests for operator authorization of exactly one corrective retry generation v2
with strict package v2 enforcement, shot-specific workflow binding, and cross-shot reuse blocking.
"""

import json
import pytest
from pathlib import Path
from app.cli import combine_authorize_corrective_retry_generation_v2
import argparse


@pytest.fixture
def temp_project_root(tmp_path: Path):
    """Create a temporary project root with required artifacts."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create corrective retry package v2
    package_v2 = {
        "corrective_retry_package_v2_created": True,
        "shot_id": "shot02",
        "cross_shot_workflow_reuse_blocked": True,
        "prompt_patch_exact_text_dependency_removed": True,
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_corrective_retry_package_v2.json", 'w') as f:
        json.dump(package_v2, f)
    
    # Create prompt patch v2
    prompt_patch_v2 = {
        "prompt_patch_v2_created": True,
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_prompt_patch_v2.json", 'w') as f:
        json.dump(prompt_patch_v2, f)
    
    return tmp_path


def test_operator_can_authorize_one_corrective_retry_generation_v2(temp_project_root: Path):
    """Test operator can authorize exactly one corrective retry generation v2."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved for v2 corrective retry",
        json=False
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    # Check authorization artifact created
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    assert auth_path.exists()
    
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["operator_retry_generation_authorized_v2"] is True
    assert auth["operator_decision"] == "approve_one_corrective_retry_generation_v2"
    assert auth["max_generations"] == 1
    assert auth["shot_id"] == "shot02"
    assert auth["corrective_retry_package_v2_required"] is True
    assert auth["corrective_retry_package_v2_available"] is True
    assert auth["shot_specific_workflow_binding_required"] is True
    assert auth["cross_shot_workflow_reuse_blocked"] is True
    assert auth["prompt_patch_v2_required"] is True
    assert auth["prompt_patch_v2_verified"] is True
    assert auth["fallback_minimal_workflow_forbidden"] is True
    assert auth["generation_allowed"] is True
    assert auth["retry_allowed"] is True
    assert auth["workflow_submitted"] is False
    assert auth["comfyui_execution"] is False
    assert auth["visual_qa_executed"] is False
    assert auth["assembly_executed"] is False
    assert auth["downstream_executed"] is False
    assert auth["production_accepted"] is False
    assert auth["next_allowed_action"] == "corrective_retry_generate_assets_v2"


def test_corrective_retry_package_v2_required(temp_project_root: Path):
    """Test that corrective_retry_package_v2.json is required."""
    control_dir = temp_project_root / "output" / "control"
    # Remove package v2
    package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
    package_path.unlink()
    
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=False
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 1  # Should fail


def test_corrective_retry_package_v2_used(temp_project_root: Path):
    """Test that corrective_retry_package_v2 is used and verified."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["corrective_retry_package_v2_required"] is True
    assert auth["corrective_retry_package_v2_available"] is True


def test_shot_specific_workflow_binding_checked_before_submit(temp_project_root: Path):
    """Test that shot-specific workflow binding is checked before authorization."""
    # Create package with wrong shot_id
    control_dir = temp_project_root / "output" / "control"
    package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
    with open(package_path, 'r') as f:
        package = json.load(f)
    package["shot_id"] = "shot01"  # Wrong shot
    with open(package_path, 'w') as f:
        json.dump(package, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",  # Requesting shot02
        reason="Approved",
        json=False
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 1  # Should fail due to shot mismatch


def test_cross_shot_workflow_reuse_blocked(temp_project_root: Path):
    """Test that cross-shot workflow reuse is blocked."""
    control_dir = temp_project_root / "output" / "control"
    package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
    with open(package_path, 'r') as f:
        package = json.load(f)
    package["cross_shot_workflow_reuse_blocked"] = False  # Not blocked
    with open(package_path, 'w') as f:
        json.dump(package, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=False
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 1  # Should fail


def test_prompt_patch_v2_required_before_submit(temp_project_root: Path):
    """Test that prompt patch v2 is required before authorization."""
    control_dir = temp_project_root / "output" / "control"
    # Remove prompt patch v2
    prompt_patch_path = control_dir / "combine_v2_prompt_patch_v2.json"
    prompt_patch_path.unlink()
    
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=False
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 1  # Should fail


def test_fallback_minimal_workflow_forbidden(temp_project_root: Path):
    """Test that fallback minimal workflow is forbidden."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["fallback_minimal_workflow_forbidden"] is True


def test_generation_attempts_limited_to_one(temp_project_root: Path):
    """Test that max_generations is limited to 1."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["max_generations"] == 1


def test_workflow_submitted(temp_project_root: Path):
    """Test that workflow is not submitted during authorization."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["workflow_submitted"] is False
    assert auth["comfyui_execution"] is False


def test_visual_qa_not_executed(temp_project_root: Path):
    """Test that visual QA is not executed during authorization."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["visual_qa_executed"] is False


def test_assembly_not_executed(temp_project_root: Path):
    """Test that assembly is not executed during authorization."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["assembly_executed"] is False


def test_downstream_not_executed(temp_project_root: Path):
    """Test that downstream is not executed during authorization."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["downstream_executed"] is False


def test_production_accepted_false(temp_project_root: Path):
    """Test that production_accepted is false during authorization."""
    args = argparse.Namespace(
        project_root=str(temp_project_root),
        decision="approve_one_corrective_retry_generation_v2",
        shot_id="shot02",
        reason="Approved",
        json=True
    )
    
    result = combine_authorize_corrective_retry_generation_v2(args)
    assert result == 0
    
    control_dir = temp_project_root / "output" / "control"
    auth_path = control_dir / "combine_v2_operator_retry_generation_authorization_v2.json"
    with open(auth_path, 'r') as f:
        auth = json.load(f)
    
    assert auth["production_accepted"] is False
