"""
RC-COMBINE-V2-1041-1100 — Tests for Corrective Retry V2 One Submit

Tests for exactly one corrective retry generation v2 submit with strict enforcement:
- Must use corrective_retry_package_v2
- Shot-specific workflow binding required
- Cross-shot workflow reuse blocked
- Prompt patch v2 required
- Fallback minimal workflow forbidden
- Max generations: 1
- No second generation attempt
- No blind retry
- No visual QA
- No assembly
- No downstream
"""

import json
import pytest
from pathlib import Path
from app.cli import combine_corrective_retry_generate_assets_v2
import argparse


@pytest.fixture
def temp_project_root_with_auth(tmp_path: Path):
    """Create a temporary project root with required artifacts including authorization."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create authorization v2
    auth_v2 = {
        "stage": "operator_retry_generation_authorization_required",
        "operator_decision": "approve_one_corrective_retry_generation_v2",
        "operator_retry_generation_authorized_v2": True,
        "corrective_retry_package_v2_required": True,
        "corrective_retry_package_v2_available": True,
        "shot_specific_workflow_binding_required": True,
        "cross_shot_workflow_reuse_blocked": True,
        "prompt_patch_v2_required": True,
        "prompt_patch_v2_verified": True,
        "fallback_minimal_workflow_forbidden": True,
        "max_generations": 1,
        "generation_allowed": True,
        "retry_allowed": True,
        "workflow_submitted": False,
        "comfyui_execution": False,
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "shot_id": "shot02",
        "reason": "Approved for v2 corrective retry",
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_operator_retry_generation_authorization_v2.json", 'w') as f:
        json.dump(auth_v2, f)
    
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
    
    # Create shot-specific workflow
    workflow = {
        "shot_id": "shot02",
        "1": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 1024
            }
        }
    }
    with open(control_dir / "shot02_submitted_workflow.json", 'w') as f:
        json.dump(workflow, f)
    
    return tmp_path


def test_corrective_retry_package_v2_required_for_submit(temp_project_root_with_auth: Path):
    """Test that corrective_retry_package_v2.json is required for submit."""
    control_dir = temp_project_root_with_auth / "output" / "control"
    # Remove package v2
    package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
    package_path.unlink()
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail


def test_corrective_retry_package_v2_used_in_submit(temp_project_root_with_auth: Path):
    """Test that corrective_retry_package_v2 is used during submit."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["corrective_retry_package_v2_used"] is True


def test_shot_specific_workflow_binding_checked_before_submit(temp_project_root_with_auth: Path):
    """Test that shot-specific workflow binding is checked before submit."""
    # Create workflow with wrong shot_id
    control_dir = temp_project_root_with_auth / "output" / "control"
    workflow_path = control_dir / "shot02_submitted_workflow.json"
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    workflow["shot_id"] = "shot01"  # Wrong shot
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail due to shot mismatch


def test_cross_shot_workflow_reuse_blocks_submit(temp_project_root_with_auth: Path):
    """Test that cross-shot workflow reuse blocks submit."""
    control_dir = temp_project_root_with_auth / "output" / "control"
    package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
    with open(package_path, 'r') as f:
        package = json.load(f)
    package["cross_shot_workflow_reuse_blocked"] = False  # Not blocked
    with open(package_path, 'w') as f:
        json.dump(package, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail


def test_prompt_patch_v2_required_before_submit(temp_project_root_with_auth: Path):
    """Test that prompt patch v2 is required before submit."""
    control_dir = temp_project_root_with_auth / "output" / "control"
    # Remove prompt patch v2
    prompt_patch_path = control_dir / "combine_v2_prompt_patch_v2.json"
    prompt_patch_path.unlink()
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail


def test_fallback_minimal_workflow_forbidden(temp_project_root_with_auth: Path):
    """Test that fallback minimal workflow is forbidden."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    pre_submit_path = control_dir / "combine_v2_corrective_retry_v2_pre_submit_validation.json"
    with open(pre_submit_path, 'r') as f:
        pre_submit = json.load(f)
    
    assert pre_submit["fallback_minimal_workflow_forbidden"] is True


def test_generation_attempts_limited_to_one(temp_project_root_with_auth: Path):
    """Test that max_generations is limited to 1."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=2,  # Try to set to 2
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail because max_generations must be 1


def test_workflow_submitted(temp_project_root_with_auth: Path):
    """Test that workflow is submitted during generation."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["workflow_submitted"] is True
    assert result_data["generation_performed"] is True


def test_comfyui_execution(temp_project_root_with_auth: Path):
    """Test that comfyui_execution reflects execute flag."""
    # Test dry run
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["comfyui_execution"] is False


def test_second_generation_blocked(temp_project_root_with_auth: Path):
    """Test that second generation is blocked."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["second_generation_attempted"] is False
    assert result_data["blind_retry_allowed"] is False


def test_visual_qa_not_executed(temp_project_root_with_auth: Path):
    """Test that visual QA is not executed during generation."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["visual_qa_executed"] is False


def test_assembly_not_executed(temp_project_root_with_auth: Path):
    """Test that assembly is not executed during generation."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["assembly_executed"] is False


def test_downstream_not_executed(temp_project_root_with_auth: Path):
    """Test that downstream is not executed during generation."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["downstream_executed"] is False


def test_production_accepted_false(temp_project_root_with_auth: Path):
    """Test that production_accepted is false during generation."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=True
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 0
    
    control_dir = temp_project_root_with_auth / "output" / "control"
    result_path = control_dir / "combine_v2_corrective_retry_v2_generation_result.json"
    with open(result_path, 'r') as f:
        result_data = json.load(f)
    
    assert result_data["production_accepted"] is False


def test_legacy_512_workflow_blocked(temp_project_root_with_auth: Path):
    """Test that legacy 512 workflows are blocked."""
    control_dir = temp_project_root_with_auth / "output" / "control"
    # Create workflow with 512 resolution
    workflow_path = control_dir / "shot02_submitted_workflow.json"
    workflow = {
        "shot_id": "shot02",
        "1": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 512
            }
        }
    }
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail due to legacy 512 workflow


def test_minimum_short_side_1024_enforced(temp_project_root_with_auth: Path):
    """Test that minimum short side 1024 is enforced."""
    control_dir = temp_project_root_with_auth / "output" / "control"
    # Create workflow with short side < 1024
    workflow_path = control_dir / "shot02_submitted_workflow.json"
    workflow = {
        "shot_id": "shot02",
        "1": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1024,
                "height": 512
            }
        }
    }
    with open(workflow_path, 'w') as f:
        json.dump(workflow, f)
    
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_auth),
        shot_id="shot02",
        execute=False,
        max_generations=1,
        json=False
    )
    
    result = combine_corrective_retry_generate_assets_v2(args)
    assert result == 1  # Should fail due to short side < 1024
