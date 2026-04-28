"""
Production Card Materializer

This module provides functionality to materialize production cards from existing project state.
It reads artifact_index.json and episode_plan.json to create role-owned cards.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime


class ProductionCardMaterializer:
    """Materializes production cards from project state."""

    def __init__(self):
        """Initialize the materializer."""
        self.card_types = [
            "ProjectCard",
            "EpisodeCard",
            "ScenarioCard",
            "ShotCard",
            "CharacterCard",
            "WorkflowRecipeCard",
            "QARequirementCard"
        ]

    def materialize_project_cards(self, project_root: str, json_output: bool = False) -> Dict[str, Any]:
        """
        Materialize production cards for a project from its current state.

        Args:
            project_root: Path to the project root
            json_output: Whether to return JSON-compatible output

        Returns:
            Materialization result dict
        """
        project_path = Path(project_root)
        result = {
            "status": "completed",
            "project_root": str(project_root),
            "cards_created": 0,
            "cards_updated": 0,
            "blocked_cards": 0,
            "routes_preserved": True,
            "downstream_blocked": True,
            "cards": []
        }

        # Read project state
        artifact_index = self._read_artifact_index(project_path)
        episode_plan = self._read_episode_plan(project_path)

        if not artifact_index:
            result["status"] = "failed"
            result["error"] = "artifact_index.json not found"
            return result

        # Create card folder structure
        cards_dir = project_path / "cards"
        self._create_card_folders(cards_dir)

        # Materialize cards
        cards_created = 0
        cards_updated = 0
        blocked_count = 0

        # ProjectCard
        project_card = self._materialize_project_card(project_path, artifact_index, episode_plan)
        project_card_path = cards_dir / "project" / "project_card.json"
        if self._write_card(project_card_path, project_card):
            cards_created += 1
            result["cards"].append(project_card_path.name)
            if project_card.get("status") in ["blocked", "needs_role_work"]:
                blocked_count += 1

        # EpisodeCard
        episode_card = self._materialize_episode_card(artifact_index, episode_plan)
        episode_card_path = cards_dir / "episodes" / "episode_card.json"
        if self._write_card(episode_card_path, episode_card):
            cards_created += 1
            result["cards"].append(episode_card_path.name)

        # ScenarioCards
        scenario_cards = self._materialize_scenario_cards(episode_plan)
        scenario_dir = cards_dir / "scenarios"
        for i, scenario_card in enumerate(scenario_cards):
            scenario_card_path = scenario_dir / f"scenario_{i+1}.json"
            if self._write_card(scenario_card_path, scenario_card):
                cards_created += 1
                result["cards"].append(scenario_card_path.name)

        # CharacterCard
        character_card = self._materialize_character_card(artifact_index)
        character_card_path = cards_dir / "characters" / "character_card.json"
        if self._write_card(character_card_path, character_card):
            cards_created += 1
            result["cards"].append(character_card_path.name)
            if character_card.get("status") in ["blocked", "needs_role_work"]:
                blocked_count += 1

        # ShotCards
        shot_cards = self._materialize_shot_cards(artifact_index, episode_plan)
        shot_dir = cards_dir / "shots"
        for shot_card in shot_cards:
            shot_card_path = shot_dir / f"{shot_card['card_id']}.json"
            if self._write_card(shot_card_path, shot_card):
                cards_created += 1
                result["cards"].append(shot_card_path.name)
                if shot_card.get("status") in ["blocked", "needs_role_work"]:
                    blocked_count += 1

        # WorkflowRecipeCard
        workflow_card = self._materialize_workflow_card(artifact_index)
        workflow_card_path = cards_dir / "workflows" / "workflow_card.json"
        if self._write_card(workflow_card_path, workflow_card):
            cards_created += 1
            result["cards"].append(workflow_card_path.name)
            if workflow_card.get("status") in ["blocked", "needs_role_work"]:
                blocked_count += 1

        # QARequirementCard
        qa_card = self._materialize_qa_card()
        qa_card_path = cards_dir / "qa" / "qa_card.json"
        if self._write_card(qa_card_path, qa_card):
            cards_created += 1
            result["cards"].append(qa_card_path.name)

        result["cards_created"] = cards_created
        result["cards_updated"] = cards_updated
        result["blocked_cards"] = blocked_count

        # Check if downstream is blocked
        result["downstream_blocked"] = blocked_count > 0

        return result

    def _read_artifact_index(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Read artifact_index.json from project."""
        artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
        if artifact_index_path.exists():
            try:
                with open(artifact_index_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _read_episode_plan(self, project_path: Path) -> Optional[Dict[str, Any]]:
        """Read episode_plan.json from project."""
        episode_plan_path = project_path / "output" / "control" / "episode_plan.json"
        if episode_plan_path.exists():
            try:
                with open(episode_plan_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _create_card_folders(self, cards_dir: Path):
        """Create card folder structure."""
        folders = [
            "project",
            "episodes",
            "scenarios",
            "shots",
            "characters",
            "environments",
            "lighting",
            "camera",
            "workflows",
            "qa"
        ]
        for folder in folders:
            (cards_dir / folder).mkdir(parents=True, exist_ok=True)

    def _write_card(self, card_path: Path, card_data: Dict[str, Any]) -> bool:
        """Write card data to file."""
        try:
            card_path.parent.mkdir(parents=True, exist_ok=True)
            with open(card_path, 'w', encoding='utf-8') as f:
                json.dump(card_data, f, indent=2)
            return True
        except (IOError, OSError):
            return False

    def _materialize_project_card(self, project_path: Path, artifact_index: Dict[str, Any], episode_plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Materialize ProjectCard from project state."""
        episode_title = episode_plan.get("episode_title", "Unknown Episode") if episode_plan else "Unknown Episode"
        
        return {
            "card_id": "project_card",
            "card_type": "ProjectCard",
            "project_id": "rc2_multishot1_ep01",
            "owner_role": "Executive Producer / Product Owner",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "title": episode_title,
                "description": f"Multi-shot production project for {episode_title}"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Executive Producer / Product Owner",
            "next_action_if_missing": "Create ProjectCard",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "title": episode_title,
            "description": f"Multi-shot production project for {episode_title}",
            "executive_producer": "Executive Producer",
            "target_deliverables": ["final_video"],
            "timeline": {}
        }

    def _materialize_episode_card(self, artifact_index: Dict[str, Any], episode_plan: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Materialize EpisodeCard from project state."""
        episode_id = artifact_index.get("episode_id", "ep01")
        episode_title = artifact_index.get("episode_title", "Unknown Episode")
        shots = artifact_index.get("shots", [])
        
        shot_ids = [shot.get("shot_id") for shot in shots]
        
        return {
            "card_id": f"{episode_id}_card",
            "card_type": "EpisodeCard",
            "project_id": "rc2_multishot1_ep01",
            "owner_role": "Director / Orchestrator",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "episode_id": episode_id,
                "title": episode_title
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Director / Orchestrator",
            "next_action_if_missing": "Create EpisodeCard",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "episode_id": episode_id,
            "title": episode_title,
            "director": "Director",
            "shot_ids": shot_ids,
            "total_shots": len(shots)
        }

    def _materialize_scenario_cards(self, episode_plan: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Materialize ScenarioCards from episode plan."""
        if not episode_plan:
            return []
        
        shots = episode_plan.get("shots", [])
        scenario_cards = []
        
        for shot in shots:
            scenario_card = {
                "card_id": f"{shot['shot_id']}_scenario",
                "card_type": "ScenarioCard",
                "project_id": "rc2_multishot1_ep01",
                "owner_role": "Screenwriter / Script Agent",
                "status": "draft",
                "version": "1.0.0",
                "required_inputs": {
                    "title": shot.get("scene_goal", ""),
                    "narrative_beat": shot.get("voiceover_text", "")
                },
                "references": [],
                "constraints": {},
                "allowed_variations": [],
                "forbidden_drift": [],
                "dependencies": [],
                "approval_required_by": "Screenwriter / Script Agent",
                "next_action_if_missing": "Create ScenarioCard",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "title": shot.get("scene_goal", ""),
                "screenwriter": "Screenwriter",
                "narrative_beat": shot.get("voiceover_text", ""),
                "location_description": shot.get("visual_description", ""),
                "involved_characters": [shot.get("reference_character", "")],
                "shot_references": [shot.get("shot_id", "")],
                "environment_reference": "env_001"
            }
            scenario_cards.append(scenario_card)
        
        return scenario_cards

    def _materialize_character_card(self, artifact_index: Dict[str, Any]) -> Dict[str, Any]:
        """Materialize CharacterCard from project state."""
        # Extract character name from episode title or shots
        episode_title = artifact_index.get("episode_title", "")
        shots = artifact_index.get("shots", [])
        
        # Find the reference character from shots
        character_name = "Unknown"
        for shot in shots:
            ref_char = shot.get("reference_character")
            if ref_char:
                character_name = ref_char
                break
        
        # Check if any shot has identity failure
        has_identity_failure = False
        for shot in shots:
            if shot.get("identity_consistency_passed") == False or shot.get("identity_qa_passed") == False:
                has_identity_failure = True
                break
        
        status = "needs_role_work" if has_identity_failure else "draft"
        
        return {
            "card_id": f"{character_name.lower()}_character",
            "card_type": "CharacterCard",
            "project_id": "rc2_multishot1_ep01",
            "owner_role": "Character Director",
            "status": status,
            "version": "1.0.0",
            "required_inputs": {
                "name": character_name,
                "visual_reference_paths": [],
                "physical_description": "Character description",
                "identity_mode": "gorynych_identity"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Character Director",
            "next_action_if_missing": "Create CharacterCard",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "name": character_name,
            "character_director": "Character Director",
            "visual_reference_paths": [],
            "physical_description": "Character description",
            "personality_traits": [],
            "voice_profile": None,
            "wardrobe_references": [],
            "identity_mode": "gorynych_identity",
            "identity_consistency_requirements": {},
            "identity_reference_required": True,
            "identity_workflow_approval_required": True
        }

    def _materialize_shot_cards(self, artifact_index: Dict[str, Any], episode_plan: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Materialize ShotCards from project state."""
        shots = artifact_index.get("shots", [])
        shot_cards = []
        
        for shot in shots:
            shot_id = shot.get("shot_id", "")
            shot_plan = None
            if episode_plan:
                for plan_shot in episode_plan.get("shots", []):
                    if plan_shot.get("shot_id") == shot_id:
                        shot_plan = plan_shot
                        break
            
            # Determine status based on shot state
            status = "draft"
            frame_qc_passed = shot.get("frame_qc_passed", False)
            identity_consistency_passed = shot.get("identity_consistency_passed", True)
            production_accepted = shot.get("production_accepted", True)
            blocking_reason = None
            next_action = "complete_and_approve_card"
            responsible_roles = ["Shot Designer / Storyboard Agent"]
            
            # If identity failure, set blocked status
            if identity_consistency_passed == False or shot.get("status") == "identity_qa_failed":
                status = "blocked"
                blocking_reason = "identity_qa_failed"
                next_action = "approve_identity_workflow_before_retry"
                responsible_roles = ["Character Director", "Workflow TD / ComfyUI Technical Director"]
            
            shot_card = {
                "card_id": shot_id,
                "card_type": "ShotCard",
                "project_id": "rc2_multishot1_ep01",
                "owner_role": "Shot Designer / Storyboard Agent",
                "status": status,
                "version": "1.0.0",
                "required_inputs": {
                    "shot_type": "medium",
                    "action_description": shot_plan.get("scene_goal", "") if shot_plan else ""
                },
                "references": [],
                "constraints": {},
                "allowed_variations": [],
                "forbidden_drift": [],
                "dependencies": [],
                "approval_required_by": "Shot Designer / Storyboard Agent",
                "next_action_if_missing": "Create ShotCard",
                "created_at": datetime.utcnow().isoformat() + "Z",
                "updated_at": datetime.utcnow().isoformat() + "Z",
                "shot_type": "medium",
                "action_description": shot_plan.get("scene_goal", "") if shot_plan else "",
                "duration_seconds": shot_plan.get("expected_duration_seconds", 0) if shot_plan else 0,
                "character_reference": shot.get("reference_character", ""),
                "environment_reference": "env_001",
                "camera_reference": "camera_001",
                "lighting_reference": "lighting_001",
                "style_reference": "style_001",
                "frame_qc_passed": frame_qc_passed,
                "identity_consistency_passed": identity_consistency_passed,
                "production_accepted": production_accepted,
                "blocking_reason": blocking_reason,
                "next_action": next_action,
                "responsible_roles": responsible_roles
            }
            shot_cards.append(shot_card)
        
        return shot_cards

    def _materialize_workflow_card(self, artifact_index: Dict[str, Any]) -> Dict[str, Any]:
        """Materialize WorkflowRecipeCard from project state."""
        # Check if any shot has identity failure
        has_identity_failure = False
        generation_mode = "gorynych_identity"
        
        shots = artifact_index.get("shots", [])
        for shot in shots:
            if shot.get("identity_consistency_passed") == False or shot.get("identity_qa_passed") == False:
                has_identity_failure = True
                break
        
        status = "needs_role_work" if has_identity_failure else "draft"
        
        return {
            "card_id": "identity_workflow",
            "card_type": "WorkflowRecipeCard",
            "project_id": "rc2_multishot1_ep01",
            "owner_role": "Workflow TD / ComfyUI Technical Director",
            "status": status,
            "version": "1.0.0",
            "required_inputs": {
                "name": "Gorynych Identity Workflow",
                "workflow_graph": {}
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Workflow TD / ComfyUI Technical Director",
            "next_action_if_missing": "Create WorkflowRecipeCard",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "name": "Gorynych Identity Workflow",
            "workflow_td": "Workflow TD / ComfyUI Technical Director",
            "workflow_graph": {},
            "node_parameters": {},
            "input_mappings": {},
            "output_mappings": {},
            "resource_requirements": {},
            "estimated_generation_time": 0,
            "generation_mode": generation_mode,
            "legacy_reference_locked_allowed_for_production": False
        }

    def _materialize_qa_card(self) -> Dict[str, Any]:
        """Materialize QARequirementCard."""
        return {
            "card_id": "identity_qa_requirements",
            "card_type": "QARequirementCard",
            "project_id": "rc2_multishot1_ep01",
            "owner_role": "Editor / Final QA Supervisor",
            "status": "draft",
            "version": "1.0.0",
            "required_inputs": {
                "qa_type": "identity_consistency",
                "acceptance_criteria": "Identity consistency across frames"
            },
            "references": [],
            "constraints": {},
            "allowed_variations": [],
            "forbidden_drift": [],
            "dependencies": [],
            "approval_required_by": "Editor / Final QA Supervisor",
            "next_action_if_missing": "Create QARequirementCard",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "qa_type": "identity_consistency",
            "acceptance_criteria": "Identity consistency across frames",
            "frame_qc_required": True,
            "identity_consistency_required": True,
            "production_acceptance_requires_identity_qa": True,
            "downstream_blocked_if_identity_failed": True
        }


def materialize_production_cards(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Materialize production cards for a project.

    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output

    Returns:
        Materialization result dict
    """
    materializer = ProductionCardMaterializer()
    result = materializer.materialize_project_cards(project_root, json_output)
    
    if json_output:
        return result
    
    return result
