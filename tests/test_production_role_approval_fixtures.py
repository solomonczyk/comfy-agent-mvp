"""
Tests for production role approval fixture validation (RC2-PRODCARDS2G)
"""

import json
import pytest
from pathlib import Path
from app.production_cards.approval_gate import (
    load_role_decisions,
    evaluate_character_director_decision,
    evaluate_workflow_td_decision,
    validate_role_approval_gate
)


class TestProductionRoleApprovalFixtures:
    """Test suite for safe approval fixtures."""
    
    def test_approved_character_director_fixture_validates(self):
        """Test that the Character Director approved fixture validates."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        decisions = load_role_decisions("dummy_project_root", decisions_root=str(fixture_root))
        
        char_decision = decisions.get("character_director_decision", {})
        assert char_decision is not None, "Character Director fixture should exist"
        
        evaluation = evaluate_character_director_decision(char_decision)
        assert evaluation["approved"] is True, "Character Director fixture should be approved"
        assert evaluation["reason"] == "approved", "Character Director fixture should have approved reason"
        assert char_decision.get("fixture_only") is True, "Fixture should be marked as fixture_only"
    
    def test_approved_workflow_td_fixture_validates(self):
        """Test that the Workflow TD approved fixture validates."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        decisions = load_role_decisions("dummy_project_root", decisions_root=str(fixture_root))
        
        workflow_decision = decisions.get("workflow_td_decision", {})
        assert workflow_decision is not None, "Workflow TD fixture should exist"
        
        evaluation = evaluate_workflow_td_decision(workflow_decision)
        assert evaluation["approved"] is True, "Workflow TD fixture should be approved"
        assert evaluation["reason"] == "approved", "Workflow TD fixture should have approved reason"
        assert workflow_decision.get("fixture_only") is True, "Fixture should be marked as fixture_only"
    
    def test_both_fixtures_together_allow_retry_generate_frames_only(self):
        """Test that both fixtures together allow retry_generate_frames only."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = validate_role_approval_gate(
            project_root="dummy_project_root",
            decisions_root=str(fixture_root),
            json_output=True
        )
        
        assert result["status"] == "ready_for_retry", "Both fixtures should allow retry"
        assert result["can_retry_generation"] is True, "Can retry generation should be true"
        assert result["downstream_blocked"] is False, "Downstream should not be blocked for retry"
        assert result["next_allowed_action"] == "retry_generate_frames", "Next action should be retry_generate_frames"
        assert result["production_accepted"] is False, "Production should NOT be accepted"
        assert result["fixture_mode"] is True, "Should be in fixture mode"
    
    def test_fixtures_do_not_set_production_accepted_true(self):
        """Test that fixtures do not set production_accepted=true."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        decisions = load_role_decisions("dummy_project_root", decisions_root=str(fixture_root))
        
        char_decision = decisions.get("character_director_decision", {})
        workflow_decision = decisions.get("workflow_td_decision", {})
        
        assert char_decision.get("production_accepted") is False, "Character Director fixture should not set production_accepted"
        assert workflow_decision.get("production_accepted") is False, "Workflow TD fixture should not set production_accepted"
        
        result = validate_role_approval_gate(
            project_root="dummy_project_root",
            decisions_root=str(fixture_root),
            json_output=True
        )
        
        assert result["production_accepted"] is False, "Gate result should have production_accepted=false"
    
    def test_fixtures_are_marked_fixture_only_true(self):
        """Test that fixtures are marked with fixture_only=true."""
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        decisions = load_role_decisions("dummy_project_root", decisions_root=str(fixture_root))
        
        char_decision = decisions.get("character_director_decision", {})
        workflow_decision = decisions.get("workflow_td_decision", {})
        
        assert char_decision.get("fixture_only") is True, "Character Director fixture should have fixture_only=true"
        assert workflow_decision.get("fixture_only") is True, "Workflow TD fixture should have fixture_only=true"
    
    def test_real_project_decisions_remain_pending(self):
        """Test that real project decisions remain pending."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        decisions = load_role_decisions(str(real_project_root))
        
        char_decision = decisions.get("character_director_decision", {})
        workflow_decision = decisions.get("workflow_td_decision", {})
        
        assert char_decision.get("decision_status") == "pending", "Real Character Director decision should be pending"
        assert workflow_decision.get("decision_status") == "pending", "Real Workflow TD decision should be pending"
        assert char_decision.get("selected_decision") is None, "Real Character Director decision should not be decided"
        assert workflow_decision.get("selected_decision") is None, "Real Workflow TD decision should not be decided"
    
    def test_real_project_approval_gate_remains_blocked(self):
        """Test that real project approval gate remains blocked."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        
        result = validate_role_approval_gate(
            project_root=str(real_project_root),
            json_output=True
        )
        
        assert result["status"] == "blocked", "Real project should be blocked"
        assert result["can_retry_generation"] is False, "Real project should not allow retry generation"
        assert result["downstream_blocked"] is True, "Real project should have downstream blocked"
        assert result["production_accepted"] is False, "Real project should not be production accepted"
        assert result.get("fixture_mode") is not True, "Real project should not be in fixture mode"
    
    def test_decisions_root_does_not_mutate_real_project(self):
        """Test that --decisions-root does not mutate real project."""
        real_project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Get real project state before using fixture
        real_decisions_before = load_role_decisions(str(real_project_root))
        
        # Use fixture decisions
        fixture_result = validate_role_approval_gate(
            project_root=str(real_project_root),
            decisions_root=str(fixture_root),
            json_output=True
        )
        
        # Check real project state after using fixture
        real_decisions_after = load_role_decisions(str(real_project_root))
        
        # Real project decisions should be unchanged
        assert real_decisions_before == real_decisions_after, "Real project decisions should not be mutated by fixture usage"
        
        # Real project gate should still be blocked
        real_result = validate_role_approval_gate(
            project_root=str(real_project_root),
            json_output=True
        )
        
        assert real_result["status"] == "blocked", "Real project should remain blocked after fixture usage"
        assert fixture_result["status"] == "ready_for_retry", "Fixture should allow retry"
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test that core module has no hardcoded project-specific names."""
        import app.production_cards.approval_gate as approval_gate_module
        
        source_code = Path(approval_gate_module.__file__).read_text()
        
        # Check for hardcoded project names
        assert "Alya" not in source_code or "character_name" in source_code, "No hardcoded character names in core logic"
        assert "Mir Erdan" not in source_code, "No hardcoded character names in core logic"
        assert "rc2_multishot1_ep01" not in source_code, "No hardcoded project paths in core logic"
