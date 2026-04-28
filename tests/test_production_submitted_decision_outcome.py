"""
Tests for RC2-PRODCARDS2P — Submitted Decision Outcome Gate

Tests that evaluate_submitted_decision_outcome correctly classifies
approvals vs change requests before any apply or retry generation.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.decision_submission_outcome import (
    load_submitted_decisions,
    classify_character_director_outcome,
    classify_workflow_td_outcome,
    determine_next_required_role_actions,
    validate_submission_safety,
    validate_workflow_td_specific_safety,
    evaluate_submitted_decision_outcome,
)


class TestLoadSubmittedDecisions:
    """Test loading submitted decisions from submission directory."""
    
    def test_load_submitted_decisions_from_default_path(self):
        """Test loading decisions from default submitted/ path."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            # Create test submissions
            char_submission = {
                "role": "Character Director",
                "selected_decision": "approve"
            }
            workflow_submission = {
                "role": "Workflow TD / ComfyUI Technical Director",
                "selected_decision": "approve_workflow"
            }
            
            with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            with open(submitted_dir / "workflow_td_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(workflow_submission, f)
            
            result = load_submitted_decisions(str(project_root))
            
            assert result["character_director_submission"]["selected_decision"] == "approve"
            assert result["workflow_td_submission"]["selected_decision"] == "approve_workflow"
    
    def test_load_submitted_decisions_from_custom_path(self):
        """Test loading decisions from custom submission root."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            custom_root = project_root / "custom_submissions"
            custom_root.mkdir(parents=True, exist_ok=True)
            
            # Create test submission
            char_submission = {
                "role": "Character Director",
                "selected_decision": "approve"
            }
            
            with open(custom_root / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            
            result = load_submitted_decisions(str(project_root), str(custom_root))
            
            assert result["character_director_submission"]["selected_decision"] == "approve"
    
    def test_load_submitted_decisions_missing_files(self):
        """Test loading decisions when files are missing."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            result = load_submitted_decisions(str(project_root))
            
            assert result["character_director_submission"] == {}
            assert result["workflow_td_submission"] == {}


class TestClassifyCharacterDirectorOutcome:
    """Test Character Director outcome classification."""
    
    def test_classify_approve_with_artifacts(self):
        """Test classify approve with complete artifacts."""
        submission = {
            "selected_decision": "approve",
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"]
        }
        
        result = classify_character_director_outcome(submission)
        
        assert result["outcome"] == "approve"
        assert result["allows_apply"] is True
        assert result["allows_retry"] is True
        assert result["artifacts_complete"] is True
    
    def test_classify_approve_without_artifacts(self):
        """Test classify approve without complete artifacts."""
        submission = {
            "selected_decision": "approve",
            "required_artifacts": []
        }
        
        result = classify_character_director_outcome(submission)
        
        assert result["outcome"] == "approve"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
        assert result["artifacts_complete"] is False
    
    def test_classify_reject(self):
        """Test classify reject."""
        submission = {
            "selected_decision": "reject"
        }
        
        result = classify_character_director_outcome(submission)
        
        assert result["outcome"] == "reject"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_request_new_reference(self):
        """Test classify request_new_reference."""
        submission = {
            "selected_decision": "request_new_reference"
        }
        
        result = classify_character_director_outcome(submission)
        
        assert result["outcome"] == "request_new_reference"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_request_workflow_change(self):
        """Test classify request_workflow_change."""
        submission = {
            "selected_decision": "request_workflow_change"
        }
        
        result = classify_character_director_outcome(submission)
        
        assert result["outcome"] == "request_workflow_change"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_no_submission(self):
        """Test classify with no submission."""
        result = classify_character_director_outcome({})
        
        assert result["outcome"] == "no_submission"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False


class TestClassifyWorkflowTDOutcome:
    """Test Workflow TD outcome classification."""
    
    def test_classify_approve_workflow_with_artifacts(self):
        """Test classify approve_workflow with complete artifacts."""
        submission = {
            "selected_decision": "approve_workflow",
            "required_artifacts": ["workflow_audit", "required_nodes"]
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "approve_workflow"
        assert result["allows_apply"] is True
        assert result["allows_retry"] is True
        assert result["artifacts_complete"] is True
    
    def test_classify_approve_workflow_without_artifacts(self):
        """Test classify approve_workflow without complete artifacts."""
        submission = {
            "selected_decision": "approve_workflow",
            "required_artifacts": []
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "approve_workflow"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
        assert result["artifacts_complete"] is False
    
    def test_classify_reject_workflow(self):
        """Test classify reject_workflow."""
        submission = {
            "selected_decision": "reject_workflow"
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "reject_workflow"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_request_missing_nodes(self):
        """Test classify request_missing_nodes."""
        submission = {
            "selected_decision": "request_missing_nodes"
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "request_missing_nodes"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_request_missing_models(self):
        """Test classify request_missing_models."""
        submission = {
            "selected_decision": "request_missing_models"
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "request_missing_models"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_request_reference_rebuild(self):
        """Test classify request_reference_rebuild."""
        submission = {
            "selected_decision": "request_reference_rebuild"
        }
        
        result = classify_workflow_td_outcome(submission)
        
        assert result["outcome"] == "request_reference_rebuild"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False
    
    def test_classify_no_submission(self):
        """Test classify with no submission."""
        result = classify_workflow_td_outcome({})
        
        assert result["outcome"] == "no_submission"
        assert result["allows_apply"] is False
        assert result["allows_retry"] is False


class TestDetermineNextRequiredRoleActions:
    """Test determining next required role actions."""
    
    def test_request_workflow_change_actions(self):
        """Test actions for request_workflow_change."""
        char_outcome = {"outcome": "request_workflow_change"}
        workflow_outcome = {"outcome": "approve_workflow"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 1
        assert actions[0]["role"] == "Character Director"
        assert actions[0]["action"] == "review_updated_identity_strategy_after_workflow_change"
    
    def test_request_new_reference_actions(self):
        """Test actions for request_new_reference."""
        char_outcome = {"outcome": "request_new_reference"}
        workflow_outcome = {"outcome": "approve_workflow"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 1
        assert actions[0]["role"] == "Character Director"
        assert actions[0]["action"] == "provide_new_character_reference"
    
    def test_request_reference_rebuild_actions(self):
        """Test actions for request_reference_rebuild."""
        char_outcome = {"outcome": "approve"}
        workflow_outcome = {"outcome": "request_reference_rebuild"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 1
        assert actions[0]["role"] == "Workflow TD / ComfyUI Technical Director"
        assert actions[0]["action"] == "rebuild_or_update_identity_workflow_reference_strategy"
    
    def test_request_missing_nodes_actions(self):
        """Test actions for request_missing_nodes."""
        char_outcome = {"outcome": "approve"}
        workflow_outcome = {"outcome": "request_missing_nodes"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 1
        assert actions[0]["role"] == "Workflow TD / ComfyUI Technical Director"
        assert actions[0]["action"] == "provide_or_install_missing_comfyui_nodes"
    
    def test_request_missing_models_actions(self):
        """Test actions for request_missing_models."""
        char_outcome = {"outcome": "approve"}
        workflow_outcome = {"outcome": "request_missing_models"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 1
        assert actions[0]["role"] == "Workflow TD / ComfyUI Technical Director"
        assert actions[0]["action"] == "provide_or_install_missing_models"
    
    def test_both_change_requests(self):
        """Test actions when both request changes."""
        char_outcome = {"outcome": "request_workflow_change"}
        workflow_outcome = {"outcome": "request_reference_rebuild"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 2
        assert any(a["role"] == "Character Director" for a in actions)
        assert any(a["role"] == "Workflow TD / ComfyUI Technical Director" for a in actions)
    
    def test_both_approvals(self):
        """Test no actions when both approve."""
        char_outcome = {"outcome": "approve"}
        workflow_outcome = {"outcome": "approve_workflow"}
        
        actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
        
        assert len(actions) == 0


class TestValidateSubmissionSafety:
    """Test submission safety validation."""
    
    def test_valid_submission(self):
        """Test valid submission passes safety checks."""
        submission = {
            "fixture_only": False,
            "production_accepted": False,
            "selected_decision": "approve",
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"]
        }
        
        result = validate_submission_safety(submission, "test_project")
        
        assert result["valid"] is True
        assert len(result["rejection_reasons"]) == 0
    
    def test_reject_fixture_only(self):
        """Test reject fixture_only=true."""
        submission = {
            "fixture_only": True,
            "production_accepted": False,
            "selected_decision": "approve",
            "allowed_decisions": ["approve"]
        }
        
        result = validate_submission_safety(submission, "test_project")
        
        assert result["valid"] is False
        assert "fixture_only_true_rejected" in result["rejection_reasons"]
    
    def test_reject_production_accepted_true(self):
        """Test reject production_accepted=true."""
        submission = {
            "fixture_only": False,
            "production_accepted": True,
            "selected_decision": "approve",
            "allowed_decisions": ["approve"]
        }
        
        result = validate_submission_safety(submission, "test_project")
        
        assert result["valid"] is False
        assert "production_accepted_true_rejected" in result["rejection_reasons"]
    
    def test_reject_selected_decision_null(self):
        """Test reject selected_decision=null."""
        submission = {
            "fixture_only": False,
            "production_accepted": False,
            "selected_decision": None,
            "allowed_decisions": ["approve"]
        }
        
        result = validate_submission_safety(submission, "test_project")
        
        assert result["valid"] is False
        assert "selected_decision_null" in result["rejection_reasons"]
    
    def test_reject_selected_decision_not_allowed(self):
        """Test reject selected_decision outside allowed list."""
        submission = {
            "fixture_only": False,
            "production_accepted": False,
            "selected_decision": "invalid_decision",
            "allowed_decisions": ["approve", "reject"]
        }
        
        result = validate_submission_safety(submission, "test_project")
        
        assert result["valid"] is False
        assert "selected_decision_not_allowed" in result["rejection_reasons"][0]
    
    def test_reject_no_submission(self):
        """Test reject when submission is missing."""
        result = validate_submission_safety({}, "test_project")
        
        assert result["valid"] is False
        assert "submission_not_found" in result["rejection_reasons"]


class TestValidateWorkflowTDSpecificSafety:
    """Test Workflow TD specific safety validation."""
    
    def test_valid_workflow_submission(self):
        """Test valid workflow submission passes safety checks."""
        submission = {
            "legacy_reference_locked_allowed_for_production": False,
            "current_required_generation_mode": "gorynych_identity"
        }
        
        result = validate_workflow_td_specific_safety(submission)
        
        assert result["valid"] is True
        assert len(result["rejection_reasons"]) == 0
    
    def test_reject_legacy_reference_locked_true(self):
        """Test reject legacy_reference_locked_allowed_for_production=true."""
        submission = {
            "legacy_reference_locked_allowed_for_production": True,
            "current_required_generation_mode": "gorynych_identity"
        }
        
        result = validate_workflow_td_specific_safety(submission)
        
        assert result["valid"] is False
        assert "legacy_reference_locked_true_rejected" in result["rejection_reasons"]
    
    def test_reject_non_gorynych_mode(self):
        """Test reject generation_mode not gorynych_identity."""
        submission = {
            "legacy_reference_locked_allowed_for_production": False,
            "current_required_generation_mode": "reference_locked"
        }
        
        result = validate_workflow_td_specific_safety(submission)
        
        assert result["valid"] is False
        assert "generation_mode_not_gorynych" in result["rejection_reasons"][0]
    
    def test_reject_no_submission(self):
        """Test reject when submission is missing."""
        result = validate_workflow_td_specific_safety({})
        
        assert result["valid"] is False
        assert "submission_not_found" in result["rejection_reasons"]


class TestEvaluateSubmittedDecisionOutcome:
    """Test evaluate_submitted_decision_outcome function."""
    
    def setup_project_with_submissions(self, tmpdir, char_decision, workflow_decision):
        """Helper to set up project with submissions."""
        project_root = Path(tmpdir)
        submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
        submitted_dir.mkdir(parents=True, exist_ok=True)
        
        # Create character director submission
        char_submission = {
            "role": "Character Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "production_accepted": False,
            "selected_decision": char_decision,
            "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
            "required_artifacts": ["approved_character_identity_rules", "approved_reference_strategy"]
        }
        
        # Create workflow TD submission
        workflow_submission = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_source": "real_role_decision",
            "fixture_only": False,
            "production_accepted": False,
            "selected_decision": workflow_decision,
            "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes", "request_missing_models", "request_reference_rebuild"],
            "required_artifacts": ["workflow_audit", "required_nodes"],
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False
        }
        
        with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
            json.dump(char_submission, f)
        with open(submitted_dir / "workflow_td_real_decision.SUBMITTED.json", 'w') as f:
            json.dump(workflow_submission, f)
        
        # Create artifact index
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        
        artifact_index = {
            "downstream_blocked": True,
            "production_accepted": False,
            "retry_gate_open": False
        }
        
        with open(control_dir / "artifact_index.json", 'w') as f:
            json.dump(artifact_index, f)
        
        # Create role_decisions with pending status
        role_decisions_dir = control_dir / "role_decisions"
        role_decisions_dir.mkdir(parents=True, exist_ok=True)
        
        char_decision_template = {
            "decision_status": "pending",
            "selected_decision": None
        }
        workflow_decision_template = {
            "decision_status": "pending",
            "selected_decision": None
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
            json.dump(char_decision_template, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'w') as f:
            json.dump(workflow_decision_template, f)
        
        return project_root
    
    def test_current_submitted_drafts_return_changes_requested(self):
        """Test current submitted drafts return changes_requested."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "changes_requested"
            assert result["submitted_decisions_valid"] is True
            assert result["ready_for_apply"] is False
            assert result["can_retry_generation"] is False
            assert result["retry_gate_open"] is False
            assert result["production_accepted"] is False
            assert result["downstream_blocked"] is True
            assert result["character_director_outcome"] == "request_workflow_change"
            assert result["workflow_td_outcome"] == "request_reference_rebuild"
            assert result["apply_performed"] is False
            assert result["real_project_mutated"] is False
    
    def test_request_workflow_change_does_not_allow_retry(self):
        """Test request_workflow_change does not allow retry."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="approve_workflow"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "changes_requested"
            assert result["ready_for_apply"] is False
            assert result["can_retry_generation"] is False
    
    def test_request_reference_rebuild_does_not_allow_retry(self):
        """Test request_reference_rebuild does not allow retry."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="approve",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "changes_requested"
            assert result["ready_for_apply"] is False
            assert result["can_retry_generation"] is False
    
    def test_valid_non_approval_submissions_return_ready_for_apply_false(self):
        """Test valid non-approval submissions return ready_for_apply=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_new_reference",
                workflow_decision="request_missing_nodes"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "changes_requested"
            assert result["submitted_decisions_valid"] is True
            assert result["ready_for_apply"] is False
    
    def test_temp_approval_submissions_return_approval_ready_for_apply(self):
        """Test temp approval submissions return approval_ready_for_apply without applying."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="approve",
                workflow_decision="approve_workflow"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "approval_ready_for_apply"
            assert result["submitted_decisions_valid"] is True
            assert result["ready_for_apply"] is True
            assert result["can_retry_generation"] is False
            assert result["can_retry_generation_after_apply"] is True
            assert result["next_allowed_action_if_applied"] == "retry_generate_frames"
            assert result["production_accepted_after_apply"] is False
            assert result["apply_performed"] is False
            assert result["real_project_mutated"] is False
    
    def test_invalid_submissions_are_rejected(self):
        """Test invalid submissions are rejected."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            # Create invalid submission with selected_decision outside allowed list
            char_submission = {
                "role": "Character Director",
                "decision_source": "real_role_decision",
                "fixture_only": False,
                "production_accepted": False,
                "selected_decision": "invalid_decision",
                "allowed_decisions": ["approve", "reject"]
            }
            
            with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            
            # Create minimal artifact index
            control_dir = project_root / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)
            artifact_index = {"downstream_blocked": True}
            with open(control_dir / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "rejected"
            assert result["submitted_decisions_valid"] is False
            assert len(result["rejection_reasons"]) > 0
    
    def test_fixture_only_true_is_rejected(self):
        """Test fixture_only=true is rejected."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            char_submission = {
                "role": "Character Director",
                "fixture_only": True,
                "production_accepted": False,
                "selected_decision": "approve",
                "allowed_decisions": ["approve"]
            }
            
            with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            
            control_dir = project_root / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)
            artifact_index = {"downstream_blocked": True}
            with open(control_dir / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "rejected"
            assert any("fixture_only_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_production_accepted_true_is_rejected(self):
        """Test production_accepted=true is rejected."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            char_submission = {
                "role": "Character Director",
                "fixture_only": False,
                "production_accepted": True,
                "selected_decision": "approve",
                "allowed_decisions": ["approve"]
            }
            
            with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            
            control_dir = project_root / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)
            artifact_index = {"downstream_blocked": True}
            with open(control_dir / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "rejected"
            assert any("production_accepted_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_legacy_reference_locked_workflow_is_rejected(self):
        """Test legacy_reference_locked workflow is rejected."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="approve",
                workflow_decision="approve_workflow"
            )
            
            # Modify workflow submission to have legacy_reference_locked_allowed_for_production=True
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            with open(submitted_dir / "workflow_td_real_decision.SUBMITTED.json", 'r') as f:
                workflow_submission = json.load(f)
            
            workflow_submission["legacy_reference_locked_allowed_for_production"] = True
            
            with open(submitted_dir / "workflow_td_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(workflow_submission, f)
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["status"] == "rejected"
            assert any("legacy_reference_locked_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_role_decisions_remain_pending(self):
        """Test role_decisions remain pending after evaluation."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            # Evaluate outcome
            evaluate_submitted_decision_outcome(str(project_root))
            
            # Check role_decisions still pending
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'r') as f:
                char_decision = json.load(f)
            
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'r') as f:
                workflow_decision = json.load(f)
            
            assert char_decision["decision_status"] == "pending"
            assert workflow_decision["decision_status"] == "pending"
    
    def test_retry_gate_remains_closed(self):
        """Test retry gate remains closed after evaluation."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["retry_gate_open"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["retry_gate_open"] is False
    
    def test_production_accepted_remains_false(self):
        """Test production_accepted remains false after evaluation."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["production_accepted"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["production_accepted"] is False
    
    def test_downstream_blocked_remains_true(self):
        """Test downstream_blocked remains true after evaluation."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert result["downstream_blocked"] is True
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["downstream_blocked"] is True
    
    def test_next_required_actions_for_change_requests(self):
        """Test next_required_actions are correctly identified for change requests."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            assert len(result["next_required_actions"]) == 2
            assert any(a["role"] == "Character Director" and a["action"] == "review_updated_identity_strategy_after_workflow_change" for a in result["next_required_actions"])
            assert any(a["role"] == "Workflow TD / ComfyUI Technical Director" and a["action"] == "rebuild_or_update_identity_workflow_reference_strategy" for a in result["next_required_actions"])
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test no core hardcode for Alya/Mir Erdan character names."""
        with TemporaryDirectory() as tmpdir:
            # Test with different character name to prove no hardcode
            project_root = Path(tmpdir)
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            char_submission = {
                "role": "Character Director",
                "decision_source": "real_role_decision",
                "fixture_only": False,
                "production_accepted": False,
                "selected_decision": "approve",
                "allowed_decisions": ["approve"],
                "required_artifacts": ["approved_character_identity_rules"],
                "character_name": "CustomCharacter"  # Not Alya or Mir Erdan
            }
            
            workflow_submission = {
                "role": "Workflow TD / ComfyUI Technical Director",
                "decision_source": "real_role_decision",
                "fixture_only": False,
                "production_accepted": False,
                "selected_decision": "approve_workflow",
                "allowed_decisions": ["approve_workflow"],
                "required_artifacts": ["workflow_audit"],
                "current_required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            
            with open(submitted_dir / "character_director_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(char_submission, f)
            with open(submitted_dir / "workflow_td_real_decision.SUBMITTED.json", 'w') as f:
                json.dump(workflow_submission, f)
            
            # Create artifact index and role_decisions
            control_dir = project_root / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)
            
            artifact_index = {
                "downstream_blocked": True,
                "production_accepted": False,
                "retry_gate_open": False
            }
            with open(control_dir / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            role_decisions_dir = control_dir / "role_decisions"
            role_decisions_dir.mkdir(parents=True, exist_ok=True)
            
            char_decision_template = {"decision_status": "pending"}
            workflow_decision_template = {"decision_status": "pending"}
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'w') as f:
                json.dump(char_decision_template, f)
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'w') as f:
                json.dump(workflow_decision_template, f)
            
            result = evaluate_submitted_decision_outcome(str(project_root))
            
            # Should work with any character name, not hardcoded to Alya/Mir Erdan
            assert result["status"] == "approval_ready_for_apply"
            assert result["submitted_decisions_valid"] is True
