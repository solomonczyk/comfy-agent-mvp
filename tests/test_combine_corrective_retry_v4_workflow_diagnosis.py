"""Test corrective retry V4 workflow diagnosis - RC-COMBINE-V2-1821-1880."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import combine_diagnose_corrective_retry_v4_workflow


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_diagnose_stub_workflow_detected(temp_project_root):
    """Test diagnosis detects stub/fallback workflow."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create stub workflow audit
    workflow_audit = {
        "audit_type": "corrective_retry_v4_workflow_submit_audit",
        "workflow_stubbed": True,
        "real_workflow_in_package": False,
        "stub_or_fallback_workflow_detected": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json").write_text(
        json.dumps(workflow_audit)
    )
    
    # Create stub submitted workflow
    stub_workflow = {"1": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024}}}
    (control_dir / "shot02_submitted_workflow.json").write_text(json.dumps(stub_workflow))
    
    # Create generation trace with stub flag
    generation_trace = {
        "events": [{"event": "comfyui_execution", "stub": True}]
    }
    (control_dir / "combine_v2_corrective_retry_v4_generation_trace.json").write_text(
        json.dumps(generation_trace)
    )
    
    # Run diagnosis
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
        result = combine_diagnose_corrective_retry_v4_workflow(args)
    
    assert result == 0
    
    # Check diagnosis artifact
    diagnosis_path = control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json"
    assert diagnosis_path.exists()
    
    diagnosis = json.loads(diagnosis_path.read_text())
    assert diagnosis["v4_workflow_diagnosis_executed"] == True
    assert diagnosis["stub_or_fallback_workflow_detected"] == True
    assert diagnosis["fallback_workflow_allowed"] == False
    assert diagnosis["real_workflow_required"] == True
    assert diagnosis["submit_blocked_until_real_workflow_bound"] == True
    assert diagnosis["next_allowed_action"] == "corrective_retry_v4_real_workflow_binding_review_required"


def test_diagnose_real_workflow_not_detected(temp_project_root):
    """Test diagnosis when real workflow is not present."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create workflow audit indicating no real workflow
    workflow_audit = {
        "audit_type": "corrective_retry_v4_workflow_submit_audit",
        "workflow_stubbed": True,
        "real_workflow_in_package": False,
        "stub_or_fallback_workflow_detected": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json").write_text(
        json.dumps(workflow_audit)
    )
    
    # Run diagnosis
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock) as mock_stdout:
        result = combine_diagnose_corrective_retry_v4_workflow(args)
    
    assert result == 0
    
    diagnosis = json.loads((control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").read_text())
    assert diagnosis["stub_or_fallback_workflow_detected"] == True


def test_diagnose_generation_performed_false(temp_project_root):
    """Test diagnosis confirms no generation was performed."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create minimal artifacts
    (control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json").write_text(
        json.dumps({"stub_or_fallback_workflow_detected": True})
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_diagnose_corrective_retry_v4_workflow(args)
    
    assert result == 0
    
    diagnosis = json.loads((control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").read_text())
    assert diagnosis["new_generation_performed"] == False
    assert diagnosis["new_comfyui_submit_executed"] == False
    assert diagnosis["retry_attempted"] == False


def test_diagnose_visual_qa_not_executed(temp_project_root):
    """Test diagnosis confirms visual QA was not executed."""
    control_dir = temp_project_root / "output" / "control"
    
    (control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json").write_text(
        json.dumps({"stub_or_fallback_workflow_detected": True})
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_diagnose_corrective_retry_v4_workflow(args)
    
    assert result == 0
    
    diagnosis = json.loads((control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").read_text())
    assert diagnosis["visual_qa_executed"] == False
    assert diagnosis["assembly_executed"] == False
    assert diagnosis["downstream_executed"] == False


def test_diagnose_production_accepted_false(temp_project_root):
    """Test diagnosis confirms production_accepted is false."""
    control_dir = temp_project_root / "output" / "control"
    
    (control_dir / "combine_v2_corrective_retry_v4_workflow_submit_audit.json").write_text(
        json.dumps({"stub_or_fallback_workflow_detected": True})
    )
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_diagnose_corrective_retry_v4_workflow(args)
    
    assert result == 0
    
    diagnosis = json.loads((control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").read_text())
    assert diagnosis["production_accepted"] == False
