"""
Tests for RC2-PRODCARDS2V — Change Request Execution Plan, No Execution

Tests that unresolved change request work orders have concrete execution plans,
execution_status remains planned, execution_performed remains false,
completion_submission_allowed remains false, retry gate remains closed,
role_decisions remain pending, production_accepted remains false,
downstream remains blocked, and no completion/apply/generation/downstream
action executes.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.change_request_execution_plan import (
    create_workflow_td_execution_plan,
    create_character_director_execution_plan,
    create_change_request_execution_plan,
    validate_change_request_execution_plan,
)


class TestCreateWorkflowTDExecutionPlan:
    """Test creating Workflow TD execution plan."""
    
    def test_creates_workflow_td_execution_plan(self):
        """Test creates Workflow TD execution plan."""
        work_order = {
            "work_order_type": "workflow_change_order",
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "revise_identity_workflow_strategy",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False
        }
        completion_template = {
            "completion_type": "workflow_change_completion",
            "role": "Workflow TD / ComfyUI Technical Director"
        }
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["plan_type"] == "workflow_td_change_request_execution_plan"
        assert plan["role"] == "Workflow TD / ComfyUI Technical Director"
        assert plan["source_work_order"] == "workflow_td_identity_workflow_change_order.json"
        assert plan["source_completion_template"] == "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
        assert plan["blocked_shot"] == "shot01"
    
    def test_execution_status_planned(self):
        """Test execution_status=planned."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["execution_status"] == "planned"
    
    def test_execution_performed_false(self):
        """Test execution_performed=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["execution_performed"] is False
    
    def test_requires_gorynych_identity(self):
        """Test Workflow TD plan requires gorynych_identity."""
        work_order = {
            "required_generation_mode": "gorynych_identity"
        }
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["required_generation_mode"] == "gorynych_identity"
    
    def test_rejects_legacy_reference_locked_production_path(self):
        """Test Workflow TD plan rejects legacy_reference_locked production path."""
        work_order = {
            "legacy_reference_locked_allowed_for_production": False
        }
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["legacy_reference_locked_allowed_for_production"] is False
    
    def test_includes_planned_steps(self):
        """Test Workflow TD plan includes planned steps."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert "audit_current_identity_workflow_strategy" in plan["planned_steps"]
        assert "verify_required_nodes" in plan["planned_steps"]
        assert "verify_required_models" in plan["planned_steps"]
        assert "define_updated_workflow_strategy" in plan["planned_steps"]
        assert "define_preflight_requirements" in plan["planned_steps"]
        assert "define_output_collection_contract" in plan["planned_steps"]
    
    def test_includes_required_outputs(self):
        """Test Workflow TD plan includes required outputs."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert "updated_workflow_strategy" in plan["required_outputs_before_completion"]
        assert "workflow_audit" in plan["required_outputs_before_completion"]
        assert "required_nodes" in plan["required_outputs_before_completion"]
        assert "required_models" in plan["required_outputs_before_completion"]
        assert "preflight_result" in plan["required_outputs_before_completion"]
        assert "output_collection_contract" in plan["required_outputs_before_completion"]
    
    def test_completion_submission_allowed_false(self):
        """Test completion_submission_allowed=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["completion_submission_allowed"] is False
    
    def test_retry_gate_open_false(self):
        """Test retry_gate_open=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test production_accepted=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test downstream_blocked=true."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_workflow_td_execution_plan(work_order, completion_template)
        
        assert plan["downstream_blocked"] is True


class TestCreateCharacterDirectorExecutionPlan:
    """Test creating Character Director execution plan."""
    
    def test_creates_character_director_execution_plan(self):
        """Test creates Character Director execution plan."""
        work_order = {
            "work_order_type": "reference_rebuild_order",
            "role": "Character Director",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "rebuild_or_update_identity_reference_strategy"
        }
        completion_template = {
            "completion_type": "reference_rebuild_completion",
            "role": "Character Director"
        }
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["plan_type"] == "character_director_reference_rebuild_execution_plan"
        assert plan["role"] == "Character Director"
        assert plan["source_work_order"] == "character_director_reference_rebuild_order.json"
        assert plan["source_completion_template"] == "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
        assert plan["blocked_shot"] == "shot01"
    
    def test_execution_status_planned(self):
        """Test execution_status=planned."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["execution_status"] == "planned"
    
    def test_execution_performed_false(self):
        """Test execution_performed=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["execution_performed"] is False
    
    def test_includes_planned_steps(self):
        """Test Character Director plan includes planned steps."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert "review_identity_failure_evidence" in plan["planned_steps"]
        assert "review_current_character_identity_rules" in plan["planned_steps"]
        assert "define_updated_reference_strategy" in plan["planned_steps"]
        assert "define_identity_acceptance_criteria" in plan["planned_steps"]
        assert "write_reference_rebuild_notes" in plan["planned_steps"]
    
    def test_includes_required_outputs(self):
        """Test Character Director plan includes required outputs."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert "updated_character_identity_rules" in plan["required_outputs_before_completion"]
        assert "updated_reference_strategy" in plan["required_outputs_before_completion"]
        assert "identity_acceptance_criteria" in plan["required_outputs_before_completion"]
        assert "reference_rebuild_notes" in plan["required_outputs_before_completion"]
    
    def test_completion_submission_allowed_false(self):
        """Test completion_submission_allowed=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["completion_submission_allowed"] is False
    
    def test_retry_gate_open_false(self):
        """Test retry_gate_open=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test production_accepted=false."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test downstream_blocked=true."""
        work_order = {"blocked_shot": "shot01"}
        completion_template = {}
        
        plan = create_character_director_execution_plan(work_order, completion_template)
        
        assert plan["downstream_blocked"] is True


