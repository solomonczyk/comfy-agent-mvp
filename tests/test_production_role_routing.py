"""
Production Card Role Routing Tests

Tests for the production card routing system.
"""

import json
import pytest
from pathlib import Path
from app.production_cards.router import ProductionRouter, route_production_cards


class TestProductionRoleRouting:
    """Test production card role routing."""

    def test_route_production_tasks_returns_structured_json(self, tmp_path):
        """Test that route-production-tasks returns structured JSON."""
        # Create a simple card structure
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        project_card = {
            "card_id": "project_001",
            "card_type": "ProjectCard",
            "project_id": "project_001",
            "owner_role": "Executive Producer / Product Owner",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "title": "Test Project",
                "description": "A test project"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Executive Producer / Product Owner",
            "next_action_if_missing": "Create ProjectCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "title": "Test Project",
            "description": "A test project",
            "executive_producer": "Test Producer",
            "target_deliverables": [],
            "timeline": {}
        }
        
        project_dir = cards_dir / "project"
        project_dir.mkdir()
        with open(project_dir / "project_001.json", "w") as f:
            json.dump(project_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Check structure
        assert "status" in result
        assert "project_root" in result
        assert "generation_ready" in result
        assert "downstream_blocked" in result
        assert "summary" in result
        assert "routes" in result
        assert "next_actions" in result
        
        # Check summary structure
        assert "cards_found" in result["summary"]
        assert "issues_found" in result["summary"]
        assert "blocked_count" in result["summary"]
        assert "roles_needed" in result["summary"]

    def test_draft_character_card_routes_to_character_director(self, tmp_path):
        """Test that draft CharacterCard routes to Character Director."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        character_card = {
            "card_id": "char_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Character",
                "visual_reference_paths": [],
                "physical_description": "Test description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Character",
            "character_director": "Test Director",
            "visual_reference_paths": [],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "char_001.json", "w") as f:
            json.dump(character_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the CharacterCard route
        char_route = None
        for route in result["routes"]:
            if route["card_type"] == "CharacterCard":
                char_route = route
                break
        
        assert char_route is not None
        assert char_route["issue_type"] == "draft_card"
        assert char_route["responsible_role"] == "Character Director"
        assert char_route["recommended_action"] == "complete_and_approve_card"
        assert char_route["downstream_blocked"] == True

    def test_draft_workflow_recipe_card_routes_to_workflow_td(self, tmp_path):
        """Test that draft WorkflowRecipeCard routes to Workflow TD."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        workflow_card = {
            "card_id": "workflow_001",
            "card_type": "WorkflowRecipeCard",
            "project_id": "project_001",
            "owner_role": "Workflow TD / ComfyUI Technical Director",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Workflow",
                "workflow_graph": {}
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Workflow TD / ComfyUI Technical Director",
            "next_action_if_missing": "Create WorkflowRecipeCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Workflow",
            "workflow_td": "Test TD",
            "workflow_graph": {},
            "node_parameters": {},
            "input_mappings": {},
            "output_mappings": {},
            "resource_requirements": {},
            "estimated_generation_time": 0
        }
        
        workflows_dir = cards_dir / "workflows"
        workflows_dir.mkdir()
        with open(workflows_dir / "workflow_001.json", "w") as f:
            json.dump(workflow_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the WorkflowRecipeCard route
        workflow_route = None
        for route in result["routes"]:
            if route["card_type"] == "WorkflowRecipeCard":
                workflow_route = route
                break
        
        assert workflow_route is not None
        assert workflow_route["issue_type"] == "draft_card"
        assert workflow_route["responsible_role"] == "Workflow TD / ComfyUI Technical Director"
        assert workflow_route["recommended_action"] == "complete_and_approve_card"
        assert workflow_route["downstream_blocked"] == True

    def test_draft_scenario_card_routes_to_screenwriter(self, tmp_path):
        """Test that draft ScenarioCard routes to Screenwriter."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        scenario_card = {
            "card_id": "scenario_001",
            "card_type": "ScenarioCard",
            "project_id": "project_001",
            "owner_role": "Screenwriter / Script Agent",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "title": "Test Scenario",
                "narrative_beat": "Test beat"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Screenwriter / Script Agent",
            "next_action_if_missing": "Create ScenarioCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "title": "Test Scenario",
            "screenwriter": "Test Screenwriter",
            "narrative_beat": "Test beat",
            "location_description": "Test location",
            "involved_characters": [],
            "shot_references": [],
            "environment_reference": "env_001"
        }
        
        scenarios_dir = cards_dir / "scenarios"
        scenarios_dir.mkdir()
        with open(scenarios_dir / "scenario_001.json", "w") as f:
            json.dump(scenario_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the ScenarioCard route
        scenario_route = None
        for route in result["routes"]:
            if route["card_type"] == "ScenarioCard":
                scenario_route = route
                break
        
        assert scenario_route is not None
        assert scenario_route["issue_type"] == "draft_card"
        assert scenario_route["responsible_role"] == "Screenwriter / Script Agent"
        assert scenario_route["recommended_action"] == "complete_and_approve_card"
        assert scenario_route["downstream_blocked"] == True

    def test_draft_shot_card_routes_to_shot_designer(self, tmp_path):
        """Test that draft ShotCard routes to Shot Designer."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        shot_card = {
            "card_id": "shot_001",
            "card_type": "ShotCard",
            "project_id": "project_001",
            "owner_role": "Shot Designer / Storyboard Agent",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "shot_type": "medium",
                "action_description": "Test action"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Shot Designer / Storyboard Agent",
            "next_action_if_missing": "Create ShotCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "shot_type": "medium",
            "action_description": "Test action",
            "duration_seconds": 5,
            "character_reference": "char_001",
            "environment_reference": "env_001",
            "camera_reference": "camera_001",
            "lighting_reference": "lighting_001",
            "style_reference": "style_001"
        }
        
        shots_dir = cards_dir / "shots"
        shots_dir.mkdir()
        with open(shots_dir / "shot_001.json", "w") as f:
            json.dump(shot_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the ShotCard route
        shot_route = None
        for route in result["routes"]:
            if route["card_type"] == "ShotCard":
                shot_route = route
                break
        
        assert shot_route is not None
        assert shot_route["issue_type"] == "draft_card"
        assert shot_route["responsible_role"] == "Shot Designer / Storyboard Agent"
        assert shot_route["recommended_action"] == "complete_and_approve_card"
        assert shot_route["downstream_blocked"] == True

    def test_draft_lighting_card_routes_to_cinematographer(self, tmp_path):
        """Test that draft LightingCard routes to Cinematographer."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        lighting_card = {
            "card_id": "lighting_001",
            "card_type": "LightingCard",
            "project_id": "project_001",
            "owner_role": "Cinematographer / Camera + Lighting Director",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Lighting",
                "mood": "Test mood"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Cinematographer / Camera + Lighting Director",
            "next_action_if_missing": "Create LightingCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Lighting",
            "cinematographer": "Test Cinematographer",
            "mood": "Test mood",
            "light_sources": [],
            "color_temperature": 5500,
            "intensity": 1.0,
            "shadow_characteristics": "soft"
        }
        
        lighting_dir = cards_dir / "lighting"
        lighting_dir.mkdir()
        with open(lighting_dir / "lighting_001.json", "w") as f:
            json.dump(lighting_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the LightingCard route
        lighting_route = None
        for route in result["routes"]:
            if route["card_type"] == "LightingCard":
                lighting_route = route
                break
        
        assert lighting_route is not None
        assert lighting_route["issue_type"] == "draft_card"
        assert lighting_route["responsible_role"] == "Cinematographer / Camera + Lighting Director"
        assert lighting_route["recommended_action"] == "complete_and_approve_card"
        assert lighting_route["downstream_blocked"] == True

    def test_missing_reference_routes_to_correct_owner_role(self, tmp_path):
        """Test that missing reference routes to correct owner role."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        character_card = {
            "card_id": "char_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            "status": "needs_references",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Character",
                "visual_reference_paths": [],
                "physical_description": "Test description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Character",
            "character_director": "Test Director",
            "visual_reference_paths": [],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "char_001.json", "w") as f:
            json.dump(character_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the CharacterCard route
        char_route = None
        for route in result["routes"]:
            if route["card_type"] == "CharacterCard":
                char_route = route
                break
        
        assert char_route is not None
        assert char_route["issue_type"] == "missing_reference"
        assert char_route["responsible_role"] == "Character Director"
        assert char_route["recommended_action"] == "add_required_references"

    def test_invalid_card_routes_to_owner_with_fix_validation_errors(self, tmp_path):
        """Test that invalid card routes to owner with fix_validation_errors."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create an invalid card (missing required field - status)
        invalid_card = {
            "card_id": "invalid_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            # Missing status field - will fail validation
            "version": "1.0.0",
            "required_inputs": {},
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Character",
            "character_director": "Test Director",
            "visual_reference_paths": [],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "invalid_001.json", "w") as f:
            json.dump(invalid_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the invalid card route
        invalid_route = None
        for route in result["routes"]:
            if route["card_id"] == "invalid_001":
                invalid_route = route
                break
        
        assert invalid_route is not None
        assert invalid_route["issue_type"] == "invalid_card"
        assert invalid_route["responsible_role"] == "Character Director"
        assert invalid_route["recommended_action"] == "fix_validation_errors"

    def test_generation_ready_false_creates_downstream_blocked_true(self, tmp_path):
        """Test that generation_ready=false creates downstream_blocked=true."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        character_card = {
            "card_id": "char_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Character",
                "visual_reference_paths": [],
                "physical_description": "Test description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Character",
            "character_director": "Test Director",
            "visual_reference_paths": [],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "char_001.json", "w") as f:
            json.dump(character_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        assert result["generation_ready"] == False
        assert result["downstream_blocked"] == True

    def test_approved_cards_produce_ready_no_blocking_route(self, tmp_path):
        """Test that approved cards produce ready/no blocking route."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        character_card = {
            "card_id": "char_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            "status": "approved",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Test Character",
                "visual_reference_paths": ["ref1.jpg", "ref2.jpg"],
                "physical_description": "Test description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Test Character",
            "character_director": "Test Director",
            "visual_reference_paths": ["ref1.jpg", "ref2.jpg"],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "char_001.json", "w") as f:
            json.dump(character_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Approved cards should not have routes
        char_route = None
        for route in result["routes"]:
            if route["card_type"] == "CharacterCard":
                char_route = route
                break
        
        assert char_route is None
        assert result["status"] == "ready" or result["status"] == "routed"

    def test_identity_qa_failed_routes_to_character_director_and_workflow_td(self, tmp_path):
        """Test that identity_qa_failed routes to Character Director + Workflow TD."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create project metadata with identity_qa_failed
        metadata = {
            "identity_qa_failed": True,
            "production_accepted": False,
            "rejection_reason": "Identity drift detected"
        }
        
        with open(tmp_path / "project_metadata.json", "w") as f:
            json.dump(metadata, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the identity QA failure route
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        assert identity_route is not None
        assert isinstance(identity_route["responsible_role"], list)
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]
        assert identity_route["recommended_action"] == "approve_identity_workflow_before_retry"
        assert identity_route["downstream_blocked"] == True

    def test_no_alya_mir_erdan_hardcode_in_router_logic(self, tmp_path):
        """Test that no Alya/Mir Erdan hardcode is added in router logic."""
        # Read the router source code to check for hardcode
        router_path = Path(__file__).parent.parent / "app" / "production_cards" / "router.py"
        with open(router_path, "r") as f:
            router_content = f.read().lower()
        
        # Check for project-specific names
        assert "alya" not in router_content
        assert "mir erdan" not in router_content
        
        # Create a card with these names to ensure router doesn't special-case them
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        character_card = {
            "card_id": "char_001",
            "card_type": "CharacterCard",
            "project_id": "project_001",
            "owner_role": "Character Director",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "name": "Alya",  # Using the name to test it's not hardcoded
                "visual_reference_paths": [],
                "physical_description": "Test description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
            "name": "Alya",
            "character_director": "Test Director",
            "visual_reference_paths": [],
            "physical_description": "Test description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {}
        }
        
        characters_dir = cards_dir / "characters"
        characters_dir.mkdir()
        with open(characters_dir / "char_001.json", "w") as f:
            json.dump(character_card, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Should route normally based on status, not name
        char_route = None
        for route in result["routes"]:
            if route["card_type"] == "CharacterCard":
                char_route = route
                break
        
        assert char_route is not None
        assert char_route["responsible_role"] == "Character Director"
        # Should not have any special handling for the name "Alya"

    def test_real_identity_failure_from_artifact_index_routes_to_character_director_and_workflow_td(self, tmp_path):
        """Test that identity failure in artifact_index routes to Character Director + Workflow TD."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index.json with identity failure
        artifact_index = {
            "episode_id": "ep01",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "status": "identity_qa_failed",
                    "media_generated": True,
                    "frame_qc_passed": True,
                    "identity_qa_passed": False,
                    "identity_consistency_passed": False,
                    "production_accepted": False,
                    "recommended_action": "route_to_character_director_and_workflow_td"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Find the identity failure route
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        assert identity_route is not None
        assert isinstance(identity_route["responsible_role"], list)
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]
        assert identity_route["recommended_action"] == "approve_identity_workflow_before_retry"
        assert identity_route["downstream_blocked"] == True

    def test_production_accepted_false_blocks_downstream(self, tmp_path):
        """Test that production_accepted=false blocks downstream."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index.json with production_accepted=false
        artifact_index = {
            "episode_id": "ep01",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "status": "identity_qa_failed",
                    "media_generated": True,
                    "frame_qc_passed": True,
                    "identity_qa_passed": False,
                    "identity_consistency_passed": False,
                    "production_accepted": False,
                    "recommended_action": "route_to_character_director_and_workflow_td"
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        assert result["downstream_blocked"] == True
        assert result["status"] == "blocked"

    def test_identity_consistency_passed_false_blocks_downstream(self, tmp_path):
        """Test that identity_consistency_passed=false blocks downstream."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index.json with identity_consistency_passed=false
        artifact_index = {
            "episode_id": "ep01",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "status": "frames_generated",
                    "media_generated": True,
                    "frame_qc_passed": True,
                    "identity_qa_passed": False,
                    "identity_consistency_passed": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        assert result["downstream_blocked"] == True
        assert result["status"] == "blocked"

    def test_frame_qc_passed_true_not_enough_for_production_acceptance(self, tmp_path):
        """Test that frame_qc_passed=true is not enough for production acceptance."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index.json with frame_qc_passed=true but identity failure
        artifact_index = {
            "episode_id": "ep01",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "status": "identity_qa_failed",
                    "media_generated": True,
                    "frame_qc_passed": True,  # Frame QC passed
                    "identity_qa_passed": False,  # But identity failed
                    "identity_consistency_passed": False,
                    "production_accepted": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Should still be blocked due to identity failure
        assert result["downstream_blocked"] == True
        # Should route to Character Director + Workflow TD, not just continue
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        assert identity_route is not None
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]

    def test_route_production_tasks_works_on_multishot_style_state(self, tmp_path):
        """Test that route-production-tasks works on rc2_multishot1_ep01 style state."""
        cards_dir = tmp_path / "cards"
        cards_dir.mkdir()
        
        # Create output/control directory structure
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create artifact_index.json similar to rc2_multishot1_ep01
        artifact_index = {
            "episode_id": "ep01",
            "episode_title": "Test Episode",
            "overall_episode_state": "preflight_complete",
            "shots": [
                {
                    "shot_id": "shot01",
                    "status": "identity_qa_failed",
                    "media_generated": True,
                    "frame_qc_passed": True,
                    "identity_qa_passed": False,
                    "identity_consistency_passed": False,
                    "production_accepted": False,
                    "generation_mode": "reference_locked",
                    "technical_fallback_only": True,
                    "recommended_action": "route_to_character_director_and_workflow_td"
                },
                {
                    "shot_id": "shot02",
                    "status": "preflight_complete",
                    "media_generated": False
                }
            ]
        }
        
        with open(control_dir / "artifact_index.json", "w") as f:
            json.dump(artifact_index, f)
        
        router = ProductionRouter()
        result = router.route_project_cards(str(tmp_path))
        
        # Should detect identity failure and route correctly
        assert result["status"] == "blocked"
        assert result["downstream_blocked"] == True
        
        identity_route = None
        for route in result["routes"]:
            if route["issue_type"] == "identity_qa_failed":
                identity_route = route
                break
        
        assert identity_route is not None
        assert isinstance(identity_route["responsible_role"], list)
        assert "Character Director" in identity_route["responsible_role"]
        assert "Workflow TD / ComfyUI Technical Director" in identity_route["responsible_role"]

    def test_no_project_specific_hardcode_added_to_router_core(self, tmp_path):
        """Test that no project-specific hardcode is added to router core logic."""
        # Read the router source code to check for hardcode
        router_path = Path(__file__).parent.parent / "app" / "production_cards" / "router.py"
        with open(router_path, "r") as f:
            router_content = f.read().lower()
        
        # Check for project-specific names
        assert "alya" not in router_content
        assert "mir erdan" not in router_content
        assert "ep01" not in router_content  # No hardcode for specific episode
        assert "shot01" not in router_content  # No hardcode for specific shot
