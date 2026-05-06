"""Test corrective retry V4 no fallback workflow guard - RC-COMBINE-V2-1821-1880."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import combine_validate_corrective_retry_v4_real_workflow_binding


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_validate_binding_stub_fallback_blocked(temp_project_root):
    """Test validation confirms stub/fallback workflow is blocked."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create binding artifact
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": False,
        "workflow_node_count": 1,
        "saveimage_configured": False,
        "fallback_workflow_blocked": True,
        "real_workflow_required_before_submit": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_validation.json").read_text())
    assert validation["fallback_workflow_blocked"] == True
    assert validation["real_workflow_required_before_submit"] == True


def test_validate_guard_artifact_created(temp_project_root):
    """Test guard artifact is created."""
    control_dir = temp_project_root / "output" / "control"
    
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": True,
        "workflow_node_count": 5,
        "saveimage_configured": True,
        "fallback_workflow_blocked": True,
        "real_workflow_required_before_submit": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    guard_path = control_dir / "combine_v2_retry_v4_no_fallback_workflow_guard.json"
    assert guard_path.exists()
    
    guard = json.loads(guard_path.read_text())
    assert guard["guard_type"] == "retry_v4_no_fallback_workflow_guard"
    assert guard["guard_enabled"] == True
    assert guard["stub_or_fallback_workflow_blocked"] == True


def test_validate_binding_requires_binding_exists(temp_project_root):
    """Test validation requires binding to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No binding artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 1  # Error exit code


def test_validate_generation_not_performed(temp_project_root):
    """Test validation confirms generation was not performed."""
    control_dir = temp_project_root / "output" / "control"
    
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": True,
        "workflow_node_count": 5,
        "saveimage_configured": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_validation.json").read_text())
    assert validation["generation_not_performed"] == True
    assert validation["comfyui_submit_not_executed"] == True


def test_validate_visual_qa_not_executed(temp_project_root):
    """Test validation confirms visual QA was not executed."""
    control_dir = temp_project_root / "output" / "control"
    
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": True,
        "workflow_node_count": 5,
        "saveimage_configured": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_validation.json").read_text())
    assert validation["visual_qa_not_executed"] == True
    assert validation["assembly_not_executed"] == True


def test_validate_production_accepted_false(temp_project_root):
    """Test validation confirms production_accepted is false."""
    control_dir = temp_project_root / "output" / "control"
    
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": True,
        "workflow_node_count": 5,
        "saveimage_configured": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_validation.json").read_text())
    assert validation["production_accepted_false"] == True


def test_validate_binding_valid_when_real_workflow(temp_project_root):
    """Test validation passes when real workflow is available."""
    control_dir = temp_project_root / "output" / "control"
    
    binding = {
        "real_workflow_binding_created": True,
        "real_workflow_available": True,
        "workflow_node_count": 5,
        "saveimage_configured": True,
        "fallback_workflow_blocked": True,
        "real_workflow_required_before_submit": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").write_text(
        json.dumps(binding)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_validate_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    validation = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_validation.json").read_text())
    assert validation["binding_valid"] == True
    
    guard = json.loads((control_dir / "combine_v2_retry_v4_no_fallback_workflow_guard.json").read_text())
    assert guard["submit_blocked_until_real_workflow_bound"] == False