class TestCreateChangeRequestExecutionPlan:
    """Test creating change request execution plans."""
    
    def test_creates_execution_plans_based_on_work_orders(self):
        """Test execution plans are based on change request work orders."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            
            # Create work orders
            work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
            work_orders_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_order = {
                "work_order_type": "workflow_change_order",
                "role": "Workflow TD / ComfyUI Technical Director",
                "blocked_shot": "shot01",
                "reason": "identity_qa_failed",
                "required_generation_mode": "gorynych_identity",
                "legacy_reference_locked_allowed_for_production": False
            }
            with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
                json.dump(workflow_order, f)
            
            character_order = {
                "work_order_type": "reference_rebuild_order",
                "role": "Character Director",
                "blocked_shot": "shot01",
                "reason": "identity_qa_failed"
            }
            with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
                json.dump(character_order, f)
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            result = create_change_request_execution_plan(str(project_root))
            
            assert result["execution_plans_created"] == 2
            assert result["execution_performed"] is False
            assert result["completion_submission_allowed"] is False
    
    def test_execution_plans_reference_completion_templates(self):
        """Test execution plans reference completion templates."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            create_change_request_execution_plan(str(project_root))
            
            # Verify plans reference completion templates
            execution_plan_dir = project_root / "output" / "control" / "change_request_execution_plan"
            workflow_plan_path = execution_plan_dir / "workflow_td_identity_workflow_execution_plan.json"
            with open(workflow_plan_path, 'r') as f:
                workflow_plan = json.load(f)
            
            assert workflow_plan["source_completion_template"] == "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
    
    def test_creates_execution_plan_summary(self):
        """Test creates CHANGE_REQUEST_EXECUTION_PLAN.md."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            create_change_request_execution_plan(str(project_root))
            
            # Verify summary file exists
            execution_plan_dir = project_root / "output" / "control" / "change_request_execution_plan"
            summary_path = execution_plan_dir / "CHANGE_REQUEST_EXECUTION_PLAN.md"
            assert summary_path.exists()
            
            # Verify summary content
            with open(summary_path, 'r') as f:
                summary = f.read()
            
            assert "Change Request Execution Plan" in summary
            assert "Unresolved Work Orders" in summary
            assert "Planned Steps" in summary
            assert "Required Outputs Before Completion" in summary
            assert "Why Execution Remains Planned" in summary


class TestNoMutation:
    """Test that execution plan creation does not mutate project state."""
    
    def test_plans_do_not_modify_role_decisions(self):
        """Test plans do not modify role_decisions/."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Create role_decisions directory (should remain unchanged)
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            role_decisions_dir.mkdir(parents=True, exist_ok=True)
            
            # Run execution plan creation
            create_change_request_execution_plan(str(project_root))
            
            # Verify role_decisions directory exists but is empty (no files created)
            assert role_decisions_dir.exists()
            assert len(list(role_decisions_dir.iterdir())) == 0
    
    def test_plans_do_not_submit_completions(self):
        """Test plans do not submit completions."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director",
                "completion_status": "template"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director",
                "completion_status": "template"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run execution plan creation
            create_change_request_execution_plan(str(project_root))
            
            # Verify no .SUBMITTED.json files were created
            submitted_files = list(completions_dir.glob("*.SUBMITTED.json"))
            assert len(submitted_files) == 0
            
            # Verify templates remain unchanged
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'r') as f:
                workflow_template_after = json.load(f)
            assert workflow_template_after["completion_status"] == "template"
    
    def test_plans_do_not_open_retry_gate(self):
        """Test plans do not open retry gate."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Create artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            artifact_index = {
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            artifact_index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(artifact_index_path, 'w') as f:
                json.dump(artifact_index, f)
            
            # Run execution plan creation
            result = create_change_request_execution_plan(str(project_root))
            
            # Verify retry gate remains closed
            assert result["retry_gate_open"] is False
            
            # Verify artifact index still has retry_gate_open=false
            with open(artifact_index_path, 'r') as f:
                artifact_index_after = json.load(f)
            assert artifact_index_after["retry_gate_open"] is False
    
    def test_plans_keep_production_accepted_false(self):
        """Test plans keep production_accepted=false."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run execution plan creation
            result = create_change_request_execution_plan(str(project_root))
            
            # Verify production_accepted remains false
            assert result["production_accepted"] is False
    
    def test_plans_keep_downstream_blocked_true(self):
        """Test plans keep downstream_blocked=true."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run execution plan creation
            result = create_change_request_execution_plan(str(project_root))
            
            # Verify downstream_blocked remains true
            assert result["downstream_blocked"] is True


