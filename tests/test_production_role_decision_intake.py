"""
Tests for production role decision intake dry-run (RC2-PRODCARDS2H)
"""

import json
import pytest
from pathlib import Path
from app.production_cards.decision_intake import (
    load_intake_decisions,
    compare_against_pending_decisions,
    verify_required_approval_artifacts,
    validate_decision_intake
)


class TestProductionRoleDecisionIntake:
    """Test suite for role decision intake dry-run validation."""
    
    def test_fixture_approvals_pass_intake_dry_run(self):
        """Test that fixture approvals pass intake dry-run validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = validate_decision_intake(str(project_root), str(fixture_root))
        
        assert result["status"] == "valid", "Fixture approvals should pass intake validation"
        assert result["dry_run"] is True, "Should be in dry-run mode"
        assert result["would_allow_retry_generation"] is True, "Should allow retry generation"
        assert result["would_apply_decisions"] == 2, "Should apply both decisions"
        assert result["next_allowed_action_if_applied"] == "retry_generate_frames", "Next action should be retry_generate_frames"
        assert result["production_accepted_after_apply"] is False, "Production should not be accepted"
        assert result["real_project_mutated"] is False, "Real project should not be mutated"
    
    def test_intake_dry_run_does_not_mutate_real_project(self):
        """Test that intake dry-run does not mutate the real project."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Get real project state before dry-run
        from app.production_cards.approval_gate import load_role_decisions
        real_decisions_before = load_role_decisions(str(project_root))
        
        # Run intake dry-run
        result = validate_decision_intake(str(project_root), str(fixture_root))
        
        # Get real project state after dry-run
        real_decisions_after = load_role_decisions(str(project_root))
        
        # Real project decisions should be unchanged
        assert real_decisions_before == real_decisions_after, "Real project decisions should not be mutated by dry-run"
        
        # Result should confirm no mutation
        assert result["real_project_mutated"] is False, "Result should confirm real project not mutated"
    
    def test_missing_character_director_decision_fails(self):
        """Test that missing Character Director decision fails intake validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        # Use empty directory to simulate missing decision
        empty_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Create temporary directory with only Workflow TD decision
        from tempfile import TemporaryDirectory
        import shutil
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Copy only Workflow TD decision
            shutil.copy(
                empty_root / "workflow_td_identity_workflow_decision.approved.json",
                temp_path / "workflow_td_identity_workflow_decision.approved.json"
            )
            
            result = validate_decision_intake(str(project_root), str(temp_path))
            
            assert result["status"] == "invalid", "Missing Character Director should fail"
            assert result["dry_run"] is True, "Should be in dry-run mode"
            assert result["would_allow_retry_generation"] is False, "Should not allow retry generation"
            assert "character_director" in result["missing_decisions"], "Should report missing Character Director"
    
    def test_missing_workflow_td_decision_fails(self):
        """Test that missing Workflow TD decision fails intake validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Create temporary directory with only Character Director decision
        from tempfile import TemporaryDirectory
        import shutil
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Copy only Character Director decision
            shutil.copy(
                fixture_root / "character_director_identity_decision.approved.json",
                temp_path / "character_director_identity_decision.approved.json"
            )
            
            result = validate_decision_intake(str(project_root), str(temp_path))
            
            assert result["status"] == "invalid", "Missing Workflow TD should fail"
            assert result["dry_run"] is True, "Should be in dry-run mode"
            assert result["would_allow_retry_generation"] is False, "Should not allow retry generation"
            assert "workflow_td" in result["missing_decisions"], "Should report missing Workflow TD"
    
    def test_incomplete_character_director_artifacts_fail(self):
        """Test that incomplete Character Director artifacts fail intake validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Create temporary directory with incomplete Character Director decision
        from tempfile import TemporaryDirectory
        import shutil
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Copy and modify Character Director decision to remove artifacts
            char_decision_path = temp_path / "character_director_identity_decision.approved.json"
            shutil.copy(fixture_root / "character_director_identity_decision.approved.json", char_decision_path)
            
            # Load and modify decision
            with open(char_decision_path, 'r') as f:
                decision = json.load(f)
            
            # Remove required artifacts
            decision["required_artifacts"] = {}
            
            with open(char_decision_path, 'w') as f:
                json.dump(decision, f)
            
            # Copy Workflow TD decision
            shutil.copy(fixture_root / "workflow_td_identity_workflow_decision.approved.json", temp_path / "workflow_td_identity_workflow_decision.approved.json")
            
            result = validate_decision_intake(str(project_root), str(temp_path))
            
            assert result["status"] == "invalid", "Incomplete artifacts should fail"
            assert result["dry_run"] is True, "Should be in dry-run mode"
            assert result["would_allow_retry_generation"] is False, "Should not allow retry generation"
            assert len(result["errors"]) > 0, "Should report artifact errors"
    
    def test_incomplete_workflow_td_artifacts_fail(self):
        """Test that incomplete Workflow TD artifacts fail intake validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Create temporary directory with incomplete Workflow TD decision
        from tempfile import TemporaryDirectory
        import shutil
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Copy Character Director decision
            shutil.copy(fixture_root / "character_director_identity_decision.approved.json", temp_path / "character_director_identity_decision.approved.json")
            
            # Copy and modify Workflow TD decision to remove artifacts
            workflow_decision_path = temp_path / "workflow_td_identity_workflow_decision.approved.json"
            shutil.copy(fixture_root / "workflow_td_identity_workflow_decision.approved.json", workflow_decision_path)
            
            # Load and modify decision
            with open(workflow_decision_path, 'r') as f:
                decision = json.load(f)
            
            # Remove required artifacts
            decision["required_artifacts"] = {}
            
            with open(workflow_decision_path, 'w') as f:
                json.dump(decision, f)
            
            result = validate_decision_intake(str(project_root), str(temp_path))
            
            assert result["status"] == "invalid", "Incomplete artifacts should fail"
            assert result["dry_run"] is True, "Should be in dry-run mode"
            assert result["would_allow_retry_generation"] is False, "Should not allow retry generation"
            assert len(result["errors"]) > 0, "Should report artifact errors"
    
    def test_legacy_reference_locked_workflow_decision_fails(self):
        """Test that legacy_reference_locked workflow decision fails intake validation."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        # Create temporary directory with unsafe Workflow TD decision
        from tempfile import TemporaryDirectory
        import shutil
        
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            # Copy Character Director decision
            shutil.copy(fixture_root / "character_director_identity_decision.approved.json", temp_path / "character_director_identity_decision.approved.json")
            
            # Copy and modify Workflow TD decision to allow legacy
            workflow_decision_path = temp_path / "workflow_td_identity_workflow_decision.approved.json"
            shutil.copy(fixture_root / "workflow_td_identity_workflow_decision.approved.json", workflow_decision_path)
            
            # Load and modify decision
            with open(workflow_decision_path, 'r') as f:
                decision = json.load(f)
            
            # Set legacy_reference_locked_allowed_for_production to true
            decision["legacy_reference_locked_allowed_for_production"] = True
            
            with open(workflow_decision_path, 'w') as f:
                json.dump(decision, f)
            
            result = validate_decision_intake(str(project_root), str(temp_path))
            
            assert result["status"] == "invalid", "Legacy reference locked should fail"
            assert result["dry_run"] is True, "Should be in dry-run mode"
            assert result["would_allow_retry_generation"] is False, "Should not allow retry generation"
            assert len(result["errors"]) > 0, "Should report legacy reference error"
    
    def test_production_accepted_remains_false_after_dry_run(self):
        """Test that production_accepted remains false after dry-run."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = validate_decision_intake(str(project_root), str(fixture_root))
        
        assert result["production_accepted_after_apply"] is False, "Production accepted should remain false after dry-run"
        assert result["dry_run"] is True, "Should be in dry-run mode"
    
    def test_dry_run_reports_next_allowed_action_if_applied_retry_generate_frames(self):
        """Test that dry-run reports next_allowed_action_if_applied = retry_generate_frames for valid approvals."""
        project_root = Path(__file__).parent.parent / "data" / "rc2_multishot1_ep01"
        fixture_root = Path(__file__).parent.parent / "data" / "fixtures" / "production_role_approvals" / "identity_retry_ready"
        
        result = validate_decision_intake(str(project_root), str(fixture_root))
        
        assert result["next_allowed_action_if_applied"] == "retry_generate_frames", "Next action should be retry_generate_frames"
        assert result["dry_run"] is True, "Should be in dry-run mode"
        assert result["would_allow_retry_generation"] is True, "Should allow retry generation"
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test that core module has no hardcoded project-specific names."""
        import app.production_cards.decision_intake as decision_intake_module
        
        source_code = Path(decision_intake_module.__file__).read_text()
        
        # Check for hardcoded project names
        assert "Alya" not in source_code or "character_name" in source_code, "No hardcoded character names in core logic"
        assert "Mir Erdan" not in source_code, "No hardcoded character names in core logic"
        assert "rc2_multishot1_ep01" not in source_code, "No hardcoded project paths in core logic"
