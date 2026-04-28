"""
Production Card Router

This module provides routing logic for production cards.
It determines which role owns the next missing, blocked, incomplete, or failed production action.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from .validator import CardValidator
from .schema_loader import list_valid_statuses


class ProductionRouter:
    """Routes production card issues to responsible roles."""

    def __init__(self, schemas_dir: Optional[str] = None):
        """
        Initialize the production router.

        Args:
            schemas_dir: Path to the schemas directory. If None, uses default.
        """
        self.validator = CardValidator(schemas_dir)
        self.valid_statuses = list_valid_statuses()

    def route_project_cards(self, project_root: str) -> Dict[str, Any]:
        """
        Route all cards in a project to determine next actions.

        Args:
            project_root: Path to the project root

        Returns:
            Routing result dict with status, routes, next_actions
        """
        project_path = Path(project_root)
        result = {
            "status": "routed",
            "project_root": project_root,
            "generation_ready": False,
            "downstream_blocked": False,
            "summary": {
                "cards_found": 0,
                "issues_found": 0,
                "blocked_count": 0,
                "roles_needed": []
            },
            "routes": [],
            "next_actions": []
        }

        # Validate cards first
        validation_result = self.validator.validate_project_cards(project_root)
        result["generation_ready"] = validation_result.get("generation_ready", False)

        cards = validation_result.get("cards", [])
        result["summary"]["cards_found"] = len(cards)

        # Check for identity QA failure in project metadata
        identity_qa_failed = self._check_identity_qa_failed(project_path)

        # Build routes for each card issue
        routes = []
        blocked_count = 0
        roles_needed_set = set()

        # Special handling for identity QA failure
        if identity_qa_failed:
            route = {
                "issue_type": "identity_qa_failed",
                "card_id": "project_metadata",
                "card_type": "ProjectCard",
                "current_status": "identity_qa_failed",
                "responsible_role": ["Character Director", "Workflow TD / ComfyUI Technical Director"],
                "recommended_action": "approve_identity_workflow_before_retry",
                "downstream_blocked": True
            }
            routes.append(route)
            blocked_count += 1
            roles_needed_set.add("Character Director")
            roles_needed_set.add("Workflow TD / ComfyUI Technical Director")
            result["downstream_blocked"] = True

        # Process each card
        for card in cards:
            card_id = card.get("card_id", "unknown")
            card_type = card.get("card_type", "unknown")
            status = card.get("status", "unknown")
            owner_role = card.get("owner_role", "unknown")
            validation_status = card.get("validation_status", "failed")
            errors = card.get("errors", [])

            # Skip if card validation passed and status is approved
            if validation_status == "passed" and status == "approved":
                continue

            # Determine issue type and responsible role
            issue_type, responsible_role, recommended_action = self._determine_card_issue(
                card, validation_result
            )

            if issue_type:
                route = {
                    "issue_type": issue_type,
                    "card_id": card_id,
                    "card_type": card_type,
                    "current_status": status,
                    "responsible_role": responsible_role,
                    "recommended_action": recommended_action,
                    "downstream_blocked": self._is_blocking_status(status)
                }
                routes.append(route)
                blocked_count += 1
                if isinstance(responsible_role, list):
                    for role in responsible_role:
                        roles_needed_set.add(role)
                else:
                    roles_needed_set.add(responsible_role)

        # Determine if downstream is blocked
        result["downstream_blocked"] = result["downstream_blocked"] or blocked_count > 0

        # Update summary
        result["summary"]["issues_found"] = len(routes)
        result["summary"]["blocked_count"] = blocked_count
        result["summary"]["roles_needed"] = sorted(list(roles_needed_set))

        # Build routes
        result["routes"] = routes

        # Build next actions
        result["next_actions"] = self._build_next_actions(routes)

        # Determine overall status
        if result["downstream_blocked"]:
            result["status"] = "blocked"
        elif result["generation_ready"]:
            result["status"] = "ready"
        else:
            result["status"] = "routed"

        return result

    def _check_identity_qa_failed(self, project_path: Path) -> bool:
        """
        Check if identity QA failed in project metadata or artifact index.

        Args:
            project_path: Path to the project root

        Returns:
            True if identity QA failed, False otherwise
        """
        # Check for identity_qa_failed in project metadata files
        metadata_files = [
            project_path / "project_metadata.json",
            project_path / "data" / "project_metadata.json",
            project_path / "output" / "project_metadata.json"
        ]

        for metadata_file in metadata_files:
            if metadata_file.exists():
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    # Check for identity_qa_failed or production_accepted=false due to identity
                    if metadata.get("identity_qa_failed") == True:
                        return True
                    if metadata.get("production_accepted") == False and "identity" in metadata.get("rejection_reason", "").lower():
                        return True
                except (json.JSONDecodeError, IOError):
                    pass

        # Check artifact_index.json for identity failures in shots
        artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
        if artifact_index_path.exists():
            try:
                with open(artifact_index_path, 'r', encoding='utf-8') as f:
                    artifact_index = json.load(f)
                
                # Check if any shot has identity failure
                shots = artifact_index.get("shots", [])
                for shot in shots:
                    # Check for identity failure indicators
                    if shot.get("identity_consistency_passed") == False:
                        return True
                    if shot.get("identity_qa_passed") == False:
                        return True
                    if shot.get("status") == "identity_qa_failed":
                        return True
                    if shot.get("production_accepted") == False and "identity" in shot.get("recommended_action", "").lower():
                        return True
            except (json.JSONDecodeError, IOError):
                pass

        return False

    def _determine_card_issue(self, card: Dict[str, Any], validation_result: Dict[str, Any]) -> tuple:
        """
        Determine the issue type and responsible role for a card.

        Args:
            card: Card data
            validation_result: Full validation result

        Returns:
            Tuple of (issue_type, responsible_role, recommended_action)
        """
        card_type = card.get("card_type", "unknown")
        status = card.get("status", "unknown")
        validation_status = card.get("validation_status", "failed")
        errors = card.get("errors", [])

        # Check validation status first
        if validation_status != "passed":
            if "project-specific hardcode" in " ".join(errors):
                return "invalid_card", card.get("owner_role", "unknown"), "fix_validation_errors"
            return "invalid_card", card.get("owner_role", "unknown"), "fix_validation_errors"

        # Check status-based issues
        if status == "draft":
            return self._route_draft_card(card_type)
        elif status == "blocked":
            return self._route_blocked_card(card_type)
        elif status == "needs_references":
            return self._route_needs_references(card_type)
        elif status == "needs_role_work":
            return self._route_needs_role_work(card_type)

        return None, None, None

    def _route_draft_card(self, card_type: str) -> tuple:
        """
        Route a draft card to its responsible role.

        Args:
            card_type: The card type

        Returns:
            Tuple of (issue_type, responsible_role, recommended_action)
        """
        routing_map = {
            "CharacterCard": ("draft_card", "Character Director", "complete_and_approve_card"),
            "EnvironmentCard": ("draft_card", "Environment / Art Director", "complete_and_approve_card"),
            "LightingCard": ("draft_card", "Cinematographer / Camera + Lighting Director", "complete_and_approve_card"),
            "CameraCard": ("draft_card", "Cinematographer / Camera + Lighting Director", "complete_and_approve_card"),
            "ScenarioCard": ("draft_card", "Screenwriter / Script Agent", "complete_and_approve_card"),
            "ShotCard": ("draft_card", "Shot Designer / Storyboard Agent", "complete_and_approve_card"),
            "WorkflowRecipeCard": ("draft_card", "Workflow TD / ComfyUI Technical Director", "complete_and_approve_card"),
            "QARequirementCard": ("draft_card", "Editor / Final QA Supervisor", "complete_and_approve_card"),
            "VoiceCard": ("draft_card", "Audio / Voice Agent", "complete_and_approve_card"),
            "StyleCard": ("draft_card", "Director / Orchestrator", "complete_and_approve_card"),
            "WardrobeCard": ("draft_card", "Wardrobe/Character Director", "complete_and_approve_card"),
            "PropCard": ("draft_card", "Prop Master / Environment Director", "complete_and_approve_card"),
            "ProjectCard": ("draft_card", "Executive Producer / Product Owner", "complete_and_approve_card"),
            "EpisodeCard": ("draft_card", "Director / Orchestrator", "complete_and_approve_card"),
            "ReleasePackageCard": ("draft_card", "Executive Producer / Product Owner", "complete_and_approve_card"),
        }

        return routing_map.get(card_type, ("draft_card", "unknown", "complete_and_approve_card"))

    def _route_blocked_card(self, card_type: str) -> tuple:
        """
        Route a blocked card to its responsible role.

        Args:
            card_type: The card type

        Returns:
            Tuple of (issue_type, responsible_role, recommended_action)
        """
        routing_map = {
            "CharacterCard": ("blocked_card", "Character Director", "resolve_blocking_issues"),
            "EnvironmentCard": ("blocked_card", "Environment / Art Director", "resolve_blocking_issues"),
            "LightingCard": ("blocked_card", "Cinematographer / Camera + Lighting Director", "resolve_blocking_issues"),
            "CameraCard": ("blocked_card", "Cinematographer / Camera + Lighting Director", "resolve_blocking_issues"),
            "ScenarioCard": ("blocked_card", "Screenwriter / Script Agent", "resolve_blocking_issues"),
            "ShotCard": ("blocked_card", "Shot Designer / Storyboard Agent", "resolve_blocking_issues"),
            "WorkflowRecipeCard": ("blocked_card", "Workflow TD / ComfyUI Technical Director", "resolve_blocking_issues"),
            "QARequirementCard": ("blocked_card", "Editor / Final QA Supervisor", "resolve_blocking_issues"),
            "VoiceCard": ("blocked_card", "Audio / Voice Agent", "resolve_blocking_issues"),
            "StyleCard": ("blocked_card", "Director / Orchestrator", "resolve_blocking_issues"),
            "WardrobeCard": ("blocked_card", "Wardrobe/Character Director", "resolve_blocking_issues"),
            "PropCard": ("blocked_card", "Prop Master / Environment Director", "resolve_blocking_issues"),
            "ProjectCard": ("blocked_card", "Executive Producer / Product Owner", "resolve_blocking_issues"),
            "EpisodeCard": ("blocked_card", "Director / Orchestrator", "resolve_blocking_issues"),
            "ReleasePackageCard": ("blocked_card", "Executive Producer / Product Owner", "resolve_blocking_issues"),
        }

        return routing_map.get(card_type, ("blocked_card", "unknown", "resolve_blocking_issues"))

    def _route_needs_references(self, card_type: str) -> tuple:
        """
        Route a card that needs references to its responsible role.

        Args:
            card_type: The card type

        Returns:
            Tuple of (issue_type, responsible_role, recommended_action)
        """
        routing_map = {
            "CharacterCard": ("missing_reference", "Character Director", "add_required_references"),
            "EnvironmentCard": ("missing_reference", "Environment / Art Director", "add_required_references"),
            "StyleCard": ("missing_reference", "Director / Orchestrator", "add_required_references"),
            "WardrobeCard": ("missing_reference", "Wardrobe/Character Director", "add_required_references"),
            "PropCard": ("missing_reference", "Prop Master / Environment Director", "add_required_references"),
        }

        return routing_map.get(card_type, ("missing_reference", "unknown", "add_required_references"))

    def _route_needs_role_work(self, card_type: str) -> tuple:
        """
        Route a card that needs role work to its responsible role.

        Args:
            card_type: The card type

        Returns:
            Tuple of (issue_type, responsible_role, recommended_action)
        """
        routing_map = {
            "CharacterCard": ("needs_role_work", "Character Director", "complete_role_work"),
            "EnvironmentCard": ("needs_role_work", "Environment / Art Director", "complete_role_work"),
            "LightingCard": ("needs_role_work", "Cinematographer / Camera + Lighting Director", "complete_role_work"),
            "CameraCard": ("needs_role_work", "Cinematographer / Camera + Lighting Director", "complete_role_work"),
            "ScenarioCard": ("needs_role_work", "Screenwriter / Script Agent", "complete_role_work"),
            "ShotCard": ("needs_role_work", "Shot Designer / Storyboard Agent", "complete_role_work"),
            "WorkflowRecipeCard": ("needs_role_work", "Workflow TD / ComfyUI Technical Director", "complete_role_work"),
            "QARequirementCard": ("needs_role_work", "Editor / Final QA Supervisor", "complete_role_work"),
            "VoiceCard": ("needs_role_work", "Audio / Voice Agent", "complete_role_work"),
            "StyleCard": ("needs_role_work", "Director / Orchestrator", "complete_role_work"),
            "WardrobeCard": ("needs_role_work", "Wardrobe/Character Director", "complete_role_work"),
            "PropCard": ("needs_role_work", "Prop Master / Environment Director", "complete_role_work"),
            "ProjectCard": ("needs_role_work", "Executive Producer / Product Owner", "complete_role_work"),
            "EpisodeCard": ("needs_role_work", "Director / Orchestrator", "complete_role_work"),
            "ReleasePackageCard": ("needs_role_work", "Executive Producer / Product Owner", "complete_role_work"),
        }

        return routing_map.get(card_type, ("needs_role_work", "unknown", "complete_role_work"))

    def _is_blocking_status(self, status: str) -> bool:
        """
        Determine if a status blocks downstream work.

        Args:
            status: The card status

        Returns:
            True if blocking, False otherwise
        """
        blocking_statuses = ["draft", "blocked", "needs_references", "needs_role_work"]
        return status in blocking_statuses

    def _build_next_actions(self, routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Build prioritized next actions from routes.

        Args:
            routes: List of route entries

        Returns:
            List of next action entries with priority
        """
        next_actions = []
        priority = 1

        # Group by role to avoid duplicate actions for same role
        role_actions = {}

        for route in routes:
            responsible_role = route["responsible_role"]
            recommended_action = route["recommended_action"]
            card_id = route["card_id"]
            issue_type = route["issue_type"]

            # Handle list of roles (for identity QA failure)
            if isinstance(responsible_role, list):
                for role in responsible_role:
                    key = f"{role}:{recommended_action}"
                    if key not in role_actions:
                        role_actions[key] = {
                            "role": role,
                            "action": recommended_action,
                            "card_ids": [card_id],
                            "issue_types": [issue_type]
                        }
                    else:
                        if card_id not in role_actions[key]["card_ids"]:
                            role_actions[key]["card_ids"].append(card_id)
                        if issue_type not in role_actions[key]["issue_types"]:
                            role_actions[key]["issue_types"].append(issue_type)
            else:
                key = f"{responsible_role}:{recommended_action}"
                if key not in role_actions:
                    role_actions[key] = {
                        "role": responsible_role,
                        "action": recommended_action,
                        "card_ids": [card_id],
                        "issue_types": [issue_type]
                    }
                else:
                    if card_id not in role_actions[key]["card_ids"]:
                        role_actions[key]["card_ids"].append(card_id)
                    if issue_type not in role_actions[key]["issue_types"]:
                        role_actions[key]["issue_types"].append(issue_type)

        # Build next actions with priority
        for key, action_data in role_actions.items():
            next_actions.append({
                "priority": priority,
                "role": action_data["role"],
                "task": action_data["action"],
                "reason": f"Address {', '.join(action_data['issue_types'])} for cards: {', '.join(action_data['card_ids'])}"
            })
            priority += 1

        return next_actions


def route_production_cards(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Route production cards to determine next actions.

    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output

    Returns:
        Routing result dict
    """
    router = ProductionRouter()
    result = router.route_project_cards(project_root)
    
    if json_output:
        return result
    
    return result
