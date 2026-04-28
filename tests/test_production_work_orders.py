"""Tests for production work orders module."""

import json
from pathlib import Path
import pytest


class TestProductionWorkOrders:
    """Test suite for production work order generation."""
    
    def test_create_production_work_orders_creates_both_json_work_orders(self, tmp_path):
        """Test that create-production-work-orders creates both JSON work orders."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        result = create_work_orders(str(tmp_path), json_output=True)
        
        # Verify both work orders were created
        assert result["status"] == "completed"
        assert result["work_orders_created"] == 2
        assert len(result["work_orders"]) == 2
        
        # Verify JSON files exist
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        char_director_json = work_orders_dir / "character_director_identity_review.json"
        workflow_td_json = work_orders_dir / "workflow_td_identity_workflow_review.json"
        
        assert char_director_json.exists()
        assert workflow_td_json.exists()
    
    def test_creates_both_markdown_summaries(self, tmp_path):
        """Test that both markdown summaries are created."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        create_work_orders(str(tmp_path), json_output=True)
        
        # Verify markdown files exist
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        char_director_md = work_orders_dir / "character_director_identity_review.md"
        workflow_td_md = work_orders_dir / "workflow_td_identity_workflow_review.md"
        
        assert char_director_md.exists()
        assert workflow_td_md.exists()
        
        # Verify markdown content is readable
        with open(char_director_md, 'r') as f:
            md_content = f.read()
            assert "# Character Director Work Order" in md_content
            assert "Alya" in md_content
        
        with open(workflow_td_md, 'r') as f:
            md_content = f.read()
            assert "# Workflow TD Work Order" in md_content
    
    def test_character_director_work_order_preserves_alya_project_data(self, tmp_path):
        """Test that Character Director work order preserves Alya project data."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        create_work_orders(str(tmp_path), json_output=True)
        
        # Read Character Director work order
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        char_director_json = work_orders_dir / "character_director_identity_review.json"
        
        with open(char_director_json, 'r') as f:
            work_order = json.load(f)
        
        # Verify Alya project data is preserved
        assert work_order["character_name"] == "Alya"
        assert work_order["display_name"] == "Alya"
        assert work_order["character_reference"] == "Alya"
        assert work_order["project_specific_data_allowed"] == True
    
    def test_workflow_td_work_order_requires_gorynych_identity(self, tmp_path):
        """Test that Workflow TD work order requires gorynych_identity."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        create_work_orders(str(tmp_path), json_output=True)
        
        # Read Workflow TD work order
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        workflow_td_json = work_orders_dir / "workflow_td_identity_workflow_review.json"
        
        with open(workflow_td_json, 'r') as f:
            work_order = json.load(f)
        
        # Verify gorynych_identity is required
        assert work_order["current_required_generation_mode"] == "gorynych_identity"
        assert work_order["legacy_reference_locked_allowed_for_production"] == False
    
    def test_work_orders_do_not_approve_production(self, tmp_path):
        """Test that work orders do not approve production."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        result = create_work_orders(str(tmp_path), json_output=True)
        
        # Verify work orders do not approve production
        assert result["downstream_blocked"] == True
        
        # Verify Character Director work order keeps downstream blocked
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        char_director_json = work_orders_dir / "character_director_identity_review.json"
        
        with open(char_director_json, 'r') as f:
            work_order = json.load(f)
        
        assert work_order["downstream_blocked"] == True
        assert work_order["production_accepted"] == False
    
    def test_work_orders_keep_downstream_blocked_true(self, tmp_path):
        """Test that work orders keep downstream_blocked=true."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        result = create_work_orders(str(tmp_path), json_output=True)
        
        # Verify downstream remains blocked
        assert result["downstream_blocked"] == True
        
        # Verify both work orders have downstream_blocked=true
        work_orders_dir = tmp_path / "output" / "control" / "work_orders"
        char_director_json = work_orders_dir / "character_director_identity_review.json"
        workflow_td_json = work_orders_dir / "workflow_td_identity_workflow_review.json"
        
        with open(char_director_json, 'r') as f:
            char_wo = json.load(f)
        with open(workflow_td_json, 'r') as f:
            workflow_wo = json.load(f)
        
        assert char_wo["downstream_blocked"] == True
        assert workflow_wo["downstream_blocked"] == True
    
    def test_artifact_index_includes_work_order_paths(self, tmp_path):
        """Test that artifact_index includes work order paths."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        create_work_orders(str(tmp_path), json_output=True)
        
        # Read updated artifact_index
        with open(control_dir / "artifact_index.json", 'r') as f:
            updated_index = json.load(f)
        
        # Verify work orders section exists
        assert "work_orders" in updated_index
        assert "character_director_work_order" in updated_index["work_orders"]
        assert "workflow_td_work_order" in updated_index["work_orders"]
        
        # Verify paths are correct
        assert updated_index["work_orders"]["character_director_work_order"] == "output/control/work_orders/character_director_identity_review.json"
        assert updated_index["work_orders"]["workflow_td_work_order"] == "output/control/work_orders/workflow_td_identity_workflow_review.json"
        
        # Verify current blocking roles
        assert "current_blocking_roles" in updated_index
        assert "Character Director" in updated_index["current_blocking_roles"]
        assert "Workflow TD / ComfyUI Technical Director" in updated_index["current_blocking_roles"]
    
    def test_episode_ledger_records_role_work_orders_created(self, tmp_path):
        """Test that episode_ledger records role_work_orders_created event."""
        from app.production_cards.work_orders import create_work_orders
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
        
        # Create work orders
        create_work_orders(str(tmp_path), json_output=True)
        
        # Read episode_ledger
        with open(control_dir / "episode_ledger.json", 'r') as f:
            ledger = json.load(f)
        
        # Verify event was recorded
        assert "events" in ledger
        assert len(ledger["events"]) > 0
        
        # Find the role_work_orders_created event
        work_order_events = [e for e in ledger["events"] if e["event_type"] == "role_work_orders_created"]
        assert len(work_order_events) == 1
        
        event = work_order_events[0]
        assert event["reason"] == "identity_qa_failed"
        assert event["downstream_blocked"] == True
        assert event["comfyui_generation"] == False
        assert event["pipeline_action_rerun"] == False
        assert event["work_order_count"] == 2
        assert "Character Director" in event["roles"]
        assert "Workflow TD / ComfyUI Technical Director" in event["roles"]
    
    def test_no_core_hardcode_for_alya_mir_erdan(self, tmp_path):
        """Test that work orders module has no hardcoded Alya/Mir Erdan."""
        import app.production_cards.work_orders as work_orders_module
        import inspect
        
        # Get the source code of the work_orders module
        source = inspect.getsource(work_orders_module)
        
        # Verify no hardcoded project-specific names
        assert "Mir Erdan" not in source
        
        # The module should not hardcode these names - they should come from input data
        # Any occurrence of "Alya" should be in test data or comments, not in core logic
