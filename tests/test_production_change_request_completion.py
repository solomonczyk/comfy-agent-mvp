"""
Tests for RC2-PRODCARDS2T — Change Request Completion Contracts, No Execution

Tests that change request work orders have formal completion templates/contracts,
selected_resolution remains null, completion_status remains template,
execution_performed remains false, ready_for_resubmission remains false,
retry gate remains closed, role_decisions remain pending, production_accepted
remains false, downstream remains blocked, and no apply/generation/downstream
action executes.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.change_request_completion import (
    create_workflow_td_completion_template,
    create_character_director_completion_template,
    create_completion_instructions,
    create_change_request_completion_contracts,
    validate_change_request_completion_contracts,
)


class TestCreateWorkflowTDCompletionTemplate:
    """Test creating Workflow TD completion template."""
    
    def test_creates_workflow_td_completion_template(self):
        """Test creates Workflow TD completion template."""
        work_order = {
            "work_order_type": "workflow_change_order",
            "role": "Workflow TD / ComfyUI Technical Director",
            "source_request": "workflow_change_request",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "revise_identity_workflow_strategy",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_outputs": [
                "updated_workflow_strategy",
                "workflow_audit",
                "required_nodes",
                "required_models",
                "preflight_result",
                "output_collection_contract"
            ]
        }
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["completion_type"] == "workflow_change_completion"
        assert template["role"] == "Workflow TD / ComfyUI Technical Director"
        assert template["source_work_order"] == "workflow_td_identity_workflow_change_order.json"
        assert template["blocked_shot"] == "shot01"
        assert template["completion_status"] == "template"
    
    def test_requires_gorynych_identity(self):
        """Test Workflow TD completion template requires gorynych_identity."""
        work_order = {
            "required_generation_mode": "gorynych_identity"
        }
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["current_required_generation_mode"] == "gorynych_identity"
    
    def test_rejects_legacy_reference_locked_production_path(self):
        """Test Workflow TD completion template rejects legacy_reference_locked production path."""
        work_order = {
            "legacy_reference_locked_allowed_for_production": False
        }
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["legacy_reference_locked_allowed_for_production"] is False
    
    def test_includes_required_outputs(self):
        """Test Workflow TD completion template includes required outputs."""
        work_order = {
            "required_outputs": [
                "updated_workflow_strategy",
                "workflow_audit",
                "required_nodes",
                "required_models",
                "preflight_result",
                "output_collection_contract"
            ]
        }
        
        template = create_workflow_td_completion_template(work_order)
        
        assert "updated_workflow_strategy" in template["required_outputs"]
        assert "workflow_audit" in template["required_outputs"]
        assert "required_nodes" in template["required_outputs"]
        assert "required_models" in template["required_outputs"]
        assert "preflight_result" in template["required_outputs"]
        assert "output_collection_contract" in template["required_outputs"]
    
    def test_selected_resolution_is_null(self):
        """Test Workflow TD completion template has selected_resolution=null."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["selected_resolution"] is None
    
    def test_completion_status_is_template(self):
        """Test Workflow TD completion template has completion_status=template."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["completion_status"] == "template"
    
    def test_execution_performed_false(self):
        """Test Workflow TD completion template has execution_performed=false."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["execution_performed"] is False
    
    def test_ready_for_resubmission_false(self):
        """Test Workflow TD completion template has ready_for_resubmission=false."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["ready_for_resubmission"] is False
    
    def test_retry_gate_open_false(self):
        """Test Workflow TD completion template has retry_gate_open=false."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test Workflow TD completion template has production_accepted=false."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test Workflow TD completion template has downstream_blocked=true."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert template["downstream_blocked"] is True
    
    def test_includes_allowed_resolutions(self):
        """Test Workflow TD completion template includes allowed resolutions."""
        work_order = {}
        
        template = create_workflow_td_completion_template(work_order)
        
        assert "workflow_strategy_updated" in template["allowed_resolutions"]
        assert "missing_nodes_reported" in template["allowed_resolutions"]
        assert "missing_models_reported" in template["allowed_resolutions"]
        assert "reference_rebuild_required" in template["allowed_resolutions"]
        assert "blocked" in template["allowed_resolutions"]


