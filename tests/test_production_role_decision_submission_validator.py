"""Tests for production role decision submission validator module."""

import json
from pathlib import Path
import pytest
import tempfile
import shutil


class TestProductionRoleDecisionSubmissionValidator:
    """Test suite for production role decision submission validation."""
    
    def test_blank_submission_templates_return_awaiting_role_input(self, tmp_path):
        """Test that blank templates (selected_decision=null) return awaiting_role_input status."""
        from app.production_cards.decision_submission_validator import validate_submitted_role_decisions
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create role_decision_submissions directory
        submissions_dir = control_dir / "role_decision_submissions"
        submissions_dir.mkdir(parents=True)
        
        # Create blank Character Director submission template
        char_submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "character_name": "TestChar",
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
            "selected_decision": None,  # BLANK
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        # Create blank Workflow TD submission template
        workflow_submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes"],
            "selected_decision": None,  # BLANK
            "required_artifacts": ["workflow_audit", "required_nodes", "required_models"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'w') as f:
            json.dump(char_submission, f)
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'w') as f:
            json.dump(workflow_submission, f)
        
        # Validate submissions
        result = validate_submitted_role_decisions(str(tmp_path))
        
        # Verify awaiting_role_input status
        assert result["status"] == "awaiting_role_input"
        assert result["submitted_decisions_ready"] is False
        assert result["valid_submissions"] == 0
        assert result["retry_gate_open"] is False
        assert result["production_accepted"] is False
        assert result["downstream_blocked"] is True
        assert "character_identity_approval" in result["missing_or_incomplete_submissions"]
        assert "workflow_fit_approval" in result["missing_or_incomplete_submissions"]
    
    def test_completed_character_director_submission_validates(self, tmp_path):
        """Test that completed Character Director submission validates successfully."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create completed Character Director submission
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "character_name": "TestChar",
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
            "selected_decision": "approve",  # COMPLETED
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify valid
        assert result["valid"] is True
        assert result["is_complete"] is True
        assert len(result["rejection_reasons"]) == 0
    
    def test_completed_workflow_td_submission_validates(self, tmp_path):
        """Test that completed Workflow TD submission validates successfully."""
        from app.production_cards.decision_submission_validator import validate_workflow_td_submission
        
        # Create completed Workflow TD submission
        submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes"],
            "selected_decision": "approve_workflow",  # COMPLETED
            "required_artifacts": ["workflow_audit", "required_nodes", "required_models"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        # Validate submission
        result = validate_workflow_td_submission(submission, tmp_path.name)
        
        # Verify valid
        assert result["valid"] is True
        assert result["is_complete"] is True
        assert len(result["rejection_reasons"]) == 0
    
    def test_both_completed_submissions_return_submitted_decisions_ready_true(self, tmp_path):
        """Test that both completed submissions return submitted_decisions_ready=true."""
        from app.production_cards.decision_submission_validator import validate_submitted_role_decisions
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create role_decision_submissions directory
        submissions_dir = control_dir / "role_decision_submissions"
        submissions_dir.mkdir(parents=True)
        
        # Create completed Character Director submission
        char_submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "character_name": "TestChar",
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
            "selected_decision": "approve",  # COMPLETED
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        # Create completed Workflow TD submission
        workflow_submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "current_decision_status": "draft_submission",
            "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes"],
            "selected_decision": "approve_workflow",  # COMPLETED
            "required_artifacts": ["workflow_audit", "required_nodes", "required_models"],
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'w') as f:
            json.dump(char_submission, f)
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'w') as f:
            json.dump(workflow_submission, f)
        
        # Validate submissions
        result = validate_submitted_role_decisions(str(tmp_path))
        
        # Verify valid status
        assert result["status"] == "valid"
        assert result["submitted_decisions_ready"] is True
        assert result["valid_submissions"] == 2
        assert result["complete_submissions"] == 2
        assert result["would_allow_intake"] is True
        assert result["would_allow_retry_generation_after_apply"] is True
        assert result["next_allowed_action_if_applied"] == "retry_generate_frames"
        assert result["production_accepted_after_apply"] is False
        assert result["retry_gate_open"] is False
        assert result["real_project_mutated"] is False
    
    def test_fixture_only_true_is_rejected(self, tmp_path):
        """Test that fixture_only=true is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with fixture_only=true
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": True,  # REJECTED
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "fixture_only_true_rejected" in result["rejection_reasons"]
    
    def test_decision_source_mismatch_is_rejected(self, tmp_path):
        """Test that decision_source mismatch is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with wrong decision_source
        submission = {
            "role": "Character Director",
            "decision_source": "fixture",  # WRONG
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "decision_source_not_real_role_decision" in result["rejection_reasons"]
    
    def test_approved_for_project_id_mismatch_is_rejected(self, tmp_path):
        """Test that approved_for_project_id mismatch is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with wrong project_id
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": "wrong_project_id",  # WRONG
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "approved_for_project_id_mismatch" in result["rejection_reasons"][0]
    
    def test_approved_for_shot_missing_is_rejected(self, tmp_path):
        """Test that missing approved_for_shot is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission without approved_for_shot
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            # approved_for_shot MISSING
            "selected_decision": "approve",
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "approved_for_shot_missing" in result["rejection_reasons"]
    
    def test_selected_decision_null_is_incomplete(self, tmp_path):
        """Test that selected_decision=null is marked as incomplete."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with selected_decision=null
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": None,  # NULL
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify incomplete
        assert result["valid"] is False
        assert result["is_complete"] is False
        assert "selected_decision_null_incomplete" in result["rejection_reasons"]
    
    def test_selected_decision_outside_allowed_decisions_is_rejected(self, tmp_path):
        """Test that selected_decision outside allowed_decisions is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with disallowed decision
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "allowed_decisions": ["approve", "reject", "request_new_reference"],
            "selected_decision": "disallowed_decision",  # NOT IN ALLOWED
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "selected_decision_not_allowed" in result["rejection_reasons"][0]
    
    def test_production_accepted_true_is_rejected(self, tmp_path):
        """Test that production_accepted=true is rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with production_accepted=true
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "production_accepted": True,  # REJECTED
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "production_accepted_true_rejected" in result["rejection_reasons"]
    
    def test_workflow_td_legacy_reference_locked_true_is_rejected(self, tmp_path):
        """Test that Workflow TD legacy_reference_locked=true is rejected."""
        from app.production_cards.decision_submission_validator import validate_workflow_td_submission
        
        # Create submission with legacy_reference_locked=true
        submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": True,  # REJECTED
            "selected_decision": "approve_workflow",
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_workflow_td_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "legacy_reference_locked_true_rejected" in result["rejection_reasons"]
    
    def test_workflow_td_non_gorynych_mode_is_rejected(self, tmp_path):
        """Test that Workflow TD non-gorynych mode is rejected."""
        from app.production_cards.decision_submission_validator import validate_workflow_td_submission
        
        # Create submission with non-gorynych mode
        submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "reference_locked",  # NOT GORYNYCH
            "legacy_reference_locked_allowed_for_production": False,
            "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes"],
            "selected_decision": "approve_workflow",
            "required_artifacts": ["workflow_audit", "required_nodes", "required_models"],
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_workflow_td_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "generation_mode_not_gorynych" in result["rejection_reasons"][0]
    
    def test_missing_required_artifacts_are_rejected(self, tmp_path):
        """Test that missing required artifacts are rejected."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission without required artifacts
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "required_artifacts": [],  # EMPTY
            "production_accepted": False
        }
        
        # Validate submission
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify rejected
        assert result["valid"] is False
        assert "required_artifacts_missing" in result["rejection_reasons"]
    
    def test_validation_does_not_mutate_project(self, tmp_path):
        """Test that validation does not mutate project files."""
        from app.production_cards.decision_submission_validator import validate_submitted_role_decisions
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create role_decision_submissions directory
        submissions_dir = control_dir / "role_decision_submissions"
        submissions_dir.mkdir(parents=True)
        
        # Create blank submissions
        char_submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": None,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        workflow_submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "selected_decision": None,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'w') as f:
            json.dump(char_submission, f)
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'w') as f:
            json.dump(workflow_submission, f)
        
        # Record file hashes before validation
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'r') as f:
            char_before = f.read()
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'r') as f:
            workflow_before = f.read()
        
        # Validate submissions
        validate_submitted_role_decisions(str(tmp_path))
        
        # Verify files unchanged
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'r') as f:
            char_after = f.read()
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'r') as f:
            workflow_after = f.read()
        
        assert char_before == char_after
        assert workflow_before == workflow_after
    
    def test_retry_gate_remains_closed(self, tmp_path):
        """Test that retry_gate remains closed after validation."""
        from app.production_cards.decision_submission_validator import validate_submitted_role_decisions
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create role_decision_submissions directory
        submissions_dir = control_dir / "role_decision_submissions"
        submissions_dir.mkdir(parents=True)
        
        # Create completed submissions
        char_submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "selected_decision": "approve",
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        workflow_submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Workflow TD / ComfyUI Technical Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "selected_decision": "approve_workflow",
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'w') as f:
            json.dump(char_submission, f)
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'w') as f:
            json.dump(workflow_submission, f)
        
        # Validate submissions
        result = validate_submitted_role_decisions(str(tmp_path))
        
        # Verify retry_gate remains closed
        assert result["retry_gate_open"] is False
        assert result["production_accepted"] is False
        assert result["downstream_blocked"] is True
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that validation does not hardcode Alya/Mir Erdan character names."""
        from app.production_cards.decision_submission_validator import validate_character_director_submission
        
        # Create submission with generic character name
        submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "approved_by_role": "Character Director",
            "approved_for_project_id": tmp_path.name,
            "approved_for_shot": "shot01",
            "character_name": "GenericCharacter",  # NOT ALYA OR MIR ERDAN
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
            "selected_decision": "approve",
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"],
            "production_accepted": False
        }
        
        # Validate submission - should succeed with generic name
        result = validate_character_director_submission(submission, tmp_path.name)
        
        # Verify valid (no hardcode rejection)
        assert result["valid"] is True
