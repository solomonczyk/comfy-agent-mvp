"""Tests for production role approval gate module."""

import json
from pathlib import Path
import pytest


class TestProductionRoleApprovalGate:
    """Test suite for role approval gate validation."""
    
    def test_pending_decisions_block_retry_generation(self, tmp_path):
        """Test that pending decisions block retry generation."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create pending Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "pending",
            "selected_decision": None,
            "required_artifacts": []
        }
        
        # Create pending Workflow TD decision
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "pending",
            "selected_decision": None,
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": []
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify pending decisions block retry
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["downstream_blocked"] == True
        assert result["production_accepted"] == False
        assert result["next_allowed_action"] is None
    
    def test_missing_character_director_approval_blocks_retry(self, tmp_path):
        """Test that missing Character Director approval blocks retry."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create pending Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "pending",
            "selected_decision": None,
            "required_artifacts": []
        }
        
        # Create approved Workflow TD decision
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": {
                "workflow_audit": "audit_result",
                "required_nodes": "nodes_list",
                "required_models": "models_list",
                "preflight_result": "preflight_pass",
                "output_collection_contract": "contract"
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify missing Character Director approval blocks retry
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["downstream_blocked"] == True
        assert "character_identity_approval" in result["missing_approvals"]
        assert "Character Director" in result["blocking_roles"]
    
    def test_missing_workflow_td_approval_blocks_retry(self, tmp_path):
        """Test that missing Workflow TD approval blocks retry."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create approved Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                "approved_reference_strategy": "strategy",
                "identity_acceptance_criteria": "criteria"
            }
        }
        
        # Create pending Workflow TD decision
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "pending",
            "selected_decision": None,
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": []
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify missing Workflow TD approval blocks retry
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["downstream_blocked"] == True
        assert "workflow_fit_approval" in result["missing_approvals"]
        assert "Workflow TD / ComfyUI Technical Director" in result["blocking_roles"]
    
    def test_both_approvals_allow_retry_generate_frames_only(self, tmp_path):
        """Test that both approvals allow retry_generate_frames only."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create approved Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                "approved_reference_strategy": "strategy",
                "identity_acceptance_criteria": "criteria"
            }
        }
        
        # Create approved Workflow TD decision
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": {
                "workflow_audit": "audit_result",
                "required_nodes": "nodes_list",
                "required_models": "models_list",
                "preflight_result": "preflight_pass",
                "output_collection_contract": "contract"
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify both approvals allow retry_generate_frames only
        assert result["status"] == "ready_for_retry"
        assert result["can_retry_generation"] == True
        assert result["downstream_blocked"] == False
        assert result["production_accepted"] == False  # Approval does NOT mean production accepted
        assert result["next_allowed_action"] == "retry_generate_frames"
        assert len(result["missing_approvals"]) == 0
    
    def test_approval_to_retry_does_not_set_production_accepted_true(self, tmp_path):
        """Test that approval to retry does not set production_accepted=true."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create approved Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                "approved_reference_strategy": "strategy",
                "identity_acceptance_criteria": "criteria"
            }
        }
        
        # Create approved Workflow TD decision
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": {
                "workflow_audit": "audit_result",
                "required_nodes": "nodes_list",
                "required_models": "models_list",
                "preflight_result": "preflight_pass",
                "output_collection_contract": "contract"
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify production_accepted remains false
        assert result["production_accepted"] == False
    
    def test_legacy_reference_locked_approval_is_rejected(self, tmp_path):
        """Test that legacy_reference_locked approval is rejected."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create approved Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                "approved_reference_strategy": "strategy",
                "identity_acceptance_criteria": "criteria"
            }
        }
        
        # Create Workflow TD decision with legacy_reference_locked_allowed=true
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": True,  # This should reject
            "required_artifacts": {
                "workflow_audit": "audit_result",
                "required_nodes": "nodes_list",
                "required_models": "models_list",
                "preflight_result": "preflight_pass",
                "output_collection_contract": "contract"
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify legacy_reference_locked approval is rejected
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["workflow_td_evaluation"]["approved"] == False
        assert result["workflow_td_evaluation"]["reason"] == "legacy_reference_locked_not_allowed"
    
    def test_workflow_approval_requires_gorynych_identity(self, tmp_path):
        """Test that workflow approval requires gorynych_identity."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create approved Character Director decision
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                "approved_reference_strategy": "strategy",
                "identity_acceptance_criteria": "criteria"
            }
        }
        
        # Create Workflow TD decision with wrong generation mode
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "reference_locked",  # Wrong mode
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": {
                "workflow_audit": "audit_result",
                "required_nodes": "nodes_list",
                "required_models": "models_list",
                "preflight_result": "preflight_pass",
                "output_collection_contract": "contract"
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify wrong generation mode is rejected
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["workflow_td_evaluation"]["approved"] == False
        assert result["workflow_td_evaluation"]["reason"] == "invalid_generation_mode"
    
    def test_incomplete_approval_artifacts_block_retry(self, tmp_path):
        """Test that incomplete approval artifacts block retry."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create Character Director decision with missing artifacts
        char_decision = {
            "role": "Character Director",
            "decision_status": "decided",
            "selected_decision": "approve",
            "required_artifacts": {
                "approved_character_identity_rules": "rules",
                # Missing approved_reference_strategy
                # Missing identity_acceptance_criteria
            }
        }
        
        # Create Workflow TD decision with missing artifacts
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "decided",
            "selected_decision": "approve_workflow",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": {
                "workflow_audit": "audit_result",
                # Missing required_nodes
                # Missing required_models
                # Missing preflight_result
                # Missing output_collection_contract
            }
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify incomplete artifacts block retry
        assert result["status"] == "blocked"
        assert result["can_retry_generation"] == False
        assert result["character_director_evaluation"]["approved"] == False
        assert result["character_director_evaluation"]["reason"] == "missing_artifacts"
        assert result["workflow_td_evaluation"]["approved"] == False
        assert result["workflow_td_evaluation"]["reason"] == "missing_artifacts"
    
    def test_validate_role_approval_gate_returns_structured_json(self, tmp_path):
        """Test that validate-role-approval-gate returns structured JSON."""
        from app.production_cards.approval_gate import validate_role_approval_gate
        
        # Create role_decisions directory
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        role_decisions_dir.mkdir(parents=True)
        
        # Create pending decisions
        char_decision = {
            "role": "Character Director",
            "decision_status": "pending",
            "selected_decision": None,
            "required_artifacts": []
        }
        
        workflow_decision = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "decision_status": "pending",
            "selected_decision": None,
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_artifacts": []
        }
        
        with open(role_decisions_dir / "character_director_identity_decision.json", "w") as f:
            json.dump(char_decision, f)
        with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", "w") as f:
            json.dump(workflow_decision, f)
        
        # Validate gate
        result = validate_role_approval_gate(str(tmp_path), json_output=True)
        
        # Verify structured JSON output
        assert "status" in result
        assert "can_retry_generation" in result
        assert "downstream_blocked" in result
        assert "production_accepted" in result
        assert "required_approvals" in result
        assert "missing_approvals" in result
        assert "blocking_roles" in result
        assert "next_allowed_action" in result
        assert "character_director_evaluation" in result
        assert "workflow_td_evaluation" in result
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that approval_gate module has no hardcoded Alya/Mir Erdan."""
        import app.production_cards.approval_gate as approval_gate_module
        import inspect
        
        # Get the source code of the approval_gate module
        source = inspect.getsource(approval_gate_module)
        
        # Verify no hardcoded project-specific names
        assert "Mir Erdan" not in source
        
        # The module should not hardcode these names - they should come from input data
        # Any occurrence of "Alya" should be in test data or comments, not in core logic
