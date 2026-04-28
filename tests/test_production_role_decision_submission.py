"""Tests for production role decision submission contract module."""

import json
from pathlib import Path
import pytest


class TestProductionRoleDecisionSubmission:
    """Test suite for production role decision submission contract generation."""
    
    def test_creates_character_director_submission_template(self, tmp_path):
        """Test that create-role-decision-submission-contract creates Character Director submission template."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        result = create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director submission template was created
        assert result["status"] == "completed"
        assert result["submission_templates_created"] == 2
        assert len(result["templates"]) == 2
        
        # Verify JSON file exists
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        assert char_template_json.exists()
        
        # Verify template is draft submission
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["current_decision_status"] == "draft_submission"
        assert template["selected_decision"] is None
    
    def test_creates_workflow_td_submission_template(self, tmp_path):
        """Test that create-role-decision-submission-contract creates Workflow TD submission template."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Workflow TD submission template was created
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        assert workflow_template_json.exists()
        
        # Verify template is draft submission
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["current_decision_status"] == "draft_submission"
        assert template["selected_decision"] is None
    
    def test_templates_are_fixture_only_false(self, tmp_path):
        """Test that submission templates are fixture_only=false."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template is fixture_only=false
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["fixture_only"] == False
        
        # Verify Workflow TD template is fixture_only=false
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["fixture_only"] == False
    
    def test_templates_use_decision_source_real_role_decision(self, tmp_path):
        """Test that submission templates use decision_source=real_role_decision."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template uses decision_source=real_role_decision
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["decision_source"] == "real_role_decision"
        
        # Verify Workflow TD template uses decision_source=real_role_decision
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["decision_source"] == "real_role_decision"
    
    def test_templates_contain_approved_for_project_id(self, tmp_path):
        """Test that submission templates contain approved_for_project_id."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template contains approved_for_project_id
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert "approved_for_project_id" in template
        assert template["approved_for_project_id"] == tmp_path.name
        
        # Verify Workflow TD template contains approved_for_project_id
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert "approved_for_project_id" in template
        assert template["approved_for_project_id"] == tmp_path.name
    
    def test_templates_contain_approved_for_shot_shot01(self, tmp_path):
        """Test that submission templates contain approved_for_shot=shot01."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        result = create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify templates contain approved_for_shot=shot01
        for template in result['templates']:
            assert "approved_for_shot" in template
            assert template["approved_for_shot"] == "shot01"
    
    def test_templates_reference_evidence_packet_paths(self, tmp_path):
        """Test that submission templates reference evidence packet paths."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template references evidence packet path
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert "based_on_evidence_packet" in template
        assert "role_review_packets" in template["based_on_evidence_packet"]
        assert "character_director_identity_evidence_packet.json" in template["based_on_evidence_packet"]
        
        # Verify Workflow TD template references evidence packet path
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert "based_on_evidence_packet" in template
        assert "role_review_packets" in template["based_on_evidence_packet"]
        assert "workflow_td_identity_workflow_evidence_packet.json" in template["based_on_evidence_packet"]
    
    def test_templates_reference_work_order_paths(self, tmp_path):
        """Test that submission templates reference work order paths."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.materializer import ProductionCardMaterializer
        from app.production_cards.work_orders import create_work_orders
        
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
        
        # Create work orders first
        create_work_orders(str(tmp_path), json_output=True)
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template references work order path
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert "based_on_work_order" in template
        assert "work_orders" in template["based_on_work_order"]
        assert "character_director_identity_review.json" in template["based_on_work_order"]
        
        # Verify Workflow TD template references work order path
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert "based_on_work_order" in template
        assert "work_orders" in template["based_on_work_order"]
        assert "workflow_td_identity_workflow_review.json" in template["based_on_work_order"]
    
    def test_selected_decision_remains_null(self, tmp_path):
        """Test that submission templates have selected_decision=null."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Character Director template has selected_decision=null
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["selected_decision"] is None
        
        # Verify Workflow TD template has selected_decision=null
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["selected_decision"] is None
    
    def test_templates_do_not_approve_decisions(self, tmp_path):
        """Test that submission templates do not approve decisions."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        result = create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify result does not approve decisions
        assert result["decision_ready"] == False
        assert result["ready_for_real_role_input"] == True
        assert result["downstream_blocked"] == True
        assert result["production_accepted"] == False
        assert result["retry_gate_open"] == False
    
    def test_templates_do_not_open_retry_gate(self, tmp_path):
        """Test that submission templates do not open retry gate."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Read artifact_index to verify retry gate is not opened
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify retry gate is not opened
        assert updated_index.get("retry_gate_open") != True
        assert updated_index.get("retry_gate_open") == False
        assert updated_index.get("downstream_blocked") == True
        assert updated_index.get("production_accepted") == False
    
    def test_production_accepted_remains_false(self, tmp_path):
        """Test that submission templates keep production_accepted=false."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        result = create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify result keeps production_accepted=false
        assert result["production_accepted"] == False
        assert result["downstream_blocked"] == True
        assert result["retry_gate_open"] == False
        
        # Verify Character Director template keeps production_accepted=false
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_template_json = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
        
        with open(char_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["production_accepted"] == False
        assert template["downstream_blocked"] == True
        
        # Verify Workflow TD template keeps production_accepted=false
        workflow_template_json = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
        
        with open(workflow_template_json, 'r') as f:
            template = json.load(f)
        
        assert template["production_accepted"] == False
        assert template["downstream_blocked"] == True
    
    def test_markdown_instructions_are_created(self, tmp_path):
        """Test that Markdown instructions are created for both roles."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        result = create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify Markdown instructions exist
        assert len(result["instructions"]) == 2
        
        # Verify Character Director instructions exist
        role_decision_submissions_dir = tmp_path / "output" / "control" / "role_decision_submissions"
        char_instructions_path = role_decision_submissions_dir / "CHARACTER_DIRECTOR_DECISION_INSTRUCTIONS.md"
        
        assert char_instructions_path.exists()
        
        # Verify Workflow TD instructions exist
        workflow_instructions_path = role_decision_submissions_dir / "WORKFLOW_TD_DECISION_INSTRUCTIONS.md"
        
        assert workflow_instructions_path.exists()
    
    def test_artifact_index_includes_submission_contract(self, tmp_path):
        """Test that artifact_index includes submission contract section."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Read updated artifact_index
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify role_decision_submission_contract section exists
        assert "role_decision_submission_contract" in updated_index
        assert "character_director_submission_template" in updated_index["role_decision_submission_contract"]
        assert "workflow_td_submission_template" in updated_index["role_decision_submission_contract"]
        
        # Verify status is created
        assert updated_index["role_decision_submission_contract"]["status"] == "created"
        assert updated_index["role_decision_submission_contract"]["downstream_blocked"] == True
        assert updated_index["role_decision_submission_contract"]["production_accepted"] == False
        assert updated_index["role_decision_submission_contract"]["retry_gate_open"] == False
    
    def test_episode_ledger_records_submission_contract_created(self, tmp_path):
        """Test that episode_ledger records role_decision_submission_contract_created event."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Read episode_ledger
        with open(control_dir / "episode_ledger.json", 'r') as f:
            ledger = json.load(f)
        
        # Verify event was recorded
        assert "events" in ledger
        assert len(ledger["events"]) > 0
        
        # Find the role_decision_submission_contract_created event
        contract_events = [e for e in ledger["events"] if e["event_type"] == "role_decision_submission_contract_created"]
        assert len(contract_events) == 1
        
        event = contract_events[0]
        assert event["downstream_blocked"] == True
        assert event["production_accepted"] == False
        assert event["retry_gate_open"] == False
        assert event["comfyui_generation"] == False
        assert event["pipeline_action_rerun"] == False
        assert "Character Director" in event["roles"]
        assert "Workflow TD / ComfyUI Technical Director" in event["roles"]
    
    def test_validate_returns_ready_for_real_role_input_true_but_decision_ready_false(self, tmp_path):
        """Test that validate returns ready_for_real_role_input=true but decision_ready=false."""
        from app.production_cards.decision_submission import create_decision_submission_contract
        from app.production_cards.decision_submission import validate_decision_submission_contract
        from app.production_cards.role_review_packets import create_role_review_packets
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
        
        # Create decision submission contract
        create_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Validate decision submission contract
        validation_result = validate_decision_submission_contract(str(tmp_path), json_output=True)
        
        # Verify validation returns ready_for_real_role_input=true but decision_ready=false
        assert validation_result["status"] == "valid"
        assert validation_result["submission_templates_found"] == 2
        assert validation_result["ready_for_real_role_input"] == True
        assert validation_result["decision_ready"] == False
        assert validation_result["retry_gate_open"] == False
        assert validation_result["downstream_blocked"] == True
        assert validation_result["production_accepted"] == False
        assert len(validation_result["validation_errors"]) == 0
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that decision_submission module has no hardcoded Alya/Mir Erdan."""
        import app.production_cards.decision_submission as decision_submission_module
        import inspect
        
        # Get the source code of the decision_submission module
        source = inspect.getsource(decision_submission_module)
        
        # Verify no hardcoded project-specific names
        assert "Mir Erdan" not in source
        
        # The module should not hardcode these names - they should come from input data
        # Any occurrence of "Alya" should be in test data or comments, not in core logic
