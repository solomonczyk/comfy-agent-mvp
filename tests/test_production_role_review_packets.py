"""Tests for production role review evidence packets module."""

import json
from pathlib import Path
import pytest


class TestProductionRoleReviewPackets:
    """Test suite for production role review evidence packet generation."""
    
    def test_creates_character_director_evidence_packet(self, tmp_path):
        """Test that create-role-review-packets creates Character Director evidence packet."""
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
        
        # Create role review evidence packets
        result = create_role_review_packets(str(tmp_path), json_output=True)
        
        # Verify Character Director evidence packet was created
        assert result["status"] == "completed"
        assert result["evidence_packets_created"] == 2
        assert len(result["packets"]) == 2
        
        # Verify JSON file exists
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        assert char_director_json.exists()
        
        # Verify packet is evidence only
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        assert packet["packet_type"] == "character_director_identity_review"
        assert packet["evidence_only"] == True
        assert packet["not_a_decision"] == True
    
    def test_creates_workflow_td_evidence_packet(self, tmp_path):
        """Test that create-role-review-packets creates Workflow TD evidence packet."""
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Verify Workflow TD evidence packet was created
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        workflow_td_json = role_review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
        
        assert workflow_td_json.exists()
        
        # Verify packet is evidence only
        with open(workflow_td_json, 'r') as f:
            packet = json.load(f)
        
        assert packet["packet_type"] == "workflow_td_identity_workflow_review"
        assert packet["evidence_only"] == True
        assert packet["not_a_decision"] == True
    
    def test_preserves_real_project_character_data(self, tmp_path):
        """Test that Character Director evidence packet preserves real project character data."""
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
                    "reference_character": "CustomChar",
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
                    "reference_character": "CustomChar",
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read Character Director evidence packet
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        # Verify real project character data is preserved (not hardcoded)
        assert packet["character_name"] == "CustomChar"
        assert packet["character_reference"] == "CustomChar"
        assert packet["project_specific_data_allowed"] == True
    
    def test_includes_pending_decision_paths(self, tmp_path):
        """Test that evidence packets include pending decision paths."""
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.materializer import ProductionCardMaterializer
        from app.production_cards.role_decisions import create_pending_role_decisions
        
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
        
        # Create pending role decisions first
        create_pending_role_decisions(str(tmp_path), json_output=True)
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read Character Director evidence packet
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        # Verify pending decision path is included
        assert "pending_decision_path" in packet
        assert "role_decisions" in packet["pending_decision_path"]
        assert "character_director_identity_decision.json" in packet["pending_decision_path"]
    
    def test_includes_work_order_paths(self, tmp_path):
        """Test that evidence packets include work order paths."""
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
        
        # Read Character Director evidence packet
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        # Verify work order path is included
        assert "work_order_path" in packet
        assert "work_orders" in packet["work_order_path"]
        assert "character_director_identity_review.json" in packet["work_order_path"]
    
    def test_includes_identity_failure_evidence(self, tmp_path):
        """Test that evidence packets include identity QA failure evidence."""
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read Character Director evidence packet
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        # Verify identity failure evidence is included
        assert "identity_qa_failure_summary" in packet
        assert packet["issue"] == "identity_qa_failed"
        assert packet["blocked_shot"] == "shot01"
    
    def test_packets_do_not_approve_decisions(self, tmp_path):
        """Test that evidence packets do not approve decisions."""
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
        
        # Create role review evidence packets
        result = create_role_review_packets(str(tmp_path), json_output=True)
        
        # Verify result does not approve decisions
        assert result["evidence_only"] == True
        assert result["not_decisions"] == True
        assert result["downstream_blocked"] == True
        assert result["production_accepted"] == False
        
        # Verify Character Director packet does not approve
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        assert packet["evidence_only"] == True
        assert packet["not_a_decision"] == True
        assert "selected_decision" not in packet
        assert "decision_status" not in packet
    
    def test_packets_do_not_open_retry_gate(self, tmp_path):
        """Test that evidence packets do not open retry gate."""
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read artifact_index to verify retry gate is not opened
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify retry gate is not opened
        assert updated_index.get("retry_gate_open") != True
        assert updated_index.get("downstream_blocked") == True
        assert updated_index.get("production_accepted") == False
    
    def test_packets_keep_production_accepted_false(self, tmp_path):
        """Test that evidence packets keep production_accepted=false."""
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
        
        # Create role review evidence packets
        result = create_role_review_packets(str(tmp_path), json_output=True)
        
        # Verify result keeps production_accepted=false
        assert result["production_accepted"] == False
        assert result["downstream_blocked"] == True
        
        # Verify Character Director packet keeps production_accepted=false
        role_review_packets_dir = tmp_path / "output" / "control" / "role_review_packets"
        char_director_json = role_review_packets_dir / "character_director_identity_evidence_packet.json"
        
        with open(char_director_json, 'r') as f:
            packet = json.load(f)
        
        assert packet["production_accepted"] == False
        assert packet["downstream_blocked"] == True
        
        # Verify Workflow TD packet keeps production_accepted=false
        workflow_td_json = role_review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
        
        with open(workflow_td_json, 'r') as f:
            packet = json.load(f)
        
        assert packet["production_accepted"] == False
        assert packet["downstream_blocked"] == True
    
    def test_artifact_index_includes_packet_paths(self, tmp_path):
        """Test that artifact_index includes evidence packet paths."""
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read updated artifact_index
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify role_review_packets section exists
        assert "role_review_packets" in updated_index
        assert "character_director_packet" in updated_index["role_review_packets"]
        assert "workflow_td_packet" in updated_index["role_review_packets"]
        
        # Verify status is created
        assert updated_index["role_review_packets"]["status"] == "created"
        assert updated_index["role_review_packets"]["downstream_blocked"] == True
        assert updated_index["role_review_packets"]["production_accepted"] == False
        assert updated_index["role_review_packets"]["evidence_only"] == True
    
    def test_episode_ledger_records_role_review_packets_created(self, tmp_path):
        """Test that episode_ledger records role_review_packets_created event."""
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Read episode_ledger
        with open(control_dir / "episode_ledger.json", 'r') as f:
            ledger = json.load(f)
        
        # Verify event was recorded
        assert "events" in ledger
        assert len(ledger["events"]) > 0
        
        # Find the role_review_packets_created event
        packet_events = [e for e in ledger["events"] if e["event_type"] == "role_review_packets_created"]
        assert len(packet_events) == 1
        
        event = packet_events[0]
        assert event["downstream_blocked"] == True
        assert event["production_accepted"] == False
        assert event["comfyui_generation"] == False
        assert event["pipeline_action_rerun"] == False
        assert event["evidence_only"] == True
        assert "Character Director" in event["roles"]
        assert "Workflow TD / ComfyUI Technical Director" in event["roles"]
    
    def test_validate_role_review_packets_returns_valid_but_decision_ready_false(self, tmp_path):
        """Test that validate-role-review-packets returns valid but decision_ready=false."""
        from app.production_cards.role_review_packets import create_role_review_packets
        from app.production_cards.role_review_packets import validate_role_review_packets
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
        
        # Create role review evidence packets
        create_role_review_packets(str(tmp_path), json_output=True)
        
        # Validate role review packets
        validation_result = validate_role_review_packets(str(tmp_path), json_output=True)
        
        # Verify validation returns valid but decision_ready=false
        assert validation_result["status"] == "valid"
        assert validation_result["packets_found"] == 2
        assert validation_result["decision_ready"] == False
        assert validation_result["downstream_blocked"] == True
        assert validation_result["production_accepted"] == False
        assert validation_result["evidence_only"] == True
        assert validation_result["not_decisions"] == True
        assert len(validation_result["missing_required_evidence"]) == 0
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that role_review_packets module has no hardcoded Alya/Mir Erdan."""
        import app.production_cards.role_review_packets as role_review_packets_module
        import inspect
        
        # Get the source code of the role_review_packets module
        source = inspect.getsource(role_review_packets_module)
        
        # Verify no hardcoded project-specific names
        assert "Mir Erdan" not in source
        
        # The module should not hardcode these names - they should come from input data
        # Any occurrence of "Alya" should be in test data or comments, not in core logic
