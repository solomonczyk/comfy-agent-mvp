"""Test corrective retry V4 generator loader fix - RC-COMBINE-V2-1881-2000."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import (
    combine_build_corrective_retry_v4_generator_loader_fix_plan,
    combine_validate_corrective_retry_v4_generator_loader_fix_plan,
    combine_apply_corrective_retry_v4_generator_loader_fix,
    combine_validate_corrective_retry_v4_generator_loader_fix
)


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_build_generator_loader_fix_plan_created(temp_project_root):
    """Test generator loader fix plan is created successfully."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create review artifact
    review = {
        "real_workflow_binding_review_executed": True,
        "real_workflow_source_candidate_identified": True,
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json",
        "real_workflow_candidate_path": "ep01_shot01_submitted_workflow.json",
        "real_workflow_candidate_is_not_stub": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 0
    
    # Check fix plan artifact
    fix_plan_path = control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json"
    assert fix_plan_path.exists()
    
    fix_plan = json.loads(fix_plan_path.read_text())
    assert fix_plan["generator_loader_fix_plan_created"] == True
    assert fix_plan["hardcoded_stub_generation_must_be_removed"] == True
    assert fix_plan["generator_must_load_approved_real_workflow_binding"] == True
    assert fix_plan["submit_must_block_without_valid_real_workflow"] == True
    assert fix_plan["max_generations_one_preserved"] == True
    assert fix_plan["post_submit_validation_preserved"] == True
    assert fix_plan["stub_asset_guard_preserved"] == True


def test_build_generator_loader_fix_plan_requires_review(temp_project_root):
    """Test generator loader fix plan requires review to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No review artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 1  # Error exit code


def test_build_generator_loader_fix_plan_fix_components(temp_project_root):
    """Test generator loader fix plan includes all required fix components."""
    control_dir = temp_project_root / "output" / "control"
    
    review = {
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json",
        "real_workflow_candidate_path": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 0
    
    fix_plan = json.loads((control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").read_text())
    assert "remove_hardcoded_stub_generation" in fix_plan["fix_components"]
    assert "load_real_workflow_from_binding" in fix_plan["fix_components"]
    assert "block_submit_without_valid_workflow" in fix_plan["fix_components"]
    assert "preserve_max_generations_one" in fix_plan["fix_components"]
    assert "preserve_post_submit_validation" in fix_plan["fix_components"]
    assert "preserve_stub_asset_guard" in fix_plan["fix_components"]


def test_build_generator_loader_fix_plan_no_generation(temp_project_root):
    """Test generator loader fix plan does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    review = {"real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 0
    
    fix_plan = json.loads((control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").read_text())
    assert fix_plan["new_generation_performed"] == False
    assert fix_plan["new_comfyui_submit_executed"] == False
    assert fix_plan["retry_attempted"] == False


def test_validate_generator_loader_fix_plan(temp_project_root):
    """Test generator loader fix plan validation."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create fix plan
    fix_plan = {
        "generator_loader_fix_plan_created": True,
        "hardcoded_stub_generation_must_be_removed": True,
        "generator_must_load_approved_real_workflow_binding": True,
        "submit_must_block_without_valid_real_workflow": True,
        "max_generations_one_preserved": True,
        "post_submit_validation_preserved": True,
        "stub_asset_guard_preserved": True,
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").write_text(
        json.dumps(fix_plan)
    )
    
    # Create review
    review = {
        "real_workflow_source_candidate_identified": True,
        "real_workflow_candidate_is_not_stub": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 0
    
    validation_path = control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json"
    assert validation_path.exists()
    
    validation = json.loads(validation_path.read_text())
    assert validation["generator_loader_fix_plan_validated"] == True
    assert validation["validation_passed"] == True


def test_validate_generator_loader_fix_plan_requires_fix_plan(temp_project_root):
    """Test validation requires fix plan to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No fix plan artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 1  # Error exit code


def test_validate_generator_loader_fix_plan_no_generation(temp_project_root):
    """Test validation does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    fix_plan = {
        "generator_loader_fix_plan_created": True,
        "hardcoded_stub_generation_must_be_removed": True,
        "generator_must_load_approved_real_workflow_binding": True,
        "submit_must_block_without_valid_real_workflow": True,
        "max_generations_one_preserved": True,
        "post_submit_validation_preserved": True,
        "stub_asset_guard_preserved": True,
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").write_text(
        json.dumps(fix_plan)
    )
    
    review = {"real_workflow_source_candidate_identified": True, "real_workflow_candidate_is_not_stub": True}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix_plan(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").read_text())
    assert validation["new_generation_performed"] == False
    assert validation["new_comfyui_submit_executed"] == False
    assert validation["retry_attempted"] == False


def test_apply_generator_loader_fix(temp_project_root):
    """Test generator loader fix is applied successfully."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create fix plan
    fix_plan = {
        "generator_loader_fix_plan_created": True,
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").write_text(
        json.dumps(fix_plan)
    )
    
    # Create review
    review = {
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json",
        "real_workflow_candidate_is_not_stub": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    # Create real workflow
    real_workflow = {
        "3": {"class_type": "KSampler", "inputs": {}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {}},
        "9": {"class_type": "SaveImage", "inputs": {}}
    }
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(real_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_apply_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 0
    
    # Check application artifact
    application_path = control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json"
    assert application_path.exists()
    
    application = json.loads(application_path.read_text())
    assert application["generator_loader_fix_applied"] == True
    assert application["hardcoded_stub_generation_removed"] == True
    assert application["generator_loads_approved_real_workflow_binding"] == True
    assert application["submit_blocks_without_valid_real_workflow"] == True
    assert application["real_workflow_loaded"] == True


def test_apply_generator_loader_fix_requires_fix_plan(temp_project_root):
    """Test apply requires fix plan to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No fix plan artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_apply_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 1  # Error exit code


def test_apply_generator_loader_fix_no_generation(temp_project_root):
    """Test apply does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    fix_plan = {"generator_loader_fix_plan_created": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_plan.json").write_text(
        json.dumps(fix_plan)
    )
    
    review = {"real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_apply_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 0
    
    application = json.loads((control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").read_text())
    assert application["new_generation_performed"] == False
    assert application["new_comfyui_submit_executed"] == False
    assert application["retry_attempted"] == False


def test_validate_generator_loader_fix_applied(temp_project_root):
    """Test generator loader fix validation after application."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create application
    application = {
        "generator_loader_fix_applied": True,
        "hardcoded_stub_generation_removed": True,
        "generator_loads_approved_real_workflow_binding": True,
        "submit_blocks_without_valid_real_workflow": True,
        "max_generations_one_preserved": True,
        "post_submit_validation_preserved": True,
        "stub_asset_guard_preserved": True,
        "real_workflow_loaded": True,
        "real_workflow_has_ksampler": True,
        "real_workflow_has_saveimage": True,
        "real_workflow_source": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    # Create review
    review = {
        "real_workflow_candidate_is_not_stub": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 0
    
    # Check validation artifact
    validation_path = control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json"
    assert validation_path.exists()
    
    # Check guard artifact
    guard_path = control_dir / "combine_v2_retry_v4_no_fallback_workflow_guard.json"
    assert guard_path.exists()
    
    validation = json.loads(validation_path.read_text())
    assert validation["generator_loader_fix_validated"] == True
    assert validation["validation_passed"] == True
    
    guard = json.loads(guard_path.read_text())
    assert guard["guard_enabled"] == True
    assert guard["stub_or_fallback_workflow_blocked"] == True


def test_validate_generator_loader_fix_requires_application(temp_project_root):
    """Test validation requires application to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No application artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 1  # Error exit code


def test_validate_generator_loader_fix_no_generation(temp_project_root):
    """Test validation does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    application = {
        "generator_loader_fix_applied": True,
        "hardcoded_stub_generation_removed": True,
        "generator_loads_approved_real_workflow_binding": True,
        "submit_blocks_without_valid_real_workflow": True,
        "max_generations_one_preserved": True,
        "post_submit_validation_preserved": True,
        "stub_asset_guard_preserved": True,
        "real_workflow_loaded": True,
        "real_workflow_has_ksampler": True,
        "real_workflow_has_saveimage": True,
        "real_workflow_source": "ep01_shot01_submitted_workflow.json"
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    review = {"real_workflow_candidate_is_not_stub": True}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_generator_loader_fix(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").read_text())
    assert validation["new_generation_performed"] == False
    assert validation["new_comfyui_submit_executed"] == False
    assert validation["retry_attempted"] == False

