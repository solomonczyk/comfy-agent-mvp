"""Test RC-COMBINE-V2-331-420 Production Brain Rerun Guard."""

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from app.agents.production_brain_agent import ProductionBrainAgent
from app.orchestrator.contracts import CombineRunContext


class TestCombineProductionBrainRerunGuard:
    """Test production brain rerun guard functionality."""
    
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
    def agent(self):
        """Create production brain agent."""
        return ProductionBrainAgent()
    
    def test_audit_guard_allowed_states(self, agent, temp_project_root):
        """Test that audit guard allows specified states."""
        allowed_states = [
            "real_visual_qa_preflight_required",
            "production_brain_audit_required",
            "operator_strategy_review"
        ]
        
        for stage in allowed_states:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            
            result = agent.run(context)
            
            # Should not be blocked by audit guard
            assert result.status != "blocked"
            assert result.metadata.get("error") != "audit_guard_failed"
    
    def test_audit_guard_blocks_disallowed_states(self, agent, temp_project_root):
        """Test that audit guard blocks disallowed states."""
        disallowed_states = [
            "workflow_td_rebuild_required",
            "recipe_rebuild_contract_required",
            "prompt_contract_rebuild_required", 
            "quality_pipeline_contract_required",
            "workflow_rebuild_preflight_required",
            "operator_rebuild_approval_required",
            "generate_assets",
            "assembly_required"
        ]
        
        for stage in disallowed_states:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            
            result = agent.run(context)
            
            # Should be blocked by audit guard
            assert result.status == "blocked"
            assert result.metadata["error"] == "audit_guard_failed"
            assert result.metadata["reason"] == "production_brain_rerun_cannot_rewind_from_later_state"
    
    def test_audit_guard_structure(self, agent, temp_project_root):
        """Test audit guard return structure."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="production_brain_audit_required",
            stage="production_brain_audit_required",
            dry_run=True
        )
        
        # Call the audit guard method directly
        audit_guard = agent._check_audit_guard(str(temp_project_root), "production_brain_audit_required")
        
        assert "idempotent_rerun_safe" in audit_guard
        assert "production_brain_rerun_cannot_rewind_from_later_state" in audit_guard
        assert "state_reset_allowed_only_when_current_state_in" in audit_guard
        assert "current_stage" in audit_guard
        
        assert audit_guard["idempotent_rerun_safe"] is True
        assert audit_guard["production_brain_rerun_cannot_rewind_from_later_state"] is True
        assert "production_brain_audit_required" in audit_guard["state_reset_allowed_only_when_current_state_in"]
        assert audit_guard["current_stage"] == "production_brain_audit_required"
    
    def test_production_brain_rerun_cannot_rewind_later_state(self, agent, temp_project_root):
        """Test that production brain rerun cannot rewind from later state."""
        # Test with a later state that should be blocked
        later_stage = "workflow_td_rebuild_required"
        
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state=later_stage,
            stage=later_stage,
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "blocked"
        assert result.metadata["reason"] == "production_brain_rerun_cannot_rewind_from_later_state"
        
        # Check audit guard details
        audit_guard = result.metadata["audit_guard"]
        assert audit_guard["idempotent_rerun_safe"] is False
        assert audit_guard["production_brain_rerun_cannot_rewind_from_later_state"] is False
        assert audit_guard["current_stage"] == later_stage
    
    def test_idempotent_rerun_safe_flag(self, agent, temp_project_root):
        """Test idempotent_rerun_safe flag behavior."""
        # Test allowed state
        allowed_stage = "production_brain_audit_required"
        audit_guard = agent._check_audit_guard(str(temp_project_root), allowed_stage)
        assert audit_guard["idempotent_rerun_safe"] is True
        
        # Test disallowed state
        disallowed_stage = "workflow_td_rebuild_required"
        audit_guard = agent._check_audit_guard(str(temp_project_root), disallowed_stage)
        assert audit_guard["idempotent_rerun_safe"] is False
    
    def test_state_reset_allowed_only_when_current_state_in(self, agent, temp_project_root):
        """Test state reset allowed only when current state in specified list."""
        audit_guard = agent._check_audit_guard(str(temp_project_root), "production_brain_audit_required")
        
        allowed_states = audit_guard["state_reset_allowed_only_when_current_state_in"]
        expected_states = [
            "real_visual_qa_preflight_required",
            "production_brain_audit_required",
            "operator_strategy_review"
        ]
        
        assert allowed_states == expected_states
    
    def test_audit_guard_prevents_bypassing_workflow_rebuild(self, agent, temp_project_root):
        """Test that audit guard prevents bypassing workflow rebuild."""
        # Try to run production brain from a state that should require workflow rebuild
        rebuild_states = [
            "workflow_td_rebuild_required",
            "recipe_rebuild_contract_required",
            "prompt_contract_rebuild_required",
            "quality_pipeline_contract_required",
            "workflow_rebuild_preflight_required",
            "operator_rebuild_approval_required"
        ]
        
        for stage in rebuild_states:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            
            result = agent.run(context)
            
            # Should be blocked to prevent bypassing workflow rebuild
            assert result.status == "blocked"
            assert result.metadata["error"] == "audit_guard_failed"
    
    def test_audit_guard_allows_early_stage_rerun(self, agent, temp_project_root):
        """Test that audit guard allows rerun from early stages."""
        early_stages = [
            "real_visual_qa_preflight_required",
            "production_brain_audit_required",
            "operator_strategy_review"
        ]
        
        for stage in early_stages:
            context = CombineRunContext(
                project_root=str(temp_project_root),
                current_state=stage,
                stage=stage,
                dry_run=True
            )
            
            result = agent.run(context)
            
            # Should not be blocked
            assert result.status != "blocked"
            assert result.metadata.get("error") != "audit_guard_failed"
    
    def test_audit_guard_with_real_visual_qa_preflight(self, agent, temp_project_root):
        """Test audit guard with real_visual_qa_preflight_required stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="real_visual_qa_preflight_required",
            stage="real_visual_qa_preflight_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        # Should not be blocked
        assert result.status != "blocked"
        assert result.metadata.get("error") != "audit_guard_failed"
        
        # Should proceed to visual failure audit (or be stubbed if dry-run)
        if result.status == "ok":
            assert result.next_recommended_stage == "visual_failure_audit_required"
    
    def test_audit_guard_with_operator_strategy_review(self, agent, temp_project_root):
        """Test audit guard with operator_strategy_review stage."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="operator_strategy_review",
            stage="operator_strategy_review",
            dry_run=True
        )
        
        result = agent.run(context)
        
        # Should not be blocked
        assert result.status != "blocked"
        assert result.metadata.get("error") != "audit_guard_failed"
    
    def test_audit_guard_error_metadata(self, agent, temp_project_root):
        """Test audit guard error metadata structure."""
        context = CombineRunContext(
            project_root=str(temp_project_root),
            current_state="workflow_td_rebuild_required",  # This should be blocked
            stage="workflow_td_rebuild_required",
            dry_run=True
        )
        
        result = agent.run(context)
        
        assert result.status == "blocked"
        assert result.metadata["error"] == "audit_guard_failed"
        assert result.metadata["reason"] == "production_brain_rerun_cannot_rewind_from_later_state"
        assert "audit_guard" in result.metadata
        
        audit_guard = result.metadata["audit_guard"]
        assert audit_guard["idempotent_rerun_safe"] is False
        assert audit_guard["production_brain_rerun_cannot_rewind_from_later_state"] is False
        assert audit_guard["current_stage"] == "workflow_td_rebuild_required"