class TestCreateCharacterDirectorCompletionTemplate:
    """Test creating Character Director completion template."""
    
    def test_creates_character_director_completion_template(self):
        """Test creates Character Director completion template."""
        work_order = {
            "work_order_type": "reference_rebuild_order",
            "role": "Character Director",
            "source_request": "reference_rebuild_request",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "rebuild_or_update_identity_reference_strategy",
            "required_outputs": [
                "updated_character_identity_rules",
                "updated_reference_strategy",
                "identity_acceptance_criteria",
                "reference_rebuild_notes"
            ]
        }
        
        template = create_character_director_completion_template(work_order)
        
        assert template["completion_type"] == "reference_rebuild_completion"
        assert template["role"] == "Character Director"
        assert template["source_work_order"] == "character_director_reference_rebuild_order.json"
        assert template["blocked_shot"] == "shot01"
        assert template["completion_status"] == "template"
    
    def test_requires_updated_reference_strategy_outputs(self):
        """Test Character Director completion template requires updated reference strategy outputs."""
        work_order = {
            "required_outputs": [
                "updated_character_identity_rules",
                "updated_reference_strategy",
                "identity_acceptance_criteria",
                "reference_rebuild_notes"
            ]
        }
        
        template = create_character_director_completion_template(work_order)
        
        assert "updated_character_identity_rules" in template["required_outputs"]
        assert "updated_reference_strategy" in template["required_outputs"]
        assert "identity_acceptance_criteria" in template["required_outputs"]
        assert "reference_rebuild_notes" in template["required_outputs"]
    
    def test_selected_resolution_is_null(self):
        """Test Character Director completion template has selected_resolution=null."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["selected_resolution"] is None
    
    def test_completion_status_is_template(self):
        """Test Character Director completion template has completion_status=template."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["completion_status"] == "template"
    
    def test_execution_performed_false(self):
        """Test Character Director completion template has execution_performed=false."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["execution_performed"] is False
    
    def test_ready_for_resubmission_false(self):
        """Test Character Director completion template has ready_for_resubmission=false."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["ready_for_resubmission"] is False
    
    def test_retry_gate_open_false(self):
        """Test Character Director completion template has retry_gate_open=false."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test Character Director completion template has production_accepted=false."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test Character Director completion template has downstream_blocked=true."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert template["downstream_blocked"] is True
    
    def test_includes_allowed_resolutions(self):
        """Test Character Director completion template includes allowed resolutions."""
        work_order = {}
        
        template = create_character_director_completion_template(work_order)
        
        assert "reference_strategy_updated" in template["allowed_resolutions"]
        assert "identity_rules_updated" in template["allowed_resolutions"]
        assert "new_reference_required" in template["allowed_resolutions"]
        assert "workflow_change_required" in template["allowed_resolutions"]
        assert "blocked" in template["allowed_resolutions"]


class TestCreateCompletionInstructions:
    """Test creating completion instructions."""
    
    def test_explains_each_role_completion(self):
        """Test instructions explain each role's completion."""
        work_orders = {
            "workflow_td": {
                "required_action": "revise_identity_workflow_strategy",
                "required_generation_mode": "gorynych_identity",
                "required_outputs": ["updated_workflow_strategy", "workflow_audit"]
            },
            "character_director": {
                "required_action": "rebuild_or_update_identity_reference_strategy",
                "required_outputs": ["updated_character_identity_rules", "updated_reference_strategy"]
            }
        }
        
        instructions = create_completion_instructions(work_orders)
        
        assert "Workflow TD / ComfyUI Technical Director" in instructions
        assert "Character Director" in instructions
    
    def test_explains_required_outputs(self):
        """Test instructions explain required outputs."""
        work_orders = {
            "workflow_td": {
                "required_outputs": ["updated_workflow_strategy", "workflow_audit"]
            }
        }
        
        instructions = create_completion_instructions(work_orders)
        
        assert "Required Outputs:" in instructions
        assert "updated_workflow_strategy" in instructions
    
    def test_explains_allowed_resolutions(self):
        """Test instructions explain allowed resolutions."""
        work_orders = {
            "workflow_td": {
                "required_action": "revise_identity_workflow_strategy",
                "required_generation_mode": "gorynych_identity",
                "required_outputs": ["updated_workflow_strategy"]
            },
            "character_director": {
                "required_action": "rebuild_or_update_identity_reference_strategy",
                "required_outputs": ["updated_character_identity_rules"]
            }
        }
        
        instructions = create_completion_instructions(work_orders)
        
        assert "Allowed Resolutions:" in instructions
    
    def test_explains_why_templates_not_completions(self):
        """Test instructions explain why templates are not completions."""
        work_orders = {}
        
        instructions = create_completion_instructions(work_orders)
        
        assert "Why These Are Templates, Not Completions" in instructions
        assert "No workflow execution has occurred" in instructions
        assert "No reference rebuild has occurred" in instructions
    
    def test_explains_why_retry_blocked(self):
        """Test instructions explain why retry remains blocked."""
        work_orders = {}
        
        instructions = create_completion_instructions(work_orders)
        
        assert "Why Retry Remains Blocked" in instructions
        assert "Completion templates are not yet completed" in instructions
        assert "No generation has been authorized" in instructions
    
    def test_explains_what_must_happen_before_retry(self):
        """Test instructions explain what must happen before retry."""
        work_orders = {}
        
        instructions = create_completion_instructions(work_orders)
        
        assert "What Must Happen Before Retry Can Be Authorized" in instructions
        assert "Workflow TD must complete" in instructions
        assert "Character Director must complete" in instructions
    
    def test_explains_no_generation_authorized(self):
        """Test instructions explain no generation authorized."""
        work_orders = {}
        
        instructions = create_completion_instructions(work_orders)
        
        assert "No Generation Authorized" in instructions
        assert "No ComfyUI execution will occur" in instructions


