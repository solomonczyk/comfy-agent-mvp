"""Tests for production role decisions module."""

import json
from pathlib import Path
import pytest


class TestProductionRoleDecisions:
    """Test suite for production role decision template generation."""
    
    def test_creates_character_director_pending_decision_template(self, tmp_path):
        """Test that create-role-decision-templates creates Character Director pending decision template."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        result = create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Verify Character Director decision template was created
        assert result["status"] == "completed"
        assert result["decision_templates_created"] == 2
        assert len(result["decision_templates"]) == 2
        
        # Verify JSON file exists
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        char_director_json = role_decisions_dir / "character_director_identity_decision.json"
        
        assert char_director_json.exists()
        
        # Verify decision is pending
        with open(char_director_json, 'r') as f:
            decision = json.load(f)
        
        assert decision["decision_status"] == "pending"
        assert decision["selected_decision"] is None
    
    def test_creates_workflow_td_pending_decision_template(self, tmp_path):
        """Test that create-role-decision-templates creates Workflow TD pending decision template."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Verify Workflow TD decision template was created
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        workflow_td_json = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
        
        assert workflow_td_json.exists()
        
        # Verify decision is pending
        with open(workflow_td_json, 'r') as f:
            decision = json.load(f)
        
        assert decision["decision_status"] == "pending"
        assert decision["selected_decision"] is None
    
    def test_preserves_alya_project_data_in_character_director_decision(self, tmp_path):
        """Test that Character Director decision preserves Alya project data."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Read Character Director decision
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        char_director_json = role_decisions_dir / "character_director_identity_decision.json"
        
        with open(char_director_json, 'r') as f:
            decision = json.load(f)
        
        # Verify Alya project data is preserved
        assert decision["character_name"] == "Alya"
        assert decision["display_name"] == "Alya"
        assert decision["reference_character"] == "Alya"
        assert decision["project_specific_data_allowed"] == True
    
    def test_workflow_td_decision_requires_gorynych_identity(self, tmp_path):
        """Test that Workflow TD decision requires gorynych_identity."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Read Workflow TD decision
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        workflow_td_json = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
        
        with open(workflow_td_json, 'r') as f:
            decision = json.load(f)
        
        # Verify gorynych_identity is required
        assert decision["current_required_generation_mode"] == "gorynych_identity"
        assert decision["legacy_reference_locked_allowed_for_production"] == False
    
    def test_pending_decisions_block_downstream(self, tmp_path):
        """Test that pending decisions block downstream."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.role_decisions import validate_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Validate role decisions
        validation_result = validate_role_decisions(str(tmp_path), json_output=True)
        
        # Verify pending decisions block downstream
        assert validation_result["status"] == "blocked"
        assert validation_result["decision_ready"] == False
        assert validation_result["downstream_blocked"] == True
    
    def test_pending_decisions_do_not_set_production_accepted_true(self, tmp_path):
        """Test that pending decisions do not set production_accepted=true."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        result = create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Verify result does not approve production
        assert result["downstream_blocked"] == True
        
        # Verify Character Director decision keeps production_accepted=false
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        char_director_json = role_decisions_dir / "character_director_identity_decision.json"
        
        with open(char_director_json, 'r') as f:
            decision = json.load(f)
        
        assert decision["downstream_blocked"] == True
        assert decision["production_accepted"] == False
        
        # Verify Workflow TD decision keeps production_accepted=false
        workflow_td_json = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
        
        with open(workflow_td_json, 'r') as f:
            decision = json.load(f)
        
        assert decision["downstream_blocked"] == True
        assert decision["production_accepted"] == False
    
    def test_validate_role_decisions_reports_missing_approvals(self, tmp_path):
        """Test that validate-role-decisions reports missing approvals."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.role_decisions import validate_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Validate role decisions
        validation_result = validate_role_decisions(str(tmp_path), json_output=True)
        
        # Verify missing approvals are reported
        assert validation_result["status"] == "blocked"
        assert validation_result["decision_ready"] == False
        assert validation_result["downstream_blocked"] == True
        assert validation_result["production_accepted"] == False
        assert len(validation_result["pending_roles"]) == 2
        assert len(validation_result["missing_approvals"]) == 2
        
        # Verify specific missing approvals
        assert "character_identity_approval" in validation_result["missing_approvals"]
        assert "workflow_fit_approval" in validation_result["missing_approvals"]
        
        # Verify pending roles
        assert "Character Director" in validation_result["pending_roles"]
        assert "Workflow TD / ComfyUI Technical Director" in validation_result["pending_roles"]
    
    def test_artifact_index_includes_decision_paths(self, tmp_path):
        """Test that artifact_index includes decision paths."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Read updated artifact_index
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify role_decisions section exists
        assert "role_decisions" in updated_index
        assert "character_director_decision" in updated_index["role_decisions"]
        assert "workflow_td_decision" in updated_index["role_decisions"]
        
        # Verify decision_status is pending
        assert updated_index["role_decisions"]["decision_status"] == "pending"
        assert updated_index["role_decisions"]["downstream_blocked"] == True
    
    def test_episode_ledger_records_role_decision_templates_created(self, tmp_path):
        """Test that episode_ledger records role_decision_templates_created event."""
        from app.production_cards.role_decisions import create_pending_role_decisions
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "scene_goal": "Introduce Alya in a serene forest setting"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards first
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Create role decision templates
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Read episode_ledger
        with open(control_dir / "episode_ledger.json", 'r') as f:
            ledger = json.load(f)
        
        # Verify event was recorded
        assert "events" in ledger
        assert len(ledger["events"]) > 0
        
        # Find the role_decision_templates_created event
        decision_events = [e for e in ledger["events"] if e["event_type"] == "role_decision_templates_created"]
        assert len(decision_events) == 1
        
        event = decision_events[0]
        assert event["decision_status"] == "pending"
        assert event["downstream_blocked"] == True
        assert event["comfyui_generation"] == False
        assert event["pipeline_action_rerun"] == False
        assert "Character Director" in event["roles"]
        assert "Workflow TD / ComfyUI Technical Director" in event["roles"]
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that role_decisions module has no hardcoded Alya/Mir Erdan."""
        import app.production_cards.role_decisions as role_decisions_module
        import inspect
        
        # Get the source code of the role_decisions module
        source = inspect.getsource(role_decisions_module)
        
        # Verify no hardcoded project-specific names
        assert "Mir Erdan" not in source
        
        # The module should not hardcode these names - they should come from input data
        # Any occurrence of "Alya" should be in test data or comments, not in core logic