class TestArtifactIndexAndEpisodeLedger:
    """Test artifact_index and episode_ledger updates."""
    
    def test_artifact_index_records_passive_execution_plan_section_only(self):
        """Test artifact_index records passive execution plan section only."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Create artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            artifact_index = {
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True
            }
            artifact_index_path.parent.mkdir(parents=True, exist_ok=True)
            with open(artifact_index_path, 'w') as f:
                json.dump(artifact_index, f)
            
            # Run execution plan creation
            create_change_request_execution_plan(str(project_root))
            
            # Verify artifact_index has passive execution plan section
            with open(artifact_index_path, 'r') as f:
                artifact_index_after = json.load(f)
            
            assert "change_request_execution_plan" in artifact_index_after
            assert artifact_index_after["change_request_execution_plan"]["status"] == "created"
            assert artifact_index_after["change_request_execution_plan"]["execution_plans_created"] == 2
            assert artifact_index_after["change_request_execution_plan"]["execution_performed"] is False
            assert artifact_index_after["change_request_execution_plan"]["completion_submission_allowed"] is False
            assert artifact_index_after["change_request_execution_plan"]["ready_for_resubmission"] is False
            assert artifact_index_after["change_request_execution_plan"]["retry_gate_open"] is False
            assert artifact_index_after["change_request_execution_plan"]["production_accepted"] is False
            assert artifact_index_after["change_request_execution_plan"]["downstream_blocked"] is True
    
    def test_episode_ledger_records_change_request_execution_plan_created(self):
        """Test episode_ledger records change_request_execution_plan_created."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Run execution plan creation
            create_change_request_execution_plan(str(project_root))
            
            # Verify episode_ledger has event
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert len(ledger["events"]) > 0
            latest_event = ledger["events"][-1]
            assert latest_event["event_type"] == "change_request_execution_plan_created"
            assert latest_event["execution_plans_created"] == 2
            assert latest_event["execution_performed"] is False
            assert latest_event["completion_submission_allowed"] is False
            assert latest_event["ready_for_resubmission"] is False
            assert latest_event["retry_gate_open"] is False
            assert latest_event["production_accepted"] is False
            assert latest_event["downstream_blocked"] is True
            assert latest_event["comfyui_generation"] is False
            assert latest_event["pipeline_action_rerun"] is False


class TestValidateChangeRequestExecutionPlan:
    """Test validating change request execution plans."""
    
    def test_validates_execution_plan_structure(self):
        """Test validates execution plan structure."""
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
            
            # Create completion contracts
            completions_dir = project_root / "output" / "control" / "change_request_completions"
            completions_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_template = {
                "completion_type": "workflow_change_completion",
                "role": "Workflow TD / ComfyUI Technical Director"
            }
            with open(completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(workflow_template, f)
            
            character_template = {
                "completion_type": "reference_rebuild_completion",
                "role": "Character Director"
            }
            with open(completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json", 'w') as f:
                json.dump(character_template, f)
            
            # Create execution plans
            create_change_request_execution_plan(str(project_root))
            
            # Validate execution plans
            result = validate_change_request_execution_plan(str(project_root))
            
            assert result["status"] == "valid"
            assert result["execution_plans_found"] == 2
            assert result["execution_performed"] is False
            assert result["completion_submission_allowed"] is False
            assert result["ready_for_resubmission"] is False
            assert result["retry_gate_open"] is False
            assert result["production_accepted"] is False
            assert result["downstream_blocked"] is True
