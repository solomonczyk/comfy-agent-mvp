"""
Tests for RC2-PRODCARDS2R — Change Request Routing Preview

Tests that decision change requests are routed to the correct production roles
without opening retry generation or applying decisions.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.change_request_router import (
    load_decision_change_requests,
    route_workflow_change_request,
    route_reference_rebuild_request,
    determine_next_actions,
    verify_no_route_to_image_generation,
    route_decision_change_requests,
)


class TestLoadDecisionChangeRequests:
    """Test loading decision change requests."""
    
    def test_load_workflow_change_request(self):
        """Test loading workflow_change_request.json."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            change_requests_dir = project_root / "output" / "control" / "decision_change_requests"
            change_requests_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_request = {
                "request_type": "workflow_change_request",
                "source_role": "Character Director",
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "required_action": "revise_identity_workflow_strategy"
            }
            
            with open(change_requests_dir / "workflow_change_request.json", 'w') as f:
                json.dump(workflow_request, f)
            
            requests = load_decision_change_requests(str(project_root))
            
            assert len(requests) == 1
            assert requests[0]["request_type"] == "workflow_change_request"
    
    def test_load_reference_rebuild_request(self):
        """Test loading reference_rebuild_request.json."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            change_requests_dir = project_root / "output" / "control" / "decision_change_requests"
            change_requests_dir.mkdir(parents=True, exist_ok=True)
            
            reference_request = {
                "request_type": "reference_rebuild_request",
                "source_role": "Workflow TD / ComfyUI Technical Director",
                "target_role": "Character Director",
                "required_action": "rebuild_or_update_identity_reference_strategy"
            }
            
            with open(change_requests_dir / "reference_rebuild_request.json", 'w') as f:
                json.dump(reference_request, f)
            
            requests = load_decision_change_requests(str(project_root))
            
            assert len(requests) == 1
            assert requests[0]["request_type"] == "reference_rebuild_request"
    
    def test_load_both_requests(self):
        """Test loading both workflow and reference requests."""
        with TemporaryDirectory() as tmpdir:
            project_root = Path(tmpdir)
            change_requests_dir = project_root / "output" / "control" / "decision_change_requests"
            change_requests_dir.mkdir(parents=True, exist_ok=True)
            
            workflow_request = {
                "request_type": "workflow_change_request",
                "source_role": "Character Director",
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "required_action": "revise_identity_workflow_strategy"
            }
            
            reference_request = {
                "request_type": "reference_rebuild_request",
                "source_role": "Workflow TD / ComfyUI Technical Director",
                "target_role": "Character Director",
                "required_action": "rebuild_or_update_identity_reference_strategy"
            }
            
            with open(change_requests_dir / "workflow_change_request.json", 'w') as f:
                json.dump(workflow_request, f)
            with open(change_requests_dir / "reference_rebuild_request.json", 'w') as f:
                json.dump(reference_request, f)
            
            requests = load_decision_change_requests(str(project_root))
            
            assert len(requests) == 2


class TestRouteWorkflowChangeRequest:
    """Test routing workflow change request."""
    
    def test_routes_to_workflow_td(self):
        """Test workflow change request routes to Workflow TD."""
        request = {
            "request_type": "workflow_change_request",
            "source_role": "Character Director",
            "target_role": "Workflow TD / ComfyUI Technical Director",
            "required_action": "revise_identity_workflow_strategy",
            "reason": "identity_qa_failed"
        }
        
        route = route_workflow_change_request(request)
        
        assert route["request_type"] == "workflow_change_request"
        assert route["source_role"] == "Character Director"
        assert route["target_role"] == "Workflow TD / ComfyUI Technical Director"
        assert route["recommended_action"] == "revise_identity_workflow_strategy"
        assert route["reason"] == "identity_qa_failed"
        assert route["blocks_retry"] is True
    
    def test_blocks_retry(self):
        """Test workflow change request blocks retry."""
        request = {
            "request_type": "workflow_change_request",
            "target_role": "Workflow TD / ComfyUI Technical Director"
        }
        
        route = route_workflow_change_request(request)
        
        assert route["blocks_retry"] is True


class TestRouteReferenceRebuildRequest:
    """Test routing reference rebuild request."""
    
    def test_routes_to_character_director(self):
        """Test reference rebuild request routes to Character Director."""
        request = {
            "request_type": "reference_rebuild_request",
            "source_role": "Workflow TD / ComfyUI Technical Director",
            "target_role": "Character Director",
            "required_action": "rebuild_or_update_identity_reference_strategy",
            "reason": "identity_qa_failed"
        }
        
        route = route_reference_rebuild_request(request)
        
        assert route["request_type"] == "reference_rebuild_request"
        assert route["source_role"] == "Workflow TD / ComfyUI Technical Director"
        assert route["target_role"] == "Character Director"
        assert route["recommended_action"] == "rebuild_or_update_identity_reference_strategy"
        assert route["reason"] == "identity_qa_failed"
        assert route["blocks_retry"] is True
    
    def test_blocks_retry(self):
        """Test reference rebuild request blocks retry."""
        request = {
            "request_type": "reference_rebuild_request",
            "target_role": "Character Director"
        }
        
        route = route_reference_rebuild_request(request)
        
        assert route["blocks_retry"] is True


class TestDetermineNextActions:
    """Test determining next required actions."""
    
    def test_workflow_td_priority_1(self):
        """Test Workflow TD actions have priority 1."""
        routes = [
            {
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "recommended_action": "revise_identity_workflow_strategy"
            },
            {
                "target_role": "Character Director",
                "recommended_action": "rebuild_or_update_identity_reference_strategy"
            }
        ]
        
        next_actions = determine_next_actions(routes)
        
        assert len(next_actions) == 2
        assert next_actions[0]["priority"] == 1
        assert next_actions[0]["role"] == "Workflow TD / ComfyUI Technical Director"
        assert next_actions[1]["priority"] == 2
        assert next_actions[1]["role"] == "Character Director"
    
    def test_character_director_priority_2(self):
        """Test Character Director actions have priority 2."""
        routes = [
            {
                "target_role": "Workflow TD / ComfyUI Technical Director",
                "recommended_action": "revise_identity_workflow_strategy"
            },
            {
                "target_role": "Character Director",
                "recommended_action": "rebuild_or_update_identity_reference_strategy"
            }
        ]
        
        next_actions = determine_next_actions(routes)
        
        assert next_actions[1]["priority"] == 2
        assert next_actions[1]["role"] == "Character Director"


class TestVerifyNoRouteToImageGeneration:
    """Test verifying no route to Image Generation Agent."""
    
    def test_no_route_to_image_generation(self):
        """Test routes to production roles do not include Image Generation."""
        routes = [
            {
                "target_role": "Workflow TD / ComfyUI Technical Director"
            },
            {
                "target_role": "Character Director"
            }
        ]
        
        result = verify_no_route_to_image_generation(routes)
        
        assert result is True
    
    def test_route_to_image_generation_detected(self):
        """Test route to Image Generation is detected."""
        routes = [
            {
                "target_role": "Image Generation Agent"
            }
        ]
        
        result = verify_no_route_to_image_generation(routes)
        
        assert result is False
    
    def test_route_to_generate_frames_detected(self):
        """Test route to Generate Frames is detected."""
        routes = [
            {
                "target_role": "Generate Frames Agent"
            }
        ]
        
        result = verify_no_route_to_image_generation(routes)
        
        assert result is False


class TestRouteDecisionChangeRequests:
    """Test routing decision change requests."""
    
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
    
    def test_route_preview_returns_blocked(self):
        """Test route preview returns blocked status."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            assert result["status"] == "blocked"
    
    def test_routes_workflow_change_request_to_workflow_td(self):
        """Test routes workflow_change_request to Workflow TD."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            workflow_route = [r for r in result["routes"] if r["request_type"] == "workflow_change_request"]
            assert len(workflow_route) == 1
            assert workflow_route[0]["target_role"] == "Workflow TD / ComfyUI Technical Director"
    
    def test_routes_reference_rebuild_request_to_character_director(self):
        """Test routes reference_rebuild_request to Character Director."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            reference_route = [r for r in result["routes"] if r["request_type"] == "reference_rebuild_request"]
            assert len(reference_route) == 1
            assert reference_route[0]["target_role"] == "Character Director"
    
    def test_no_route_points_to_image_generation_agent(self):
        """Test no route points to Image Generation Agent."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            assert result["no_image_generation_route"] is True
            
            # Verify all routes are to production roles
            for route in result["routes"]:
                assert "Image Generation" not in route["target_role"]
                assert "Generate Frames" not in route["target_role"]
    
    def test_retry_gate_remains_closed(self):
        """Test retry gate remains closed."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            assert result["retry_gate_open"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["retry_gate_open"] is False
    
    def test_production_accepted_remains_false(self):
        """Test production_accepted remains false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            assert result["production_accepted"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["production_accepted"] is False
    
    def test_downstream_blocked_remains_true(self):
        """Test downstream_blocked remains true."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            assert result["downstream_blocked"] is True
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["downstream_blocked"] is True
    
    def test_role_decisions_remain_pending(self):
        """Test role_decisions remain pending."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            # Check role_decisions still pending
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'r') as f:
                char_decision = json.load(f)
            
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'r') as f:
                workflow_decision = json.load(f)
            
            assert char_decision["decision_status"] == "pending"
            assert workflow_decision["decision_status"] == "pending"
    
    def test_artifact_index_records_passive_routing_section(self):
        """Test artifact_index records passive routing section only."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            # Check artifact index has passive section
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert "decision_change_request_routing" in artifact_index
            assert artifact_index["decision_change_request_routing"]["status"] == "blocked"
            assert artifact_index["decision_change_request_routing"]["retry_gate_open"] is False
            assert artifact_index["decision_change_request_routing"]["production_accepted"] is False
            assert artifact_index["decision_change_request_routing"]["downstream_blocked"] is True
    
    def test_episode_ledger_records_decision_change_requests_routed(self):
        """Test episode_ledger records decision_change_requests_routed."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            # Check episode ledger
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert "events" in ledger
            assert len(ledger["events"]) > 0
            
            # Find the decision_change_requests_routed event
            routed_events = [e for e in ledger["events"] if e.get("event_type") == "decision_change_requests_routed"]
            assert len(routed_events) > 0
            
            event = routed_events[-1]
            assert event["event_type"] == "decision_change_requests_routed"
            assert event["change_requests_found"] == 2
            assert event["retry_gate_open"] is False
            assert event["production_accepted"] is False
            assert event["downstream_blocked"] is True
            assert event["comfyui_generation"] is False
            assert event["pipeline_action_rerun"] is False
    
    def test_no_generation_downstream_action_executes(self):
        """Test no generation/downstream action executes."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = route_decision_change_requests(str(project_root))
            
            # Verify no generation was authorized
            assert result["ready_for_apply"] is False
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
                "reason": "identity_qa_failed",
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
            
            result = route_decision_change_requests(str(project_root))
            
            # Should work with any character name, not hardcoded to Alya/Mir Erdan
            assert result["status"] == "blocked"
            assert result["change_requests_found"] == 1
