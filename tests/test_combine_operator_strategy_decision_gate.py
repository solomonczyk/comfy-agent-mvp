"""Test RC-COMBINE-V2-331-420 Operator Strategy Decision Gate."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.cli import combine_operator_strategy_decision
from app.orchestrator import CombineOrchestrator


class TestCombineOperatorStrategyDecisionGate:
    """Test operator strategy decision gate functionality."""
    
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
            def __init__(self, decision="approve_workflow_rebuild_plan", reason="test"):
                self.project_root = str(temp_project_root)
                self.decision = decision
                self.reason = reason
                self.json = False
        return MockArgs()
    
    def test_approve_workflow_rebuild_plan(self, temp_project_root, mock_args):
        """Test approve_workflow_rebuild_plan decision."""
        mock_args.decision = "approve_workflow_rebuild_plan"
        mock_args.reason = "production_brain_requires_workflow_recipe_rebuild_before_next_generation"
        
        with patch('app.orchestrator.CombineOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator_class.return_value = mock_orchestrator
            
            result = combine_operator_strategy_decision(mock_args)
            
            assert result == 0
            
            # Check decision artifact was created
            decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
            assert decision_path.exists()
            
            with open(decision_path, 'r') as f:
                decision_data = json.load(f)
            
            assert decision_data["operator_strategy_decision"] == "approve_workflow_rebuild_plan"
            assert decision_data["workflow_rebuild_authorized"] is True
            assert decision_data["generation_allowed"] is False
            assert decision_data["retry_allowed"] is False
            assert decision_data["next_allowed_action"] == "workflow_td_rebuild_required"
            assert decision_data["production_accepted"] is False
            
            # Check orchestrator was called to transition state
            mock_orchestrator.transition_to.assert_called_once_with("workflow_td_rebuild_required")
    
    def test_request_recipe_audit_changes(self, temp_project_root, mock_args):
        """Test request_recipe_audit_changes decision."""
        mock_args.decision = "request_recipe_audit_changes"
        
        result = combine_operator_strategy_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_strategy_decision"] == "request_recipe_audit_changes"
        assert decision_data["workflow_rebuild_authorized"] is False
        assert decision_data["next_allowed_action"] == "generation_recipe_audit_required"
    
    def test_manual_review_decision(self, temp_project_root, mock_args):
        """Test manual_review decision."""
        mock_args.decision = "manual_review"
        
        result = combine_operator_strategy_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_strategy_decision"] == "manual_review"
        assert decision_data["workflow_rebuild_authorized"] is False
        assert decision_data["next_allowed_action"] == "operator_strategy_review"
    
    def test_abort_route_decision(self, temp_project_root, mock_args):
        """Test abort_route decision."""
        mock_args.decision = "abort_route"
        
        result = combine_operator_strategy_decision(mock_args)
        
        assert result == 0
        
        decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
        with open(decision_path, 'r') as f:
            decision_data = json.load(f)
        
        assert decision_data["operator_strategy_decision"] == "abort_route"
        assert decision_data["workflow_rebuild_authorized"] is False
        assert decision_data["next_allowed_action"] == "blocked_generation_route_aborted"
    
    def test_json_output(self, temp_project_root, mock_args, capsys):
        """Test JSON output format."""
        mock_args.json = True
        mock_args.decision = "approve_workflow_rebuild_plan"
        
        with patch('app.orchestrator.CombineOrchestrator'):
            result = combine_operator_strategy_decision(mock_args)
            
            assert result == 0
            
            captured = capsys.readouterr()
            output_data = json.loads(captured.out)
            
            assert output_data["operator_strategy_decision"] == "approve_workflow_rebuild_plan"
            assert output_data["workflow_rebuild_authorized"] is True
    
    def test_orchestrator_transition_failure(self, temp_project_root, mock_args):
        """Test handling of orchestrator transition failure."""
        mock_args.decision = "approve_workflow_rebuild_plan"
        
        with patch('app.orchestrator.CombineOrchestrator') as mock_orchestrator_class:
            mock_orchestrator = MagicMock()
            mock_orchestrator.transition_to.side_effect = Exception("Transition failed")
            mock_orchestrator_class.return_value = mock_orchestrator
            
            result = combine_operator_strategy_decision(mock_args)
            
            assert result == 1
    
    def test_invalid_decision(self, temp_project_root, mock_args):
        """Test handling of invalid decision."""
        mock_args.decision = "invalid_decision"
        
        result = combine_operator_strategy_decision(mock_args)
        
        assert result == 1
    
    def test_hard_boundaries_enforced(self, temp_project_root, mock_args):
        """Test that hard boundaries are enforced."""
        mock_args.decision = "approve_workflow_rebuild_plan"
        
        with patch('app.orchestrator.CombineOrchestrator'):
            result = combine_operator_strategy_decision(mock_args)
            
            assert result == 0
            
            decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
            with open(decision_path, 'r') as f:
                decision_data = json.load(f)
            
            # Verify hard boundaries
            assert decision_data["generation_allowed"] is False
            assert decision_data["retry_allowed"] is False
            assert decision_data["production_accepted"] is False
    
    def test_reason_preserved(self, temp_project_root, mock_args):
        """Test that decision reason is preserved."""
        test_reason = "production_brain_requires_workflow_recipe_rebuild_before_next_generation"
        mock_args.reason = test_reason
        mock_args.decision = "approve_workflow_rebuild_plan"
        
        with patch('app.orchestrator.CombineOrchestrator'):
            result = combine_operator_strategy_decision(mock_args)
            
            assert result == 0
            
            decision_path = temp_project_root / "output" / "control" / "combine_v2_operator_strategy_decision.json"
            with open(decision_path, 'r') as f:
                decision_data = json.load(f)
            
            assert decision_data["reason"] == test_reason
