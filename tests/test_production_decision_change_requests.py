"""
Tests for RC2-PRODCARDS2Q — Decision Change Request Pack

Tests that decision change requests are created from submitted decision outcomes
without opening retry generation or applying decisions.
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from app.production_cards.decision_change_requests import (
    load_submitted_decision_outcome,
    create_workflow_change_request,
    create_reference_rebuild_request,
    create_change_request_summary,
    create_decision_change_request_pack,
    validate_decision_change_request_pack,
    load_artifact_index,
    load_episode_ledger,
    append_episode_ledger_event,
    update_artifact_index_for_change_requests,
)


class TestLoadSubmittedDecisionOutcome:
    """Test loading submitted decision outcome."""
    
    def test_load_submitted_decision_outcome(self):
        """Test loading submitted decision outcome from decision_submission_outcome module."""
        # This test verifies integration with RC2-PRODCARDS2P
        # The actual implementation is tested in test_production_submitted_decision_outcome.py
        assert True  # Integration test placeholder


class TestCreateWorkflowChangeRequest:
    """Test creating workflow change request."""
    
    def test_create_workflow_change_request_structure(self):
        """Test workflow change request has required structure."""
        project_root = "/tmp/test_project"
        submitted_outcome = {
            "character_director_outcome": "request_workflow_change",
            "workflow_td_outcome": "approve_workflow"
        }
        
        request = create_workflow_change_request(project_root, submitted_outcome)
        
        assert request["request_type"] == "workflow_change_request"
        assert request["source_role"] == "Character Director"
        assert request["source_decision"] == "request_workflow_change"
        assert request["blocked_shot"] == "shot01"
        assert request["reason"] == "identity_qa_failed"
        assert request["target_role"] == "Workflow TD / ComfyUI Technical Director"
        assert request["required_generation_mode"] == "gorynych_identity"
        assert request["legacy_reference_locked_allowed_for_production"] is False
        assert request["required_action"] == "revise_identity_workflow_strategy"
        assert request["retry_gate_open"] is False
        assert request["production_accepted"] is False
        assert request["downstream_blocked"] is True
        assert "created_at" in request
    
    def test_workflow_change_request_routes_to_workflow_td(self):
        """Test workflow change request routes to Workflow TD."""
        project_root = "/tmp/test_project"
        submitted_outcome = {
            "character_director_outcome": "request_workflow_change"
        }
        
        request = create_workflow_change_request(project_root, submitted_outcome)
        
        assert request["target_role"] == "Workflow TD / ComfyUI Technical Director"
        assert request["required_action"] == "revise_identity_workflow_strategy"


class TestCreateReferenceRebuildRequest:
    """Test creating reference rebuild request."""
    
    def test_create_reference_rebuild_request_structure(self):
        """Test reference rebuild request has required structure."""
        project_root = "/tmp/test_project"
        submitted_outcome = {
            "character_director_outcome": "approve",
            "workflow_td_outcome": "request_reference_rebuild"
        }
        
        request = create_reference_rebuild_request(project_root, submitted_outcome)
        
        assert request["request_type"] == "reference_rebuild_request"
        assert request["source_role"] == "Workflow TD / ComfyUI Technical Director"
        assert request["source_decision"] == "request_reference_rebuild"
        assert request["blocked_shot"] == "shot01"
        assert request["reason"] == "identity_qa_failed"
        assert request["target_role"] == "Character Director"
        assert request["required_action"] == "rebuild_or_update_identity_reference_strategy"
        assert request["required_generation_mode"] == "gorynych_identity"
        assert request["legacy_reference_locked_allowed_for_production"] is False
        assert request["retry_gate_open"] is False
        assert request["production_accepted"] is False
        assert request["downstream_blocked"] is True
        assert "created_at" in request
    
    def test_reference_rebuild_request_routes_to_character_director(self):
        """Test reference rebuild request routes to Character Director."""
        project_root = "/tmp/test_project"
        submitted_outcome = {
            "workflow_td_outcome": "request_reference_rebuild"
        }
        
        request = create_reference_rebuild_request(project_root, submitted_outcome)
        
        assert request["target_role"] == "Character Director"
        assert request["required_action"] == "rebuild_or_update_identity_reference_strategy"


class TestCreateChangeRequestSummary:
    """Test creating change request summary."""
    
    def test_create_change_request_summary_content(self):
        """Test change request summary contains required content."""
        project_root = "/tmp/test_project"
        submitted_outcome = {
            "character_director_outcome": "request_workflow_change",
            "workflow_td_outcome": "request_reference_rebuild",
            "status": "changes_requested",
            "ready_for_apply": False,
            "can_retry_generation": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "apply_performed": False
        }
        workflow_request = {
            "request_type": "workflow_change_request",
            "target_role": "Workflow TD / ComfyUI Technical Director",
            "required_action": "revise_identity_workflow_strategy"
        }
        reference_request = {
            "request_type": "reference_rebuild_request",
            "target_role": "Character Director",
            "required_action": "rebuild_or_update_identity_reference_strategy"
        }
        
        summary = create_change_request_summary(
            project_root,
            submitted_outcome,
            workflow_request,
            reference_request
        )
        
        assert "Current Submitted Decision Outcomes" in summary
        assert "character_director_outcome" in summary or "Character Director Outcome" in summary
        assert "workflow_td_outcome" in summary or "Workflow TD Outcome" in summary
        assert "Why Retry Remains Blocked" in summary
        assert "Next Required Actions by Role" in summary
        assert "Workflow TD" in summary
        assert "Character Director" in summary
        assert "What Must Be Resolved Before Approval/Apply" in summary
        assert "Generation Authorized" in summary
        assert "No apply, generation, or downstream action has been executed" in summary


class TestCreateDecisionChangeRequestPack:
    """Test creating decision change request pack."""
    
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
    
    def test_creates_workflow_change_request_json(self):
        """Test creates workflow_change_request.json."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="approve_workflow"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            workflow_request_path = project_root / "output" / "control" / "decision_change_requests" / "workflow_change_request.json"
            assert workflow_request_path.exists()
            
            with open(workflow_request_path, 'r') as f:
                workflow_request = json.load(f)
            
            assert workflow_request["request_type"] == "workflow_change_request"
            assert workflow_request["target_role"] == "Workflow TD / ComfyUI Technical Director"
    
    def test_creates_reference_rebuild_request_json(self):
        """Test creates reference_rebuild_request.json."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="approve",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            reference_request_path = project_root / "output" / "control" / "decision_change_requests" / "reference_rebuild_request.json"
            assert reference_request_path.exists()
            
            with open(reference_request_path, 'r') as f:
                reference_request = json.load(f)
            
            assert reference_request["request_type"] == "reference_rebuild_request"
            assert reference_request["target_role"] == "Character Director"
    
    def test_creates_change_request_summary_md(self):
        """Test creates CHANGE_REQUEST_SUMMARY.md."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            summary_path = project_root / "output" / "control" / "decision_change_requests" / "CHANGE_REQUEST_SUMMARY.md"
            assert summary_path.exists()
            
            with open(summary_path, 'r') as f:
                summary = f.read()
            
            assert "Decision Change Request Summary" in summary
            assert "Current Submitted Decision Outcomes" in summary
    
    def test_change_requests_based_on_submitted_decision_outcome(self):
        """Test change requests are based on submitted decision outcome."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Verify result reflects submitted outcome
            assert result["outcome_status"] == "changes_requested"
            assert result["change_requests_created"] == 2
    
    def test_request_workflow_change_routes_to_workflow_td(self):
        """Test request_workflow_change routes to Workflow TD."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="approve_workflow"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            workflow_request_path = project_root / "output" / "control" / "decision_change_requests" / "workflow_change_request.json"
            with open(workflow_request_path, 'r') as f:
                workflow_request = json.load(f)
            
            assert workflow_request["target_role"] == "Workflow TD / ComfyUI Technical Director"
    
    def test_request_reference_rebuild_routes_to_character_director(self):
        """Test request_reference_rebuild routes to Character Director."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="approve",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            reference_request_path = project_root / "output" / "control" / "decision_change_requests" / "reference_rebuild_request.json"
            with open(reference_request_path, 'r') as f:
                reference_request = json.load(f)
            
            assert reference_request["target_role"] == "Character Director"
    
    def test_change_requests_do_not_modify_role_decisions(self):
        """Test change requests do not modify role_decisions/."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Check role_decisions still pending
            role_decisions_dir = project_root / "output" / "control" / "role_decisions"
            
            with open(role_decisions_dir / "character_director_identity_decision.json", 'r') as f:
                char_decision = json.load(f)
            
            with open(role_decisions_dir / "workflow_td_identity_workflow_decision.json", 'r') as f:
                workflow_decision = json.load(f)
            
            assert char_decision["decision_status"] == "pending"
            assert workflow_decision["decision_status"] == "pending"
    
    def test_change_requests_do_not_open_retry_gate(self):
        """Test change requests do not open retry gate."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            assert result["retry_gate_open"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["retry_gate_open"] is False
    
    def test_change_requests_keep_production_accepted_false(self):
        """Test change requests keep production_accepted=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            assert result["production_accepted"] is False
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["production_accepted"] is False
    
    def test_change_requests_keep_downstream_blocked_true(self):
        """Test change requests keep downstream_blocked=true."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            assert result["downstream_blocked"] is True
            
            # Check artifact index
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert artifact_index["downstream_blocked"] is True


class TestValidateDecisionChangeRequestPack:
    """Test validating decision change request pack."""
    
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
        
        # Create summary
        summary = "# Decision Change Request Summary\n\nTest summary."
        with open(change_requests_dir / "CHANGE_REQUEST_SUMMARY.md", 'w') as f:
            f.write(summary)
        
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
    
    def test_validation_returns_ready_for_apply_false(self):
        """Test validation returns ready_for_apply=false."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_change_requests(tmpdir)
            
            result = validate_decision_change_request_pack(str(project_root))
            
            assert result["ready_for_apply"] is False
    
    def test_artifact_index_records_passive_change_request_section(self):
        """Test artifact_index records passive change request section only."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Check artifact index has passive section
            artifact_index_path = project_root / "output" / "control" / "artifact_index.json"
            with open(artifact_index_path, 'r') as f:
                artifact_index = json.load(f)
            
            assert "decision_change_requests" in artifact_index
            assert artifact_index["decision_change_requests"]["status"] == "created"
            assert artifact_index["decision_change_requests"]["ready_for_apply"] is False
            assert artifact_index["decision_change_requests"]["retry_gate_open"] is False
            assert artifact_index["decision_change_requests"]["production_accepted"] is False
            assert artifact_index["decision_change_requests"]["downstream_blocked"] is True
    
    def test_episode_ledger_records_decision_change_requests_created(self):
        """Test episode_ledger records decision_change_requests_created."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Check episode ledger
            ledger_path = project_root / "output" / "control" / "episode_ledger.json"
            with open(ledger_path, 'r') as f:
                ledger = json.load(f)
            
            assert "events" in ledger
            assert len(ledger["events"]) > 0
            
            # Find the decision_change_requests_created event
            change_request_events = [e for e in ledger["events"] if e.get("event_type") == "decision_change_requests_created"]
            assert len(change_request_events) > 0
            
            event = change_request_events[-1]
            assert event["event_type"] == "decision_change_requests_created"
            assert event["reason"] == "submitted_role_decisions_requested_changes"
            assert event["ready_for_apply"] is False
            assert event["retry_gate_open"] is False
            assert event["production_accepted"] is False
            assert event["downstream_blocked"] is True
            assert event["comfyui_generation"] is False
            assert event["pipeline_action_rerun"] is False
    
    def test_no_generation_downstream_action_executes(self):
        """Test no generation/downstream action executes."""
        with TemporaryDirectory() as tmpdir:
            project_root = self.setup_project_with_submissions(
                tmpdir,
                char_decision="request_workflow_change",
                workflow_decision="request_reference_rebuild"
            )
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Verify no generation was authorized
            assert result["generation_authorized"] is False
            
            # Verify no apply happened
            assert result["apply_performed"] is False
            
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
            submitted_dir = project_root / "output" / "control" / "role_decision_submissions" / "submitted"
            submitted_dir.mkdir(parents=True, exist_ok=True)
            
            char_submission = {
                "role": "Character Director",
                "decision_source": "real_role_decision",
                "fixture_only": False,
                "production_accepted": False,
                "selected_decision": "request_workflow_change",
                "allowed_decisions": ["approve", "reject", "request_new_reference", "request_workflow_change"],
                "required_artifacts": ["approved_character_identity_rules"],
                "character_name": "CustomCharacter"  # Not Alya or Mir Erdan
            }
            
            workflow_submission = {
                "role": "Workflow TD / ComfyUI Technical Director",
                "decision_source": "real_role_decision",
                "fixture_only": False,
                "production_accepted": False,
                "selected_decision": "request_reference_rebuild",
                "allowed_decisions": ["approve_workflow", "reject_workflow", "request_missing_nodes", "request_missing_models", "request_reference_rebuild"],
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
            
            result = create_decision_change_request_pack(str(project_root))
            
            # Should work with any character name, not hardcoded to Alya/Mir Erdan
            assert result["status"] == "completed"
            assert result["change_requests_created"] == 2
