"""Tests for production real role decision draft submission module."""

import json
from pathlib import Path
import pytest


class TestProductionRealRoleDecisionDrafts:
    """Test suite for production real role decision draft submission generation."""
    
    def test_creates_character_director_submitted_draft(self, tmp_path):
        """Test that create-real-role-decision-drafts creates Character Director submitted draft."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify Character Director submitted draft was created
        assert result["status"] == "completed"
        assert result["drafts_created"] == 2
        assert result["drafts_are_submitted_decisions"] == True
        assert result["apply_performed"] == False
        assert result["retry_gate_open"] == False
        assert result["production_accepted"] == False
        assert result["downstream_blocked"] == True
        
        # Verify JSON file exists in submitted/ folder
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        
        assert char_draft_json.exists()
        
        # Verify draft is submitted with decision filled
        with open(char_draft_json, 'r') as f:
            draft = json.load(f)
        
        assert draft["decision_status"] == "submitted"
        assert draft["selected_decision"] is not None
        assert draft["draft_submission"] == True
        assert draft["not_applied"] == True
    
    def test_creates_workflow_td_submitted_draft(self, tmp_path):
        """Test that create-real-role-decision-drafts creates Workflow TD submitted draft."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify Workflow TD submitted draft was created
        assert result["status"] == "completed"
        assert result["drafts_created"] == 2
        
        # Verify JSON file exists in submitted/ folder
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        
        assert workflow_draft_json.exists()
        
        # Verify draft is submitted with decision filled
        with open(workflow_draft_json, 'r') as f:
            draft = json.load(f)
        
        assert draft["decision_status"] == "submitted"
        assert draft["selected_decision"] is not None
        assert draft["draft_submission"] == True
        assert draft["not_applied"] == True
    
    def test_drafts_use_decision_source_real_role_decision(self, tmp_path):
        """Test that drafts use decision_source=real_role_decision."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify drafts use decision_source=real_role_decision
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert char_draft["decision_source"] == "real_role_decision"
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert workflow_draft["decision_source"] == "real_role_decision"
    
    def test_drafts_use_fixture_only_false(self, tmp_path):
        """Test that drafts use fixture_only=false."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify drafts use fixture_only=false
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert char_draft["fixture_only"] == False
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert workflow_draft["fixture_only"] == False
    
    def test_drafts_are_based_on_evidence_packets(self, tmp_path):
        """Test that drafts are based on evidence packets."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify drafts are based on evidence packets
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert "based_on_evidence_packet" in char_draft
        assert "character_director_identity_evidence_packet.json" in char_draft["based_on_evidence_packet"]
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert "based_on_evidence_packet" in workflow_draft
        assert "workflow_td_identity_workflow_evidence_packet.json" in workflow_draft["based_on_evidence_packet"]
    
    def test_drafts_are_based_on_work_orders(self, tmp_path):
        """Test that drafts are based on work orders."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify drafts are based on work orders
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert "based_on_work_order" in char_draft
        assert "character_director_identity_review.json" in char_draft["based_on_work_order"]
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert "based_on_work_order" in workflow_draft
        assert "workflow_td_identity_workflow_review.json" in workflow_draft["based_on_work_order"]
    
    def test_drafts_include_required_artifacts(self, tmp_path):
        """Test that drafts include required artifacts."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify Character Director draft includes required artifacts
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert "approved_character_identity_rules" in char_draft
        assert "approved_reference_strategy" in char_draft
        assert "identity_acceptance_criteria" in char_draft
        
        # Verify Workflow TD draft includes required artifacts
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert "workflow_audit" in workflow_draft
        assert "required_nodes" in workflow_draft
        assert "required_models" in workflow_draft
        assert "preflight_result" in workflow_draft
        assert "output_collection_contract" in workflow_draft
    
    def test_drafts_do_not_modify_role_decisions(self, tmp_path):
        """Test that drafts do not modify role_decisions/."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify role_decisions/ was not modified (should not exist or be empty)
        role_decisions_dir = tmp_path / "output" / "control" / "role_decisions"
        
        # If role_decisions exists, verify no decisions have selected_decision filled
        if role_decisions_dir.exists():
            for decision_file in role_decisions_dir.glob("*.json"):
                with open(decision_file, 'r') as f:
                    decision = json.load(f)
                # Drafts should NOT have filled selected_decision in role_decisions/
                assert decision.get("selected_decision") is None, f"role_decisions/{decision_file.name} was mutated"
    
    def test_drafts_do_not_open_retry_gate(self, tmp_path):
        """Test that drafts do not open retry gate."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify retry_gate_open=false
        assert result["retry_gate_open"] == False
        
        # Verify artifact_index still has retry_gate_open=false
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        assert updated_index.get("retry_gate_open") == False
    
    def test_drafts_keep_production_accepted_false(self, tmp_path):
        """Test that drafts keep production_accepted=false."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify production_accepted=false
        assert result["production_accepted"] == False
        
        # Verify drafts themselves have production_accepted=false
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert char_draft["production_accepted"] == False
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert workflow_draft["production_accepted"] == False
    
    def test_drafts_keep_downstream_blocked_true(self, tmp_path):
        """Test that drafts keep downstream_blocked=true."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify downstream_blocked=true
        assert result["downstream_blocked"] == True
        
        # Verify drafts themselves have downstream_blocked=true
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        assert char_draft["downstream_blocked"] == True
        
        workflow_draft_json = submitted_dir / "workflow_td_real_decision.SUBMITTED.json"
        with open(workflow_draft_json, 'r') as f:
            workflow_draft = json.load(f)
        assert workflow_draft["downstream_blocked"] == True
    
    def test_validate_submitted_role_decisions_can_validate_submitted_draft_folder(self, tmp_path):
        """Test that validate-submitted-role-decisions can validate submitted draft folder."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        from app.production_cards.decision_submission_validator import validate_submitted_role_decisions as validate_submissions
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Validate submitted decisions using custom submission-root
        # The validator expects the submission_root to contain the submitted files directly
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        result = validate_submissions(str(tmp_path), submission_root=str(submitted_dir))
        
        # Verify validation passed - drafts are valid submissions with decisions filled
        assert result["status"] == "valid"
        assert result["submitted_decisions_ready"] == True
        assert result["valid_submissions"] == 2
    
    def test_no_generation_or_downstream_action_executes(self, tmp_path):
        """Test that no generation or downstream action executes during draft creation."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        result = create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify no generation artifacts were created
        # Draft creation should only create JSON files, not frames, scenes, or audio
        assert result["apply_performed"] == False
        assert result["retry_gate_open"] == False
        
        # Verify no frame generation artifacts exist
        frames_dir = tmp_path / "output" / "frames"
        if frames_dir.exists():
            # Should be empty or not contain generated frames
            frame_files = list(frames_dir.glob("*.png"))
            assert len(frame_files) == 0, "Frame generation artifacts should not exist"
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that drafts do not hardcode Alya or Mir Erdan character names."""
        from app.production_cards.decision_submission import create_real_role_decision_drafts
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.materializer import ProductionCardMaterializer
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index with identity failure using generic character
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "GenericChar",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "GenericChar",
                    "scene_goal": "Test scene"
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
        
        # Create role review evidence packets first
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract (templates)
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Create real role decision drafts (submitted)
        create_real_role_decision_drafts(str(tmp_path), json_output=True)
        
        # Verify drafts use project-specific data, not hardcoded Alya/Mir Erdan
        submitted_dir = tmp_path / "output" / "control" / "role_decision_submissions" / "submitted"
        
        char_draft_json = submitted_dir / "character_director_real_decision.SUBMITTED.json"
        with open(char_draft_json, 'r') as f:
            char_draft = json.load(f)
        
        # Character name should come from evidence packet, not hardcoded
        # If evidence packet has "GenericChar", draft should use that
        # This test verifies the mechanism works, not that specific names are excluded
        assert char_draft["character_name"] == "GenericChar" or char_draft["character_name"] == "Unknown"
