"""Test corrective retry V4 real workflow submit preflight - RC-COMBINE-V2-1881-2000."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import combine_preflight_corrective_retry_v4_real_workflow_submit


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_preflight_real_workflow_submit_executed(temp_project_root):
    """Test real workflow submit preflight is executed successfully."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create validation artifact
    validation = {
        "generator_loader_fix_validated": True,
        "validation_passed": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").write_text(
        json.dumps(validation)
    )
    
    # Create application artifact
    application = {
        "generator_loader_fix_applied": True,
        "hardcoded_stub_generation_removed": True,
        "submit_blocks_without_valid_real_workflow": True,
        "max_generations_one_preserved": True,
        "post_submit_validation_preserved": True,
        "stub_asset_guard_preserved": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    # Create review artifact
    review = {
        "real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"
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
        max_generations=1,
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_preflight_corrective_retry_v4_real_workflow_submit(args)
    
    assert result == 0
    
    # Check preflight artifact
    preflight_path = control_dir / "combine_v2_corrective_retry_v4_real_workflow_submit_preflight.json"
    assert preflight_path.exists()
    
    preflight = json.loads(preflight_path.read_text())
    assert preflight["real_workflow_preflight_executed"] == True
    assert preflight["preflight_passed"] == True
    assert preflight["workflow_valid_for_submit"] == True
    assert preflight["dry_run_mode"] == True
    assert preflight["comfyui_submit_not_executed"] == True
    assert preflight["next_allowed_action"] == "corrective_retry_v4_generate_assets"


def test_preflight_real_workflow_submit_requires_validation(temp_project_root):
    """Test preflight requires validation to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No validation artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        max_generations=1,
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_preflight_corrective_retry_v4_real_workflow_submit(args)
    
    assert result == 1  # Error exit code


def test_preflight_real_workflow_submit_validates_workflow(temp_project_root):
    """Test preflight validates workflow has required nodes."""
    control_dir = temp_project_root / "output" / "control"
    
    validation = {"generator_loader_fix_validated": True, "validation_passed": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").write_text(
        json.dumps(validation)
    )
    
    application = {
        "generator_loader_fix_applied": True,
        "hardcoded_stub_generation_removed": True,
        "submit_blocks_without_valid_real_workflow": True,
        "max_generations_one_preserved": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    review = {"real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    # Stub workflow - only EmptyLatentImage
    stub_workflow = {"1": {"class_type": "EmptyLatentImage", "inputs": {}}}
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(stub_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        max_generations=1,
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_preflight_corrective_retry_v4_real_workflow_submit(args)
    
    assert result == 0
    
    preflight = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_submit_preflight.json").read_text())
    assert preflight["workflow_valid_for_submit"] == False
    assert preflight["preflight_passed"] == False


def test_preflight_real_workflow_submit_no_generation(temp_project_root):
    """Test preflight does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    validation = {"generator_loader_fix_validated": True, "validation_passed": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").write_text(
        json.dumps(validation)
    )
    
    application = {"generator_loader_fix_applied": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    review = {"real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
    real_workflow = {
        "3": {"class_type": "KSampler", "inputs": {}},
        "9": {"class_type": "SaveImage", "inputs": {}}
    }
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(real_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        max_generations=1,
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_preflight_corrective_retry_v4_real_workflow_submit(args)
    
    assert result == 0
    
    preflight = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_submit_preflight.json").read_text())
    assert preflight["new_generation_performed"] == False
    assert preflight["new_comfyui_submit_executed"] == False
    assert preflight["retry_attempted"] == False
    assert preflight["visual_qa_executed"] == False
    assert preflight["assembly_executed"] == False


def test_preflight_real_workflow_submit_max_generations_preserved(temp_project_root):
    """Test preflight preserves max_generations parameter."""
    control_dir = temp_project_root / "output" / "control"
    
    validation = {"generator_loader_fix_validated": True, "validation_passed": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_validation.json").write_text(
        json.dumps(validation)
    )
    
    application = {"generator_loader_fix_applied": True, "max_generations_one_preserved": True}
    (control_dir / "combine_v2_corrective_retry_v4_generator_loader_fix_application.json").write_text(
        json.dumps(application)
    )
    
    review = {"real_workflow_source_candidate": "ep01_shot01_submitted_workflow.json"}
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").write_text(
        json.dumps(review)
    )
    
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
        max_generations=1,
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_preflight_corrective_retry_v4_real_workflow_submit(args)
    
    assert result == 0
    
    preflight = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_submit_preflight.json").read_text())
    assert preflight["max_generations"] == 1
    assert preflight["max_generations_one_preserved"] == True

