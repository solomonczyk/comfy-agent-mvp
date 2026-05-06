"""Test corrective retry V4 real workflow binding review - RC-COMBINE-V2-1881-1940."""
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from app.cli import combine_review_corrective_retry_v4_real_workflow_binding


@pytest.fixture
def temp_project_root():
    """Create temporary project root with control directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root


def test_review_workflow_binding_created(temp_project_root):
    """Test workflow binding review is created successfully."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create diagnosis artifact
    diagnosis = {
        "v4_workflow_diagnosis_executed": True,
        "previous_failure_code": "CORRECTIVE_RETRY_V4_WORKFLOW_SUBMIT_INVALID",
        "stub_or_fallback_workflow_detected": True,
        "fallback_workflow_allowed": False,
        "real_workflow_required": True
    }
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    # Create shot01 workflow as real workflow candidate
    shot01_workflow = {
        "3": {"class_type": "KSampler", "inputs": {"seed": 123}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "test.safetensors"}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "test"}}
    }
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(shot01_workflow))
    
    # Create stub shot02 workflow
    stub_workflow = {"1": {"class_type": "EmptyLatentImage", "inputs": {"width": 1024, "height": 1024}}}
    (control_dir / "shot02_submitted_workflow.json").write_text(json.dumps(stub_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_review_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    # Check review artifact
    review_path = control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json"
    assert review_path.exists()
    
    review = json.loads(review_path.read_text())
    assert review["real_workflow_binding_review_executed"] == True
    assert review["previous_failure_code"] == "CORRECTIVE_RETRY_V4_WORKFLOW_SUBMIT_INVALID"
    assert review["hardcoded_stub_generation_root_cause_confirmed"] == True
    assert review["real_workflow_source_candidate_identified"] == True
    assert review["real_workflow_candidate_is_not_stub"] == True
    assert review["real_workflow_source_candidate"] == "ep01_shot01_submitted_workflow.json"


def test_review_workflow_binding_requires_diagnosis(temp_project_root):
    """Test workflow binding review requires diagnosis to exist first."""
    control_dir = temp_project_root / "output" / "control"
    
    # No diagnosis artifact
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_review_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 1  # Error exit code


def test_review_workflow_binding_identifies_real_candidate(temp_project_root):
    """Test workflow binding review identifies real workflow candidate."""
    control_dir = temp_project_root / "output" / "control"
    
    # Create diagnosis
    diagnosis = {
        "v4_workflow_diagnosis_executed": True,
        "previous_failure_code": "CORRECTIVE_RETRY_V4_WORKFLOW_SUBMIT_INVALID",
        "stub_or_fallback_workflow_detected": True,
        "fallback_workflow_allowed": False
    }
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    # Create shot01 workflow with KSampler and SaveImage (needs > 2 nodes)
    shot01_workflow = {
        "3": {"class_type": "KSampler", "inputs": {}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {}},
        "9": {"class_type": "SaveImage", "inputs": {}}
    }
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(shot01_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_review_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    review = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").read_text())
    assert review["real_workflow_source_candidate_identified"] == True
    assert review["real_workflow_candidate_is_not_stub"] == True
    assert review["has_ksampler"] == True
    assert review["has_saveimage"] == True


def test_review_workflow_binding_no_generation_performed(temp_project_root):
    """Test workflow binding review does not perform generation."""
    control_dir = temp_project_root / "output" / "control"
    
    diagnosis = {"v4_workflow_diagnosis_executed": True}
    (control_dir / "combine_v2_corrective_retry_v4_workflow_diagnosis.json").write_text(
        json.dumps(diagnosis)
    )
    
    shot01_workflow = {"3": {"class_type": "KSampler", "inputs": {}}}
    (control_dir / "ep01_shot01_submitted_workflow.json").write_text(json.dumps(shot01_workflow))
    
    args = MagicMock(
        project_root=str(temp_project_root),
        shot_id="shot02",
        json=True
    )
    
    with patch('sys.stdout', new_callable=MagicMock):
        result = combine_review_corrective_retry_v4_real_workflow_binding(args)
    
    assert result == 0
    
    review = json.loads((control_dir / "combine_v2_corrective_retry_v4_real_workflow_binding_review.json").read_text())
    assert review["new_generation_performed"] == False
    assert review["new_comfyui_submit_executed"] == False
    assert review["retry_attempted"] == False
