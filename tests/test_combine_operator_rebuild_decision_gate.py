"""Test RC-COMBINE-V2-421-520 Operator Rebuild Decision Gate."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.cli import combine_operator_rebuild_decision
from app.orchestrator import CombineOrchestrator


class TestCombineOperatorRebuildDecisionGate:
    """Test operator rebuild decision gate functionality."""
    
    @pytest.fixture
    def temp_project_root(self):
        """Create a temporary project root for testing."""
        temp_dir = tempfile.mkdtemp()
        project_root = Path(temp_dir)
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        yield project_root
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def mock_args(self, temp_project_root):
        """Create mock CLI arguments."""
        class MockArgs:
            def __init__(self, decision="approve_rebuild_implementation", reason="test"):
                self.project_root = str(temp_project_root)
                self.decision = decision
                self.reason = reason
                self.json = False
        return MockArgs()
    
    def test_approve_rebuild_implementation(self, temp_project_root, mock_args):
        """Test approve_rebuild_implementation decision."""
        mock_args.decision = "approve_rebuild_implementation"
        mock_args.reason = "operator_approved_workflow_recipe_rebuild_after_production_brain_audit"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        # Check decision artifact was created
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        assert decision_path.exists()
        
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_rebuild_decision"] == "approve_rebuild_implementation"
        assert decision_data["workflow_rebuild_implementation_authorized"] is True
        assert decision_data["generation_allowed"] is False
        assert decision_data["comfyui_execution"] is False
        assert decision_data["workflow_submitted"] is False
        assert decision_data["next_allowed_action"] == "workflow_recipe_implementation_required"
        assert decision_data["production_accepted"] is False
    
    def test_request_rebuild_changes(self, temp_project_root, mock_args):
        """Test request_rebuild_changes decision."""
        mock_args.decision = "request_rebuild_changes"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_rebuild_decision"] == "request_rebuild_changes"
        assert decision_data["workflow_rebuild_implementation_authorized"] is False
        assert decision_data["next_allowed_action"] == "workflow_td_rebuild_required"
    
    def test_manual_review_decision(self, temp_project_root, mock_args):
        """Test manual_review decision."""
        mock_args.decision = "manual_review"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_rebuild_decision"] == "manual_review"
        assert decision_data["workflow_rebuild_implementation_authorized"] is False
        assert decision_data["next_allowed_action"] == "operator_rebuild_approval_required"
    
    def test_abort_route_decision(self, temp_project_root, mock_args):
        """Test abort_route decision."""
        mock_args.decision = "abort_route"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_rebuild_decision"] == "abort_route"
        assert decision_data["workflow_rebuild_implementation_authorized"] is False
        assert decision_data["next_allowed_action"] == "blocked_generation_route_aborted"
    
    def test_json_output(self, temp_project_root, mock_args, capsys):
        """Test JSON output format."""
        mock_args.json = True
        mock_args.decision = "approve_rebuild_implementation"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        captured = capsys.readouterr()
        output_data = json.loads(captured.out)
        
        assert output_data["operator_rebuild_decision"] == "approve_rebuild_implementation"
        assert output_data["workflow_rebuild_implementation_authorized"] is True
    
    def test_invalid_decision(self, temp_project_root, mock_args):
        """Test handling of invalid decision."""
        mock_args.decision = "invalid_decision"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 1
    
    def test_hard_boundaries_enforced(self, temp_project_root, mock_args):
        """Test that hard boundaries are enforced."""
        mock_args.decision = "approve_rebuild_implementation"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        # Verify hard boundaries
        assert decision_data["generation_allowed"] is False
        assert decision_data["comfyui_execution"] is False
        assert decision_data["workflow_submitted"] is False
        assert decision_data["production_accepted"] is False
    
    def test_reason_preserved(self, temp_project_root, mock_args):
        """Test that decision reason is preserved."""
        test_reason = "operator_approved_workflow_recipe_rebuild_after_production_brain_audit"
        mock_args.reason = test_reason
        mock_args.decision = "approve_rebuild_implementation"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_rebuild_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["reason"] == test_reason
    
    def test_state_transition_on_approval(self, temp_project_root, mock_args):
        """Test that state transitions to operator_rebuild_approved on approval."""
        mock_args.decision = "approve_rebuild_implementation"
        
        result = combine_operator_rebuild_decision(mock_args)
        
        assert result == 0
        
        # Check artifact index was updated
        artifact_index_path = temp_project_root / "output" / "control" / "artifact_index.json"
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        assert artifact_index["current_state"] == "operator_rebuild_approved"
