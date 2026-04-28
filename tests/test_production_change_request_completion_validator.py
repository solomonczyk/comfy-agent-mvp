"""
Tests for RC2-PRODCARDS2U — Submitted Change Request Completion Validation, No Apply

Tests that submitted change request completions are validated before they are allowed
to trigger resubmission of role decisions, without executing workflow changes,
rebuilding references, applying decisions, or opening retry generation.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.change_request_completion_validator import (
    validate_workflow_td_completion_submission,
    validate_character_director_completion_submission,
    compare_completion_against_contract,
    validate_submitted_change_request_completions,
)


class TestBlankCompletionTemplates:
    """Test that blank completion templates return awaiting_completion_input."""
    
    def test_blank_completion_templates_return_awaiting_completion_input(self):
        """Test blank completion templates return awaiting_completion_input."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            result = validate_submitted_change_request_completions(str(project_root))
            
            assert result["status"] == "awaiting_completion_input"
            assert result["submitted_completions_ready"] is False
            assert result["valid_completions"] == 0
            assert result["ready_for_resubmission"] is False
            assert result["execution_performed"] is False
            assert result["retry_gate_open"] is False
            assert result["production_accepted"] is False
            assert result["downstream_blocked"] is True
    
    def test_completion_status_template_is_incomplete(self):
        """Test completion_status=template is incomplete."""
        completion = {
            "completion_status": "template",
            "selected_resolution": None
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["is_complete"] is False
        assert result["valid"] is False
        assert any("completion_status_not_submitted" in r for r in result["rejection_reasons"])
    
    def test_selected_resolution_null_is_incomplete(self):
        """Test selected_resolution=null is incomplete."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": None
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["is_complete"] is False
        assert result["valid"] is False
        assert any("selected_resolution_null" in r for r in result["rejection_reasons"])


class TestSubmittedCompletionValidation:
    """Test that submitted completions validate in temp fixtures."""
    
    def test_workflow_td_submitted_completion_validates_in_temp_fixture(self):
        """Test Workflow TD submitted completion validates in temp fixture."""
        with TemporaryDirectory() as tmpdir:
            completion_root = Path(tmpdir)
            completion_root.mkdir(parents=True, exist_ok=True)
            
            completion = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "source_work_order": "workflow_td_identity_workflow_change_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "workflow_strategy_updated",
                "allowed_resolutions": ["workflow_strategy_updated", "missing_nodes_reported"],
                "required_outputs": ["updated_workflow_strategy", "workflow_audit"],
                "outputs_provided": {
                    "updated_workflow_strategy": {"strategy": "updated"},
                    "workflow_audit": {"audit": "complete"}
                },
                "current_required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False,
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            
            with open(completion_root / "workflow_td_identity_workflow_change.SUBMITTED.json", 'w') as f:
                json.dump(completion, f)
            
            work_order = {
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            
            result = validate_workflow_td_completion_submission(completion, work_order)
            
            assert result["valid"] is True
            assert result["is_complete"] is True
            assert len(result["rejection_reasons"]) == 0
    
    def test_character_director_submitted_completion_validates_in_temp_fixture(self):
        """Test Character Director submitted completion validates in temp fixture."""
        with TemporaryDirectory() as tmpdir:
            completion_root = Path(tmpdir)
            completion_root.mkdir(parents=True, exist_ok=True)
            
            completion = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "source_work_order": "character_director_reference_rebuild_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "reference_strategy_updated",
                "allowed_resolutions": ["reference_strategy_updated", "identity_rules_updated"],
                "required_outputs": ["updated_character_identity_rules", "updated_reference_strategy"],
                "outputs_provided": {
                    "updated_character_identity_rules": {"rules": "updated"},
                    "updated_reference_strategy": {"strategy": "updated"}
                },
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            
            with open(completion_root / "character_director_reference_rebuild.SUBMITTED.json", 'w') as f:
                json.dump(completion, f)
            
            work_order = {
                "blocked_shot": "shot01"
            }
            
            result = validate_character_director_completion_submission(completion, work_order)
            
            assert result["valid"] is True
            assert result["is_complete"] is True
            assert len(result["rejection_reasons"]) == 0
    
    def test_both_completed_submissions_return_submitted_completions_ready_true(self):
        """Test both completed submissions return submitted_completions_ready=true."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create submitted completions
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_completion = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "source_work_order": "workflow_td_identity_workflow_change_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "workflow_strategy_updated",
                "allowed_resolutions": ["workflow_strategy_updated"],
                "required_outputs": ["updated_workflow_strategy"],
                "outputs_provided": {"updated_workflow_strategy": {"strategy": "updated"}},
                "current_required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False,
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.SUBMITTED.json", 'w') as f:
                json.dump(workflow_completion, f)
            
            character_completion = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "source_work_order": "character_director_reference_rebuild_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "reference_strategy_updated",
                "allowed_resolutions": ["reference_strategy_updated"],
                "required_outputs": ["updated_character_identity_rules"],
                "outputs_provided": {"updated_character_identity_rules": {"rules": "updated"}},
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.SUBMITTED.json", 'w') as f:
                json.dump(character_completion, f)
            
            result = validate_submitted_change_request_completions(str(project_root))
            
            assert result["status"] == "valid"
            assert result["submitted_completions_ready"] is True
            assert result["valid_completions"] == 2
            assert result["ready_for_resubmission"] is True
            assert result["would_allow_new_role_decision_drafts"] is True
            assert result["execution_performed"] is True
            assert result["retry_gate_open"] is False
            assert result["production_accepted"] is False
            assert result["downstream_blocked"] is True
            assert result["real_project_mutated"] is False
    
    def test_valid_completions_do_not_open_retry_gate(self):
        """Test valid completions do not open retry gate."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create submitted completions
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_completion = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "source_work_order": "workflow_td_identity_workflow_change_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "workflow_strategy_updated",
                "allowed_resolutions": ["workflow_strategy_updated"],
                "required_outputs": ["updated_workflow_strategy"],
                "outputs_provided": {"updated_workflow_strategy": {"strategy": "updated"}},
                "current_required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False,
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.SUBMITTED.json", 'w') as f:
                json.dump(workflow_completion, f)
            
            character_completion = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "source_work_order": "character_director_reference_rebuild_order.json",
                "blocked_shot": "shot01",
                "completion_status": "submitted",
                "selected_resolution": "reference_strategy_updated",
                "allowed_resolutions": ["reference_strategy_updated"],
                "required_outputs": ["updated_character_identity_rules"],
                "outputs_provided": {"updated_character_identity_rules": {"rules": "updated"}},
                "execution_performed": True,
                "apply_performed": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.SUBMITTED.json", 'w') as f:
                json.dump(character_completion, f)
            
            result = validate_submitted_change_request_completions(str(project_root))
            
            assert result["retry_gate_open"] is False


class TestUnsafeCompletionRejection:
    """Test that unsafe completions are rejected."""
    
    def test_selected_resolution_outside_allowed_resolutions_is_rejected(self):
        """Test selected_resolution outside allowed_resolutions is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "invalid_resolution",
            "allowed_resolutions": ["workflow_strategy_updated", "missing_nodes_reported"]
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("selected_resolution_not_allowed" in r for r in result["rejection_reasons"])
    
    def test_missing_required_outputs_are_rejected(self):
        """Test missing required outputs are rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "required_outputs": ["updated_workflow_strategy", "workflow_audit"],
            "outputs_provided": {
                "updated_workflow_strategy": {"strategy": "updated"}
                # workflow_audit is missing
            }
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("missing_required_outputs" in r for r in result["rejection_reasons"])
    
    def test_production_accepted_true_is_rejected(self):
        """Test production_accepted=true is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "allowed_resolutions": ["workflow_strategy_updated"],
            "required_outputs": [],
            "outputs_provided": {},
            "production_accepted": True
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("production_accepted_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_retry_gate_open_true_is_rejected(self):
        """Test retry_gate_open=true is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "allowed_resolutions": ["workflow_strategy_updated"],
            "required_outputs": [],
            "outputs_provided": {},
            "retry_gate_open": True
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("retry_gate_open_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_apply_performed_true_is_rejected(self):
        """Test apply_performed=true is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "allowed_resolutions": ["workflow_strategy_updated"],
            "required_outputs": [],
            "outputs_provided": {},
            "apply_performed": True
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("apply_performed_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_legacy_reference_locked_workflow_is_rejected(self):
        """Test legacy_reference_locked workflow is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "allowed_resolutions": ["workflow_strategy_updated"],
            "required_outputs": [],
            "outputs_provided": {},
            "legacy_reference_locked_allowed_for_production": True
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("legacy_reference_locked_true_rejected" in r for r in result["rejection_reasons"])
    
    def test_non_gorynych_mode_is_rejected(self):
        """Test non-gorynych mode is rejected."""
        completion = {
            "completion_status": "submitted",
            "selected_resolution": "workflow_strategy_updated",
            "allowed_resolutions": ["workflow_strategy_updated"],
            "required_outputs": [],
            "outputs_provided": {},
            "current_required_generation_mode": "other_mode"
        }
        work_order = {"blocked_shot": "shot01"}
        
        result = validate_workflow_td_completion_submission(completion, work_order)
        
        assert result["valid"] is False
        assert any("generation_mode_not_gorynych" in r for r in result["rejection_reasons"])


class TestNoMutation:
    """Test that validation does not mutate project state."""
    
    def test_validation_does_not_mutate_project(self):
        """Test validation does not mutate project."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Read original state
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'r') as f:
                original_workflow = json.load(f)
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'r') as f:
                original_character = json.load(f)
            
            # Run validation
            validate_submitted_change_request_completions(str(project_root))
            
            # Verify files unchanged
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'r') as f:
                after_workflow = json.load(f)
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'r') as f:
                after_character = json.load(f)
            
            assert original_workflow == after_workflow
            assert original_character == after_character
    
    def test_role_decisions_remain_pending(self):
        """Test role_decisions remain pending after validation."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run validation
            result = validate_submitted_change_request_completions(str(project_root))
            
            # Verify result indicates role_decisions remain pending
            assert result["ready_for_resubmission"] is False
            assert result["retry_gate_open"] is False
            assert result["production_accepted"] is False
    
    def test_retry_gate_remains_closed(self):
        """Test retry_gate remains closed after validation."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run validation
            result = validate_submitted_change_request_completions(str(project_root))
            
            # Verify retry gate remains closed
            assert result["retry_gate_open"] is False
    
    def test_production_accepted_remains_false(self):
        """Test production_accepted remains false after validation."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run validation
            result = validate_submitted_change_request_completions(str(project_root))
            
            # Verify production_accepted remains false
            assert result["production_accepted"] is False
    
    def test_downstream_blocked_remains_true(self):
        """Test downstream_blocked remains true after validation."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create blank completion templates
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template",
                "selected_resolution": None,
                "execution_performed": False,
                "ready_for_resubmission": False,
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run validation
            result = validate_submitted_change_request_completions(str(project_root))
            
            # Verify downstream_blocked remains true
            assert result["downstream_blocked"] is True


class TestCompareCompletionAgainstContract:
    """Test compare_completion_against_contract function."""
    
    def test_compare_completion_against_contract_compliant(self):
        """Test compare_completion_against_contract with compliant completion."""
        completion = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "required_generation_mode": "gorynych_identity"
        }
        work_order = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "required_generation_mode": "gorynych_identity"
        }
        
        result = compare_completion_against_contract(completion, work_order)
        
        assert result["contract_compliant"] is True
        assert len(result["mismatches"]) == 0
    
    def test_compare_completion_against_contract_non_compliant(self):
        """Test compare_completion_against_contract with non-compliant completion."""
        completion = {
            "role": "Different Role",
            "blocked_shot": "shot02",
            "required_generation_mode": "other_mode"
        }
        work_order = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "required_generation_mode": "gorynych_identity"
        }
        
        result = compare_completion_against_contract(completion, work_order)
        
        assert result["contract_compliant"] is False
        assert len(result["mismatches"]) > 0
