"""
Tests for RC2-PRODCARDS2S — Change Request Work Orders, No Execution

Tests that routed decision change requests are converted into concrete Workflow TD
and Character Director work orders without executing workflow changes, rebuilding
references, applying decisions, or opening retry generation.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.change_request_work_orders import (
    create_workflow_td_change_work_order,
    create_character_director_reference_rebuild_work_order,
    create_work_order_summary,
    create_change_request_work_orders,
    validate_change_request_work_orders,
)


class TestCreateWorkflowTDChangeWorkOrder:
    """Test creating Workflow TD workflow change work order."""
    
    def test_creates_workflow_td_work_order(self):
        """Test creates Workflow TD workflow change work order."""
        route = {
            "request_type": "workflow_change_request",
            "source_role": "Character Director",
            "source_decision": "request_workflow_change",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "target_role": "Workflow TD / ComfyUI Technical Director",
            "recommended_action": "revise_identity_workflow_strategy",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["work_order_type"] == "workflow_change_order"
        assert work_order["role"] == "Workflow TD / ComfyUI Technical Director"
        assert work_order["source_request"] == "workflow_change_request"
        assert work_order["source_decision"] == "request_workflow_change"
        assert work_order["blocked_shot"] == "shot01"
        assert work_order["reason"] == "identity_qa_failed"
        assert work_order["required_action"] == "revise_identity_workflow_strategy"
    
    def test_requires_gorynych_identity(self):
        """Test Workflow TD work order requires gorynych_identity."""
        route = {
            "request_type": "workflow_change_request",
            "required_generation_mode": "gorynych_identity"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["required_generation_mode"] == "gorynych_identity"
    
    def test_rejects_legacy_reference_locked_production_path(self):
        """Test Workflow TD work order rejects legacy_reference_locked production path."""
        route = {
            "request_type": "workflow_change_request",
            "legacy_reference_locked_allowed_for_production": False
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["legacy_reference_locked_allowed_for_production"] is False
    
    def test_includes_required_outputs(self):
        """Test Workflow TD work order includes required outputs."""
        route = {
            "request_type": "workflow_change_request"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert "updated_workflow_strategy" in work_order["required_outputs"]
        assert "workflow_audit" in work_order["required_outputs"]
        assert "required_nodes" in work_order["required_outputs"]
        assert "required_models" in work_order["required_outputs"]
        assert "preflight_result" in work_order["required_outputs"]
        assert "output_collection_contract" in work_order["required_outputs"]
    
    def test_execution_performed_false(self):
        """Test Workflow TD work order has execution_performed=false."""
        route = {
            "request_type": "workflow_change_request"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["execution_performed"] is False
    
    def test_retry_gate_open_false(self):
        """Test Workflow TD work order has retry_gate_open=false."""
        route = {
            "request_type": "workflow_change_request"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test Workflow TD work order has production_accepted=false."""
        route = {
            "request_type": "workflow_change_request"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test Workflow TD work order has downstream_blocked=true."""
        route = {
            "request_type": "workflow_change_request"
        }
        
        work_order = create_workflow_td_change_work_order(route)
        
        assert work_order["downstream_blocked"] is True


class TestCreateCharacterDirectorReferenceRebuildWorkOrder:
    """Test creating Character Director reference rebuild work order."""
    
    def test_creates_character_director_work_order(self):
        """Test creates Character Director reference rebuild work order."""
        route = {
            "request_type": "reference_rebuild_request",
            "source_role": "Workflow TD / ComfyUI Technical Director",
            "source_decision": "request_reference_rebuild",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "target_role": "Character Director",
            "recommended_action": "rebuild_or_update_identity_reference_strategy",
            "required_generation_mode": "gorynych_identity"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert work_order["work_order_type"] == "reference_rebuild_order"
        assert work_order["role"] == "Character Director"
        assert work_order["source_request"] == "reference_rebuild_request"
        assert work_order["source_decision"] == "request_reference_rebuild"
        assert work_order["blocked_shot"] == "shot01"
        assert work_order["reason"] == "identity_qa_failed"
        assert work_order["required_action"] == "rebuild_or_update_identity_reference_strategy"
    
    def test_requires_updated_reference_strategy_outputs(self):
        """Test Character Director work order requires updated reference strategy outputs."""
        route = {
            "request_type": "reference_rebuild_request"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert "updated_character_identity_rules" in work_order["required_outputs"]
        assert "updated_reference_strategy" in work_order["required_outputs"]
        assert "identity_acceptance_criteria" in work_order["required_outputs"]
        assert "reference_rebuild_notes" in work_order["required_outputs"]
    
    def test_execution_performed_false(self):
        """Test Character Director work order has execution_performed=false."""
        route = {
            "request_type": "reference_rebuild_request"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert work_order["execution_performed"] is False
    
    def test_retry_gate_open_false(self):
        """Test Character Director work order has retry_gate_open=false."""
        route = {
            "request_type": "reference_rebuild_request"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert work_order["retry_gate_open"] is False
    
    def test_production_accepted_false(self):
        """Test Character Director work order has production_accepted=false."""
        route = {
            "request_type": "reference_rebuild_request"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert work_order["production_accepted"] is False
    
    def test_downstream_blocked_true(self):
        """Test Character Director work order has downstream_blocked=true."""
        route = {
            "request_type": "reference_rebuild_request"
        }
        
        work_order = create_character_director_reference_rebuild_work_order(route)
        
        assert work_order["downstream_blocked"] is True


class TestCreateWorkOrderSummary:
    """Test creating work order summary."""
    
    def test_includes_current_routing(self):
        """Test summary includes current change request routing."""
        routes = [
            {
                "request_type": "workflow_change_request",
                "source_role": "Character Director",
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "recommended_action": "revise_identity_workflow_strategy",
                "reason": "identity_qa_failed",
                "blocks_retry": True
            }
        ]
        artifact_index = {"retry_gate_open": False, "production_accepted": False, "downstream_blocked": True}
        
        summary = create_work_order_summary(routes, artifact_index)
        
        assert "Current Change Request Routing" in summary
        assert "workflow_change_request" in summary
        assert "Character Director" in summary
        assert "Workflow TD / ComfyUI Technical Director" in summary
    
    def test_explains_each_role_required_work(self):
        """Test summary explains each role's required work."""
        routes = [
            {
                "request_type": "workflow_change_request",
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "recommended_action": "revise_identity_workflow_strategy"
            },
            {
                "request_type": "reference_rebuild_request",
                "target_role": "Character Director",
                "recommended_action": "rebuild_or_update_identity_reference_strategy"
            }
        ]
        artifact_index = {}
        
        summary = create_work_order_summary(routes, artifact_index)
        
        assert "Each Role's Required Work" in summary
        assert "Workflow TD / ComfyUI Technical Director" in summary
        assert "Character Director" in summary
    
    def test_explains_why_retry_blocked(self):
        """Test summary explains why retry remains blocked."""
        routes = []
        artifact_index = {}
        
        summary = create_work_order_summary(routes, artifact_index)
        
        assert "Why Retry Remains Blocked" in summary
        assert "Role decisions remain pending" in summary
        assert "No generation has been authorized" in summary
    
    def test_explains_what_must_happen_before_resubmit(self):
        """Test summary explains what must happen before decisions can be resubmitted."""
        routes = []
        artifact_index = {}
        
        summary = create_work_order_summary(routes, artifact_index)
        
        assert "What Must Happen Before Decisions Can Be Resubmitted" in summary
        assert "Workflow TD must complete" in summary
        assert "Character Director must complete" in summary
        assert "Decisions must be approved" in summary
    
    def test_explains_no_generation_authorized(self):
        """Test summary explains no generation has been authorized."""
        routes = []
        artifact_index = {}
        
        summary = create_work_order_summary(routes, artifact_index)
        
        assert "No Generation Authorized" in summary
        assert "No ComfyUI execution will occur" in summary
        assert "No frames will be generated" in summary
        assert "No references will be rebuilt" in summary


class TestCreateChangeRequestWorkOrders:
    """Test creating change request work orders end-to-end."""
    
    def setup_project_with_change_requests(self, tmpdir):
        """Helper to set up project with change requests."""
        project_root = Path(tmpdir)
        change_requests_dir = project_root / "output" / "control" / "decision_change_requests"
        change_requests_dir.mkdir(parents=True, exist_ok=True)
        
        # Create workflow change request
        workflow_request = {
            "request_type": "workflow_change_request",
            "source_role": "Character Director",
            "source_decision": "request_workflow_change",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "target_role": "Workflow TD / ComfyUI Technical Director",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_action": "revise_identity_workflow_strategy",
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(change_requests_dir / "workflow_change_request.json", 'w') as f:
            json.dump(workflow_request, f)
        
        # Create reference rebuild request
        reference_request = {
            "request_type": "reference_rebuild_request",
            "source_role": "Workflow TD / ComfyUI Technical Director",
            "source_decision": "request_reference_rebuild",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "target_role": "Character Director",
            "required_action": "rebuild_or_update_identity_reference_strategy",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(change_requests_dir / "reference_rebuild_request.json", 'w') as f:
            json.dump(reference_request, f)
        
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
    
    def test_creates_workflow_td_work_order(self):
        """Test creates Workflow TD workflow change work order."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            work_order_path = project_root / "output" / "control" / "change_request_work_orders" / "workflow_td_identity_workflow_change_order.json"
            assert work_order_path.exists()
            
            with open(work_order_path, 'r') as f:
                work_order = json.load(f)
            
            assert work_order["work_order_type"] == "workflow_change_order"
            assert work_order["role"] == "Workflow TD / ComfyUI Technical Director"
    
    def test_creates_character_director_work_order(self):
        """Test creates Character Director reference rebuild work order."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            work_order_path = project_root / "output" / "control" / "change_request_work_orders" / "character_director_reference_rebuild_order.json"
            assert work_order_path.exists()
            
            with open(work_order_path, 'r') as f:
                work_order = json.load(f)
            
            assert work_order["work_order_type"] == "reference_rebuild_order"
            assert work_order["role"] == "Character Director"
    
    def test_creates_work_order_summary(self):
        """Test creates CHANGE_REQUEST_WORK_ORDER_SUMMARY.md."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            summary_path = project_root / "output" / "control" / "change_request_work_orders" / "CHANGE_REQUEST_WORK_ORDER_SUMMARY.md"
            assert summary_path.exists()
            
            with open(summary_path, 'r') as f:
                summary = f.read()
            
            assert "Change Request Work Order Summary" in summary
    
    def test_work_orders_based_on_change_request_routing(self):
        """Test work orders are based on change request routing."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            # Verify result reflects routing
            assert result["work_orders_created"] == 2
            assert result["execution_performed"] is False
    
    def test_work_orders_do_not_modify_role_decisions(self):
        """Test work orders do not modify role_decisions/."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            # Check role_decisions still pending
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'r') as f:
                char_decision = json.load(f)
            
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'r') as f:
                workflow_decision = json.load(f)
            
            assert char_decision["decision_status"] == "pending"
            assert workflow_decision["decision_status"] == "pending"
    
    def test_work_orders_do_not_open_retry_gate(self):
        """Test work orders do not open retry gate."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            assert result["retry_gate_open"] is False
            
            # Check work orders
            workflow_order_path = project_root / "output" / "control" / "change_request_work_orders" / "workflow_td_identity_workflow_change_order.json"
            with open(workflow_order_path, 'r') as f:
                workflow_order = json.load(f)
            
            assert workflow_order["retry_gate_open"] is False
    
    def test_work_orders_keep_production_accepted_false(self):
        """Test work orders keep production_accepted=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            assert result["production_accepted"] is False
            
            # Check work orders
            workflow_order_path = project_root / "output" / "control" / "change_request_work_orders" / "workflow_td_identity_workflow_change_order.json"
            with open(workflow_order_path, 'r') as f:
                workflow_order = json.load(f)
            
            assert workflow_order["production_accepted"] is False
    
    def test_work_orders_keep_downstream_blocked_true(self):
        """Test work orders keep downstream_blocked=true."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            assert result["downstream_blocked"] is True
            
            # Check work orders
            workflow_order_path = project_root / "output" / "control" / "change_request_work_orders" / "workflow_td_identity_workflow_change_order.json"
            with open(workflow_order_path, 'r') as f:
                workflow_order = json.load(f)
            
            assert workflow_order["downstream_blocked"] is True
    
    def test_artifact_index_records_passive_work_order_section(self):
        """Test artifact_index records passive work order section only."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            # Check artifact index has passive section
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert "change_request_work_orders" in artifact_index
            assert artifact_index["change_request_work_orders"]["status"] == "created"
            assert artifact_index["change_request_work_orders"]["execution_performed"] is False
            assert artifact_index["change_request_work_orders"]["retry_gate_open"] is False
            assert artifact_index["change_request_work_orders"]["production_accepted"] is False
            assert artifact_index["change_request_work_orders"]["downstream_blocked"] is True
    
    def test_episode_ledger_records_change_request_work_orders_created(self):
        """Test episode_ledger records change_request_work_orders_created."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            # Check episode ledger
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert "events" in ledger
            assert len(ledger["events"]) > 0
            
            # Find the change_request_work_orders_created event
            work_order_events = [e for e in ledger["events"] if e.get("event_type") == "change_request_work_orders_created"]
            assert len(work_order_events) > 0
            
            event = work_order_events[-1]
            assert event["event_type"] == "change_request_work_orders_created"
            assert event["work_orders_created"] == 2
            assert event["execution_performed"] is False
            assert event["retry_gate_open"] is False
            assert event["production_accepted"] is False
            assert event["downstream_blocked"] is True
            assert event["comfyui_generation"] is False
            assert event["pipeline_action_rerun"] is False
    
    def test_validation_returns_ready_for_apply_false(self):
        """Test validation returns ready_for_apply=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            create_change_request_work_orders(str(project_root))
            result = validate_change_request_work_orders(str(project_root))
            
            assert result["ready_for_apply"] is False
    
    def test_no_generation_downstream_action_executes(self):
        """Test no generation/downstream action executes."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = create_change_request_work_orders(str(project_root))
            
            # Verify no generation was authorized
            assert result["execution_performed"] is False
            assert result["apply_performed"] is False
            assert result["can_retry_generation"] is False
            
            # Check episode ledger for generation events
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            # The latest event should have comfyui_generation=false
            latest_event = ledger["events"][-1]
            assert latest_event["comfyui_generation"] is False
            assert latest_event["pipeline_action_rerun"] is False
    
    def test_no_core_hardcode_for_alya_mir_erdan(self):
        """Test no core hardcode for Alya/Mir Erdan character names."""
        # Test with different character name to prove no hardcode
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            change_requests_dir = project_root / "output" / "control" / "decision_change_requests"
            change_requests_dir.mkdir(parents=True, exist_ok=True)
            
            # Create workflow change request with custom character
            workflow_request = {
                "request_type": "workflow_change_request",
                "source_role": "Character Director",
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "required_action": "revise_identity_workflow_strategy",
                "character_name": "CustomCharacter"  # Not Alya or Mir Erdan
            }
            
            with open(change_requests_dir / "workflow_change_request.json", 'w') as f:
                json.dump(workflow_request, f)
            
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
            
            result = create_change_request_work_orders(str(project_root))
            
            # Should work with any character name, not hardcoded to Alya/Mir Erdan
            assert result["status"] == "completed"
            assert result["work_orders_created"] == 1


class TestValidateChangeRequestWorkOrders:
    """Test validating change request work orders."""
    
    def setup_project_with_work_orders(self, tmpdir):
        """Helper to set up project with work orders."""
        project_root = Path(tmpdir)
        work_orders_dir = project_root / "output" / "control" / "change_request_work_orders"
        work_orders_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Workflow TD work order
        workflow_order = {
            "work_order_type": "workflow_change_order",
            "role": "Workflow TD / ComfyUI Technical Director",
            "source_request": "workflow_change_request",
            "source_decision": "request_workflow_change",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "revise_identity_workflow_strategy",
            "required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "required_outputs": ["updated_workflow_strategy", "workflow_audit"],
            "execution_performed": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(work_orders_dir / "workflow_td_identity_workflow_change_order.json", 'w') as f:
            json.dump(workflow_order, f)
        
        # Create Character Director work order
        character_order = {
            "work_order_type": "reference_rebuild_order",
            "role": "Character Director",
            "source_request": "reference_rebuild_request",
            "source_decision": "request_reference_rebuild",
            "blocked_shot": "shot01",
            "reason": "identity_qa_failed",
            "required_action": "rebuild_or_update_identity_reference_strategy",
            "required_generation_mode": "gorynych_identity",
            "required_outputs": ["updated_character_identity_rules", "updated_reference_strategy"],
            "execution_performed": False,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(work_orders_dir / "character_director_reference_rebuild_order.json", 'w') as f:
            json.dump(character_order, f)
        
        # Create summary
        with open(work_orders_dir / "CHANGE_REQUEST_WORK_ORDER_SUMMARY.md", 'w') as f:
            f.write("# Summary\n")
        
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
    
    def test_validates_work_orders(self):
        """Test validates work orders successfully."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = validate_change_request_work_orders(str(project_root))
            
            assert result["status"] == "valid"
            assert result["work_orders_found"] == 2
    
    def test_validation_returns_ready_for_apply_false(self):
        """Test validation returns ready_for_apply=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_work_orders(tmpdir)
            
            result = validate_change_request_work_orders(str(project_root))
            
            assert result["ready_for_apply"] is False
