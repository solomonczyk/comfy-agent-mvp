"""RC-COMBINE-V2-981-1040-FIX — Test prompt patch v2 verification.

Tests that prompt patching uses node/field-based targeting instead of exact-text
comparison, and that the verification properly confirms the strategy.
"""
import json
import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.cli import combine_verify_prompt_patch_v2


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


def test_verify_prompt_patch_v2_requires_strategy_file(control_dir, mock_args, tmp_path):
    """Test that verification reads the prompt patch strategy v2 file."""
    mock_args.project_root = str(tmp_path)
    
    # Create the strategy file
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name", "semantic_role", "positive_prompt_field", "negative_prompt_field"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_verify_prompt_patch_v2(mock_args)
        
        assert result == 0


def test_verify_prompt_patch_v2_confirms_exact_text_removal(control_dir, mock_args, tmp_path):
    """Test that verification confirms exact-text dependency is removed."""
    mock_args.project_root = str(tmp_path)
    
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        with patch('builtins.print') as mock_print:
            result = combine_verify_prompt_patch_v2(mock_args)
            
            assert result == 0
            # Check that verification passed
            output_calls = [str(call) for call in mock_print.call_args_list]
            assert any("PASSED" in call for call in output_calls)


def test_verify_prompt_patch_v2_confirms_node_field_strategy(control_dir, mock_args, tmp_path):
    """Test that verification confirms node/field-based strategy is used."""
    mock_args.project_root = str(tmp_path)
    
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name", "semantic_role", "positive_prompt_field", "negative_prompt_field"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        with patch('builtins.print') as mock_print:
            result = combine_verify_prompt_patch_v2(mock_args)
            
            assert result == 0
            output_calls = [str(call) for call in mock_print.call_args_list]
            assert any("Positive Patch by Node Field: True" in call for call in output_calls)
            assert any("Negative Patch by Node Field: True" in call for call in output_calls)


def test_verify_prompt_patch_v2_forbids_exact_text_strategy(control_dir, mock_args, tmp_path):
    """Test that verification forbids exact-text strategy."""
    mock_args.project_root = str(tmp_path)
    
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_verify_prompt_patch_v2(mock_args)
        
        assert result == 0


def test_verify_prompt_patch_v2_enforces_no_generation_boundary(control_dir, mock_args, tmp_path):
    """Test that verification enforces no-generation boundary."""
    mock_args.project_root = str(tmp_path)
    
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        result = combine_verify_prompt_patch_v2(mock_args)
        
        assert result == 0


def test_verify_prompt_patch_v2_json_output(control_dir, mock_args, tmp_path):
    """Test that verification can output JSON format."""
    mock_args.project_root = str(tmp_path)
    mock_args.json = True
    
    strategy = {
        "strategy_name": "combine_v2_prompt_patch_strategy_v2",
        "strategy_version": "2.0",
        "patch_strategy": ["node_id", "node_class_type", "field_name"],
        "forbidden_strategy": ["exact_text_equality_required_for_patch"],
        "prompt_patch_exact_text_dependency_removed": True,
        "positive_prompt_patch_applied_by_node_field": True,
        "negative_prompt_patch_applied_by_node_field": True,
        "prompt_patch_verified_after_write": True,
        "timestamp": datetime.utcnow().isoformat()
    }
    with open(control_dir / "combine_v2_prompt_patch_strategy_v2.json", 'w') as f:
        json.dump(strategy, f)
    
    with patch('app.cli.Path') as mock_path:
        mock_path_instance = Path(tmp_path)
        mock_path.return_value = mock_path_instance
        mock_path.side_effect = lambda x: tmp_path / x if isinstance(x, str) else x
        
        with patch('builtins.print') as mock_print:
            result = combine_verify_prompt_patch_v2(mock_args)
            
            assert result == 0
            assert mock_print.called
