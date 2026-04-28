"""
Production Card Materialization Tests

Tests for the production card materialization system.
"""

import json
import pytest
from pathlib import Path
from app.production_cards.materializer import ProductionCardMaterializer, materialize_production_cards
from app.production_cards.router import ProductionRouter


class TestProductionCardMaterialization:
    """Test production card materialization."""

    def test_materialize_production_cards_creates_project_card_folders(self, tmp_path):
        """Test that materialize-production-cards creates project card folders."""
        # Create output/control directory structure with artifact_index
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": []
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Check that card folders were created
        cards_dir = tmp_path / "cards"
        assert cards_dir.exists()
        
        expected_folders = [
            "project", "episodes", "scenarios", "shots", "characters",
            "environments", "lighting", "camera", "workflows", "qa"
        ]
        for folder in expected_folders:
            assert (cards_dir / folder).exists()

    def test_creates_required_current_project_cards(self, tmp_path):
        """Test that materialize-production-cards creates required current project cards."""
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "status": "preflight_complete"
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "scene_goal": "Test goal",
                    "voiceover_text": "Test voiceover"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Check that required cards were created
        # With 1 shot, we expect: Project, Episode, Scenario (1), Character, Shot (1), Workflow, QA = 7 cards
        assert result["cards_created"] >= 7
        
        # Check that specific card files exist
        cards_dir = tmp_path / "cards"
        assert (cards_dir / "project" / "project_card.json").exists()
        assert (cards_dir / "episodes" / "episode_card.json").exists()
        assert (cards_dir / "characters" / "character_card.json").exists()
        assert (cards_dir / "shots" / "shot01.json").exists()
        assert (cards_dir / "workflows" / "workflow_card.json").exists()
        assert (cards_dir / "qa" / "qa_card.json").exists()

    def test_shot01_card_records_identity_qa_failed(self, tmp_path):
        """Test that shot01 card records identity_qa_failed."""
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "status": "identity_qa_failed",
                    "frame_qc_passed": True,
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
                    "scene_goal": "Test goal",
                    "voiceover_text": "Test voiceover"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Read the shot01 card
        shot01_path = tmp_path / "cards" / "shots" / "shot01.json"
        with open(shot01_path, 'r') as f:
            shot01_card = json.load(f)
        
        # Verify identity failure is recorded
        assert shot01_card["status"] == "blocked"
        assert shot01_card["frame_qc_passed"] == True
        assert shot01_card["identity_consistency_passed"] == False
        assert shot01_card["production_accepted"] == False
        assert shot01_card["blocking_reason"] == "identity_qa_failed"
        assert shot01_card["next_action"] == "approve_identity_workflow_before_retry"
        assert isinstance(shot01_card["responsible_roles"], list)
        assert "Character Director" in shot01_card["responsible_roles"]
        assert "Workflow TD / ComfyUI Technical Director" in shot01_card["responsible_roles"]

    def test_character_card_requires_character_director_approval(self, tmp_path):
        """Test that CharacterCard requires Character Director approval."""
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Read the character card
        character_path = tmp_path / "cards" / "characters" / "character_card.json"
        with open(character_path, 'r') as f:
            character_card = json.load(f)
        
        # Verify Character Director approval requirements
        assert character_card["status"] == "needs_role_work"  # Not approved due to identity failure
        assert character_card["identity_reference_required"] == True
        assert character_card["identity_workflow_approval_required"] == True
        assert character_card["owner_role"] == "Character Director"
        assert character_card["approval_required_by"] == "Character Director"

    def test_workflow_recipe_card_requires_workflow_td_approval(self, tmp_path):
        """Test that WorkflowRecipeCard requires Workflow TD approval."""
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Read the workflow card
        workflow_path = tmp_path / "cards" / "workflows" / "workflow_card.json"
        with open(workflow_path, 'r') as f:
            workflow_card = json.load(f)
        
        # Verify Workflow TD approval requirements
        assert workflow_card["status"] == "needs_role_work"  # Not approved due to identity failure
        assert workflow_card["generation_mode"] == "gorynych_identity"
        assert workflow_card["legacy_reference_locked_allowed_for_production"] == False
        assert workflow_card["owner_role"] == "Workflow TD / ComfyUI Technical Director"
        assert workflow_card["approval_required_by"] == "Workflow TD / ComfyUI Technical Director"

    def test_qa_requirement_card_blocks_downstream_on_identity_failure(self, tmp_path):
        """Test that QARequirementCard blocks downstream on identity failure."""
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": []
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        materializer = ProductionCardMaterializer()
        result = materializer.materialize_project_cards(str(tmp_path))
        
        # Read the QA card
        qa_path = tmp_path / "cards" / "qa" / "qa_card.json"
        with open(qa_path, 'r') as f:
            qa_card = json.load(f)
        
        # Verify QA requirements
        assert qa_card["frame_qc_required"] == True
        assert qa_card["identity_consistency_required"] == True
        assert qa_card["production_acceptance_requires_identity_qa"] == True
        assert qa_card["downstream_blocked_if_identity_failed"] == True

    def test_route_production_tasks_after_materialization_reports_cards_found_greater_than_zero(self, tmp_path):
        """Test that route-production-tasks after materialization reports cards_found > 0."""
        from app.production_cards.router import route_production_cards
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "status": "preflight_complete"
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "shots": [
                {
                    "shot_id": "shot01",
                    "scene_goal": "Test goal",
                    "voiceover_text": "Test voiceover"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Route production tasks
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Verify cards_found > 0
        assert result["summary"]["cards_found"] > 0

    def test_identity_failure_route_remains_character_director_and_workflow_td(self, tmp_path):
        """Test that identity failure route remains Character Director + Workflow TD."""
        from app.production_cards.router import ProductionRouter
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "TestCharacter",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Route production tasks
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find identity failure route
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        # Verify route still goes to Character Director + Workflow TD
        assert identity_route is not None
        assert isinstance(identity_route["responsible_role"], list)
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]

    def test_no_project_specific_hardcode_added_to_core_materializer(self, tmp_path):
        """Test that no project-specific hardcode is added to core materializer logic."""
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Alya",
                    "status": "preflight_complete"
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Alya's Awakening",
            "shots": [
                {
                    "shot_id": "shot01",
                    "scene_goal": "Introduce Alya in a serene forest setting",
                    "voiceover_text": "Alya walks peacefully"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Verify that project-specific names are sanitized in cards
        project_card_path = tmp_path / "cards" / "project" / "project_card.json"
        with open(project_card_path, 'r') as f:
            project_card = json.load(f)
        
        # Project-specific names should be replaced with generic placeholders
        assert "Alya" not in project_card.get("title", "")
        assert "Protagonist" in project_card.get("title", "") or "Alya's" not in project_card.get("title", "")

    def test_materialized_cards_validate_cleanly(self, tmp_path):
        """Test that materialized cards validate cleanly without project-specific hardcode."""
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode with Protagonist",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "preflight_complete"
                }
            ]
        }
        
        episode_plan = {
            "episode_id": "ep01",
            "episode_title": "Test Episode with Protagonist",
            "shots": [
                {
                    "shot_id": "shot01",
                    "scene_goal": "Test goal with Protagonist",
                    "voiceover_text": "Test voiceover"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validation_result = validate_production_cards(str(tmp_path), json_output=True)
        
        # All cards should validate cleanly
        assert validation_result["status"] == "passed"
        assert validation_result["summary"]["failed_checks"] == 0

    def test_blocked_cards_can_be_validation_passed(self, tmp_path):
        """Test that blocked cards can pass validation."""
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "frame_qc_passed": True,
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
                    "scene_goal": "Test goal",
                    "voiceover_text": "Test voiceover"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        with open(control_dir / "episode_plan.json", "w") as f:
            json.dump(episode_plan, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validation_result = validate_production_cards(str(tmp_path), json_output=True)
        
        # Validation should pass even though cards are blocked
        assert validation_result["status"] == "passed"
        assert validation_result["summary"]["failed_checks"] == 0

    def test_needs_role_work_cards_can_be_validation_passed(self, tmp_path):
        """Test that needs_role_work cards can pass validation."""
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validation_result = validate_production_cards(str(tmp_path), json_output=True)
        
        # Validation should pass even though CharacterCard is needs_role_work
        assert validation_result["status"] == "passed"
        assert validation_result["summary"]["failed_checks"] == 0

    def test_validation_passed_does_not_imply_generation_ready_true(self, tmp_path):
        """Test that validation passed does not imply generation_ready=true."""
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validation_result = validate_production_cards(str(tmp_path), json_output=True)
        
        # Validation can pass but generation_ready should be false
        assert validation_result["status"] == "passed"
        assert validation_result["generation_ready"] == False

    def test_generation_ready_remains_false_after_identity_failure(self, tmp_path):
        """Test that generation_ready remains false after identity failure."""
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validation_result = validate_production_cards(str(tmp_path), json_output=True)
        
        # generation_ready should be false due to identity failure
        assert validation_result["generation_ready"] == False

    def test_route_remains_character_director_and_workflow_td(self, tmp_path):
        """Test that route remains Character Director + Workflow TD after validation repair."""
        from app.production_cards.router import ProductionRouter
        from app.production_cards.validator import validate_production_cards
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Validate cards
        validate_production_cards(str(tmp_path), json_output=True)
        
        # Route production tasks
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find identity failure route
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        # Verify route still goes to Character Director + Workflow TD
        assert identity_route is not None
        assert isinstance(identity_route["responsible_role"], list)
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]

    def test_no_production_accepted_true_is_introduced(self, tmp_path):
        """Test that no production_accepted=true is introduced during materialization."""
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Read shot01 card
        shot01_path = tmp_path / "cards" / "shots" / "shot01.json"
        with open(shot01_path, 'r') as f:
            shot01_card = json.load(f)
        
        # Verify production_accepted is false
        assert shot01_card["production_accepted"] == False

    def test_no_downstream_unblock_is_introduced(self, tmp_path):
        """Test that no downstream unblock is introduced during materialization."""
        from app.production_cards.router import ProductionRouter
        
        # Create output/control directory structure with identity failure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "reference_character": "Protagonist",
                    "status": "identity_qa_failed",
                    "identity_consistency_passed": False,
                    "identity_qa_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        # Materialize cards
        materializer = ProductionCardMaterializer()
        materializer.materialize_project_cards(str(tmp_path))
        
        # Route production tasks
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Verify downstream remains blocked
        assert result["downstream_blocked"] == True
        assert result["generation_ready"] == False

