"""RC-COMBINE-V2-981-1040-FIX — Test corrective retry package v2.

Tests that the corrective retry package v2 enforces shot-specific workflow binding,
removes exact-text prompt patching dependency, and forbids generation/retry.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import combine_build_corrective_retry_package_v2


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


def test_build_corrective_retry_package_v2_requires_plan(control_dir, mock_args, tmp_path):
    """Test that package v2 requires corrective retry plan."""
    mock_args.project_root = str(tmp_path)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        # Should fail because plan doesn't exist
        assert result == 1


def test_build_corrective_retry_package_v2_creates_strategy(control_dir, mock_args, tmp_path):
    """Test that package v2 creates prompt patch strategy v2."""
    mock_args.project_root = str(tmp_path)
    
    # Create the required plan file
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        strategy_path = control_dir / "combine_v2_prompt_patch_strategy_v2.json"
        assert strategy_path.exists()
        
        with open(strategy_path, 'r') as f:
            strategy = json.load(f)
        
        assert strategy["strategy_name"] == "combine_v2_prompt_patch_strategy_v2"
        assert strategy["strategy_version"] == "2.0"
        assert "node_id" in strategy["patch_strategy"]
        assert "node_class_type" in strategy["patch_strategy"]
        assert "field_name" in strategy["patch_strategy"]
        assert "exact_text_equality_required_for_patch" in strategy["forbidden_strategy"]
        assert strategy["prompt_patch_exact_text_dependency_removed"] is True


def test_build_corrective_retry_package_v2_enforces_shot_binding(control_dir, mock_args, tmp_path):
    """Test that package v2 enforces shot-specific workflow binding."""
    mock_args.project_root = str(tmp_path)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        assert package["package_type"] == "corrective_retry_package_v2"
        assert package["package_version"] == "2.0"
        assert package["shot_id"] == "shot02"
        assert package["shot_specific_workflow_binding_required"] is True
        assert package["cross_shot_workflow_reuse_blocked"] is True
        assert package["fallback_minimal_workflow_forbidden"] is True


def test_build_corrective_retry_package_v2_removes_exact_text_dependency(control_dir, mock_args, tmp_path):
    """Test that package v2 removes exact-text prompt patching dependency."""
    mock_args.project_root = str(tmp_path)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        assert package["prompt_patch_exact_text_dependency_removed"] is True
        assert package["prompt_patch_verification_required"] is True


def test_build_corrective_retry_package_v2_forbids_generation(control_dir, mock_args, tmp_path):
    """Test that package v2 forbids generation and retry."""
    mock_args.project_root = str(tmp_path)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        package_path = control_dir / "combine_v2_corrective_retry_package_v2.json"
        with open(package_path, 'r') as f:
            package = json.load(f)
        
        assert package["generation_allowed"] is False
        assert package["retry_allowed"] is False
        assert package["workflow_submitted"] is False
        assert package["comfyui_execution"] is False
        assert package["production_accepted"] is False


def test_build_corrective_retry_package_v2_creates_preflight_report(control_dir, mock_args, tmp_path):
    """Test that package v2 creates preflight report."""
    mock_args.project_root = str(tmp_path)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        preflight_path = control_dir / "combine_v2_corrective_retry_v2_preflight_report.json"
        assert preflight_path.exists()
        
        with open(preflight_path, 'r') as f:
            preflight = json.load(f)
        
        assert preflight["stage"] == "corrective_retry_v2_preflight"
        assert preflight["package_type"] == "corrective_retry_package_v2"
        assert preflight["shot_id"] == "shot02"
        assert preflight["preflight_status"] == "ready_for_operator_authorization"


def test_build_corrective_retry_package_v2_creates_auth_request(control_dir, mock_args, tmp_path):
    """Test that package v2 creates operator authorization request v2."""
    mock_args.project_root = str(tmp_path)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        auth_request_path = control_dir / "combine_v2_operator_retry_generation_authorization_request_v2.json"
        assert auth_request_path.exists()
        
        with open(auth_request_path, 'r') as f:
            auth_request = json.load(f)
        
        assert auth_request["stage"] == "operator_retry_generation_authorization_required"
        assert auth_request["request_type"] == "operator_retry_generation_authorization_request_v2"
        assert auth_request["shot_id"] == "shot02"
        assert auth_request["next_allowed_action"] == "operator_retry_generation_authorization_required"


def test_build_corrective_retry_package_v2_updates_artifact_index(control_dir, mock_args, tmp_path):
    """Test that package v2 updates artifact index."""
    mock_args.project_root = str(tmp_path)
    
    # Create artifact index
    idx = {"existing_key": "value"}
    with open(control_dir / "artifact_index.json", 'w') as f:
        json.dump(idx, f)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_idx = json.load(f)
        
        assert updated_idx["corrective_retry_package_v2_created"] is True
        assert updated_idx["shot_workflow_binding_policy_created"] is True
        assert updated_idx["prompt_patch_strategy_v2_created"] is True


def test_build_corrective_retry_package_v2_updates_episode_ledger(control_dir, mock_args, tmp_path):
    """Test that package v2 updates episode ledger."""
    mock_args.project_root = str(tmp_path)
    
    # Create episode ledger
    ledger = {"events": []}
    with open(control_dir / "episode_ledger.json", 'w') as f:
        json.dump(ledger, f)
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_build_corrective_retry_package_v2(mock_args)
        
        assert result == 0
        
        with open(control_dir / "episode_ledger.json", 'r') as f:
            updated_ledger = json.load(f)
        
        assert len(updated_ledger["events"]) > 0
        latest_event = updated_ledger["events"][-1]
        assert latest_event["event_type"] == "corrective_retry_package_v2_created"
        assert latest_event["shot_id"] == "shot02"
        assert latest_event["package_type"] == "corrective_retry_package_v2"


def test_build_corrective_retry_package_v2_json_output(control_dir, mock_args, tmp_path):
    """Test that package v2 can output JSON format."""
    mock_args.project_root = str(tmp_path)
    mock_args.json = True
    
    plan = {
        "source_asset": "output/frames/shot01_frame_0001.png",
        "failure_basis": ["subject_not_recognizable"]
    }
    with open(control_dir / "combine_v2_corrective_retry_plan.json", 'w') as f:
        json.dump(plan, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        with patch('builtins.print') as mock_print:
            result = combine_build_corrective_retry_package_v2(mock_args)
            
            assert result == 0
            assert mock_print.called