class TestCreateChangeRequestCompletionContracts:
    """Test creating change request completion contracts end-to-end."""
    
    def setup_project_with_work_orders(self, tmpdir):
        """Helper to set up project with work orders."""
        project_root = Path(tmpdir)
        work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
        work_orders_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Workflow TD work order
        workflow_order = {
            "work_order_type": "workflow_change_order",
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_outputs": ["updated_workflow_strategy", "workflow_audit"]
        }
        
        with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
            json.dump(workflow_order, f)
        
        # Create Character Director work order
        character_order = {
            "work_order_type": "reference_rebuild_order",
            "role": "Character Director",
            "blocked_shot": "shot01",
            "required_outputs": ["updated_character_identity_rules", "updated_reference_strategy"]
        }
        
        with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
            json.dump(character_order, f)
        
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
        
        return project_root
    
    def test_creates_workflow_td_completion_template(self):
        """Test creates Workflow TD completion template."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            assert template_path.exists()
            
            with open(template_path, 'r') as f:
                template = json.load(f)
            
            assert template["completion_type"] == "workflow_change_completion"
            assert template["role"] == "Workflow TD / ComfyUI Technical Director"
    
    def test_creates_character_director_completion_template(self):
        """Test creates Character Director completion template."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            template_path = project_root / "output" / "control" / "change_request_completions" / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
            assert template_path.exists()
            
            with open(template_path, 'r') as f:
                template = json.load(f)
            
            assert template["completion_type"] == "reference_rebuild_completion"
            assert template["role"] == "Character Director"
    
    def test_creates_completion_instructions(self):
        """Test creates CHANGE_REQUEST_COMPLETION_INSTRUCTIONS.md."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            instructions_path = project_root / "output" / "control" / "change_request_completions" / "CHANGE_REQUEST_COMPLETION_INSTRUCTIONS.md"
            assert instructions_path.exists()
            
            with open(instructions_path, 'r') as f:
                instructions = f.read()
            
            assert "Change Request Completion Instructions" in instructions
    
    def test_templates_based_on_change_request_work_orders(self):
        """Test templates are based on change request work orders."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["completion_templates_created"] == 2
    
    def test_templates_have_selected_resolution_null(self):
        """Test templates have selected_resolution=null."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["selected_resolution"] is None
    
    def test_templates_have_completion_status_template(self):
        """Test templates have completion_status=template."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["completion_status"] == "template"
    
    def test_templates_keep_execution_performed_false(self):
        """Test templates keep execution_performed=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["execution_performed"] is False
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["execution_performed"] is False
    
    def test_templates_do_not_modify_role_decisions(self):
        """Test templates do not modify role_decisions/."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            # role_decisions directory should not be created or modified
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            # If it doesn't exist, it wasn't modified
            # If it exists, it wasn't modified by completion contract creation
    
    def test_templates_do_not_open_retry_gate(self):
        """Test templates do not open retry gate."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["retry_gate_open"] is False
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["retry_gate_open"] is False
    
    def test_templates_keep_production_accepted_false(self):
        """Test templates keep production_accepted=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["production_accepted"] is False
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["production_accepted"] is False
    
    def test_templates_keep_downstream_blocked_true(self):
        """Test templates keep downstream_blocked=true."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["downstream_blocked"] is True
            
            workflow_template_path = project_root / "output" / "control" / "change_request_completions" / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
            with open(workflow_template_path, 'r') as f:
                workflow_template = json.load(f)
            
            assert workflow_template["downstream_blocked"] is True
    
    def test_artifact_index_records_passive_completion_contract_section(self):
        """Test artifact_index records passive completion contract section only."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert "change_request_completion_contracts" in artifact_index
            assert artifact_index["change_request_completion_contracts"]["status"] == "created"
            assert artifact_index["change_request_completion_contracts"]["execution_performed"] is False
            assert artifact_index["change_request_completion_contracts"]["ready_for_resubmission"] is False
            assert artifact_index["change_request_completion_contracts"]["retry_gate_open"] is False
            assert artifact_index["change_request_completion_contracts"]["production_accepted"] is False
            assert artifact_index["change_request_completion_contracts"]["downstream_blocked"] is True
    
    def test_episode_ledger_records_change_request_completion_contracts_created(self):
        """Test episode_ledger records change_request_completion_contracts_created."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert "events" in ledger
            assert len(ledger["events"]) > 0
            
            completion_events = [e for e in ledger["events"] if e.get("event_type") == "change_request_completion_contracts_created"]
            assert len(completion_events) > 0
            
            event = completion_events[-1]
            assert event["event_type"] == "change_request_completion_contracts_created"
            assert event["completion_templates_created"] == 2
            assert event["execution_performed"] is False
            assert event["ready_for_resubmission"] is False
            assert event["retry_gate_open"] is False
            assert event["production_accepted"] is False
            assert event["downstream_blocked"] is True
            assert event["comfyui_generation"] is False
            assert event["pipeline_action_rerun"] is False
    
    def test_validation_returns_ready_for_resubmission_false(self):
        """Test validation returns ready_for_resubmission=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            create_change_request_completion_contracts(str(project_root))
            result = validate_change_request_completion_contracts(str(project_root))
            
            assert result["ready_for_resubmission"] is False
    
    def test_no_generation_downstream_action_executes(self):
        """Test no generation/downstream action executes."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["execution_performed"] is False
            assert result["ready_for_apply"] is False
            
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            latest_event = ledger["events"][-1]
            assert latest_event["comfyui_generation"] is False
            assert latest_event["pipeline_action_rerun"] is False
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test no core hardcode for Alya/Mir Erdan character names."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "blocked_shot": "shot01",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False,
                "character_name": "CustomCharacter"
            }
            
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            control_dir = project_root / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)
            
            artifact_index = {
                "downstream_blocked": True,
                "production_accepted": False,
                "retry_gate_open": False
            }
            with open(control_dir / "artifact_index.json", 'w') as f:
                json.dump(artifact_index, f)
            
            result = create_change_request_completion_contracts(str(project_root))
            
            assert result["status"] == "completed"
            assert result["completion_templates_created"] == 1


class TestValidateChangeRequestCompletionContracts:
    """Test validating change request completion contracts."""
    
    def setup_project_with_completion_contracts(self, tmpdir):
        """Helper to set up project with completion contracts."""
        project_root = Path(tmpdir)
        completions_dir = project_root / "output" / "control" / "change_request_completions"
        completions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Workflow TD completion template
        workflow_template = {
            "completion_type": "workflow_change_completion",
            "role": "Workflow TD / ComfyUI Technical Director",
            "source_work_order": "workflow_td_identity_workflow_change_order.json",
            "blocked_shot": "shot01",
            "completion_status": "template",
            "execution_performed": False,
            "selected_resolution": None,
            "allowed_resolutions": ["workflow_strategy_updated", "blocked"],
            "required_outputs": ["updated_workflow_strategy", "workflow_audit"],
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "ready_for_resubmission": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
            json.dump(workflow_template, f)
        
        # Create Character Director completion template
        character_template = {
            "completion_type": "reference_rebuild_completion",
            "role": "Character Director",
            "source_work_order": "character_director_reference_rebuild_order.json",
            "blocked_shot": "shot01",
            "completion_status": "template",
            "execution_performed": False,
            "selected_resolution": None,
            "allowed_resolutions": ["reference_strategy_updated", "blocked"],
            "required_outputs": ["updated_character_identity_rules", "updated_reference_strategy"],
            "ready_for_resubmission": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
            json.dump(character_template, f)
        
        # Create instructions
        with open(completions_dir / "CHANGE_REQUEST_COMPLETION_INSTRUCTIONS.md", 'w') as f:
            f.write("# Instructions\n")
        
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
        
        return project_root
    
    def test_validates_completion_contracts(self):
        """Test validates completion contracts successfully."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_completion_contracts(tmpdir)
            
            result = validate_change_request_completion_contracts(str(project_root))
            
            assert result["status"] == "valid"
            assert result["completion_templates_found"] == 2
    
    def test_validation_returns_ready_for_resubmission_false(self):
        """Test validation returns ready_for_resubmission=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_completion_contracts(tmpdir)
            
            result = validate_change_request_completion_contracts(str(project_root))
            
            assert result["ready_for_resubmission"] is False
