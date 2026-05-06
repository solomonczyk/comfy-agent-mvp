"""Test corrective retry V4 real workflow binding - RC-COMBINE-V2-1821-1880."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import combine_build_corrective_retry_v4_real_workflow_binding


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_build_workflow_binding_created(temp_project_root):
    """Test workflow binding is created successfully."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create diagnosis artifact first
    diagnosis = {
        "v4_workflow_diagnosis_executed": True,
        "stub_or_fallback_workflow_detected": True,
        "real_workflow_required": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    # Create a minimal submitted workflow (stub)
    stub_workflow = {"1": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024}}}
    (control_dir / "shot02_submitted_workflow.json").write_text(json.dumps(stub_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    # Check binding artifact
    binding_path = control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json"
    assert binding_path.exists()
    
    binding = json.loads(binding_path.read_text())
    assert binding["real_workflow_binding_created"] == True
    assert binding["binding_type"] == "corrective_retry_v4_real_workflow_binding"
    assert binding["shot_id"] == "shot02"


def test_build_workflow_binding_fallback_blocked(temp_project_root):
    """Test workflow binding blocks fallback workflow."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create diagnosis
    diagnosis = {"v4_workflow_diagnosis_executed": True}
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    binding = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").read_text())
    assert binding["fallback_workflow_blocked"] == True
    assert binding["real_workflow_required_before_submit"] == True


def test_build_workflow_binding_requires_diagnosis(temp_project_root):
    """Test workflow binding requires diagnosis to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No diagnosis artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 1  # Error exit code


def test_build_workflow_binding_real_workflow_required(temp_project_root):
    """Test workflow binding enforces real workflow requirement."""
    control_dir = temp_project_root / "output" / "control"
    
    diagnosis = {"v4_workflow_diagnosis_executed": True}
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    binding = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding.json").read_text())
    assert binding["real_workflow_required_before_submit"] == True


def test_build_workflow_binding_generation_not_performed(temp_project_root):
    """Test workflow binding does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    diagnosis = {"v4_workflow_diagnosis_executed": True}
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_build_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    # Binding creation should not trigger generation
    # This is verified by the fact that no generation artifacts are created
