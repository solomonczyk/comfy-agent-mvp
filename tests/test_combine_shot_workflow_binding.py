"""RC-COMBINE-V2-981-1040-FIX — Test shot-specific workflow binding guard.

Tests that the workflow binding guard properly blocks cross-shot workflow reuse
and enforces shot-specific workflow binding.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch, MagicMock
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import combine_validate_shot_workflow_binding


@pytest.fixture
def mock_args():
    """Create mock argparse.Namespace for testing."""
    from argparse import Namespace
    return Namespace(
        project_root="f:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01",
        shot_id="shot02",
        json=False
    )


@pytest.fixture
def control_dir(tmp_path):
    """Create a temporary control directory for testing."""
    control = tmp_path / "output" / "control"
    control.mkdir(parents=True, exist_ok=True)
    return control


def test_validate_shot_workflow_binding_creates_policy(control_dir, mock_args, tmp_path):
    """Test that validation creates the workflow binding policy."""
    mock_args.project_root = str(tmp_path)
    
    with patch('app.cli.Path') as mock_path:
        mock_path.return_value = tmp_path
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_validate_shot_workflow_binding(mock_args)
        
        assert result == 0
        
        policy_path = control_dir / "combine_v2_shot_workflow_binding_policy.json"
        assert policy_path.exists()
        
        with open(policy_path, 'r') as f:
            policy = json.load(f)
        
        assert policy["policy_name"] == "combine_v2_shot_workflow_binding_policy"
        assert policy["policy_version"] == "2.0"
        assert policy["require_matching_shot_id"] is True
        assert policy["allow_cross_shot_reuse"] is False
        assert policy["allow_fallback_minimal_workflow"] is False
        assert policy["on_mismatch"] == "block_and_request_shot_specific_workflow"


def test_validate_shot_workflow_binding_detects_cross_shot_reuse(control_dir, mock_args, tmp_path):
    """Test that validation detects cross-shot workflow reuse."""
    mock_args.project_root = str(tmp_path)
    
    # Create a workflow file for shot01
    shot01_workflow = {
        "3": {"class_type": "KSampler", "inputs": {}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {}}
    }
    with open(control_dir / "ep01_shot01_submitted_workflow.json", 'w') as f:
        json.dump(shot01_workflow, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_validate_shot_workflow_binding(mock_args)
        
        assert result == 0
        
        guard_report_path = control_dir / "combine_v2_cross_shot_reuse_guard_report.json"
        assert guard_report_path.exists()
        
        with open(guard_report_path, 'r') as f:
            report = json.load(f)
        
        assert report["requested_shot_id"] == "shot02"
        assert report["workflow_shot_id"] == "ep01_shot01"
        assert report["cross_shot_workflow_reuse_detected"] is True
        assert report["cross_shot_workflow_reuse_blocked"] is True
        assert report["validation_result"] == "blocked"


def test_validate_shot_workflow_binding_blocks_fallback_minimal_workflow(control_dir, mock_args, tmp_path):
    """Test that validation blocks fallback minimal workflow."""
    mock_args.project_root = str(tmp_path)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_validate_shot_workflow_binding(mock_args)
        
        assert result == 0
        
        guard_report_path = control_dir / "combine_v2_cross_shot_reuse_guard_report.json"
        with open(guard_report_path, 'r') as f:
            report = json.load(f)
        
        assert report["fallback_minimal_workflow_forbidden"] is True
        assert report["silent_cross_shot_reuse_allowed"] is False


def test_validate_shot_workflow_binding_forbids_generation(control_dir, mock_args, tmp_path):
    """Test that validation enforces no-generation boundary."""
    mock_args.project_root = str(tmp_path)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_validate_shot_workflow_binding(mock_args)
        
        assert result == 0
        
        guard_report_path = control_dir / "combine_v2_cross_shot_reuse_guard_report.json"
        with open(guard_report_path, 'r') as f:
            report = json.load(f)
        
        assert report["generation_allowed"] is False
        assert report["retry_allowed"] is False
        assert report["workflow_submitted"] is False
        assert report["comfyui_execution"] is False


def test_validate_shot_workflow_binding_json_output(control_dir, mock_args, tmp_path):
    """Test that validation can output JSON format."""
    mock_args.project_root = str(tmp_path)
    mock_args.json = True
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        with patch('builtins.print') as mock_print:
            result = combine_validate_shot_workflow_binding(mock_args)
            
            assert result == 0
            # Check that print was called with JSON output
            assert mock_print.called
