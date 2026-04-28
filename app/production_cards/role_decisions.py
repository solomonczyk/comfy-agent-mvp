"""
Production Role Decisions Module

Creates and validates role decision templates for Character Director and Workflow TD
when identity QA fails and production is blocked.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_work_orders(project_root: str) -> Dict[str, Any]:
    """Load existing work orders to extract project data."""
    work_orders_dir = Path(project_root) / "output" / "control" / "work_orders"
    
    character_director_order = {}
    workflow_td_order = {}
    
    char_order_path = work_orders_dir / "character_director_identity_review.json"
    if char_order_path.exists():
        with open(char_order_path, 'r') as f:
            character_director_order = json.load(f)
    
    workflow_order_path = work_orders_dir / "workflow_td_identity_workflow_review.json"
    if workflow_order_path.exists():
        with open(workflow_order_path, 'r') as f:
            workflow_td_order = json.load(f)
    
    return {
        "character_director_work_order": character_director_order,
        "workflow_td_work_order": workflow_td_order
    }


def load_character_card(project_root: str) -> Dict[str, Any]:
    """Load character card to preserve real project data."""
    character_card_path = Path(project_root) / "cards" / "characters" / "character_card.json"
    
    if character_card_path.exists():
        with open(character_card_path, 'r') as f:
            return json.load(f)
    
    return {}


def load_workflow_card(project_root: str) -> Dict[str, Any]:
    """Load workflow card to preserve real project data."""
    workflow_card_path = Path(project_root) / "cards" / "workflows" / "workflow_card.json"
    
    if workflow_card_path.exists():
        with open(workflow_card_path, 'r') as f:
            return json.load(f)
    
    return {}


def create_character_director_decision_template(
    project_root: str,
    character_card: Dict[str, Any],
    blocked_shot: str
) -> Dict[str, Any]:
    """Create Character Director decision template."""
    # Preserve real project data from character card
    character_name = character_card.get("name", "Unknown")
    display_name = character_card.get("display_name", "Unknown")
    reference_character = character_card.get("reference_character", "Unknown")
    
    decision_template = {
        "role": "Character Director",
        "work_order": "character_director_identity_review",
        "blocked_shot": blocked_shot,
        "character_name": character_name,
        "display_name": display_name,
        "reference_character": reference_character,
        "decision_status": "pending",
        "allowed_decisions": [
            "approve",
            "reject",
            "request_new_reference",
            "request_workflow_change"
        ],
        "selected_decision": None,
        "required_artifacts": [
            "approved_character_identity_rules",
            "approved_reference_strategy",
            "identity_acceptance_criteria"
        ],
        "downstream_blocked": True,
        "production_accepted": False,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    return decision_template


def create_workflow_td_decision_template(
    project_root: str,
    workflow_card: Dict[str, Any],
    blocked_shot: str
) -> Dict[str, Any]:
    """Create Workflow TD decision template."""
    # Preserve real project data from workflow card
    generation_mode = workflow_card.get("generation_mode", "gorynych_identity")
    legacy_reference_locked_allowed = workflow_card.get("legacy_reference_locked_allowed_for_production", False)
    
    decision_template = {
        "role": "Workflow TD / ComfyUI Technical Director",
        "work_order": "workflow_td_identity_workflow_review",
        "blocked_shot": blocked_shot,
        "decision_status": "pending",
        "current_required_generation_mode": generation_mode,
        "legacy_reference_locked_allowed_for_production": legacy_reference_locked_allowed,
        "allowed_decisions": [
            "approve_workflow",
            "reject_workflow",
            "request_missing_nodes",
            "request_missing_models",
            "request_reference_rebuild"
        ],
        "selected_decision": None,
        "required_artifacts": [
            "workflow_audit",
            "required_nodes",
            "required_models",
            "preflight_result",
            "output_collection_contract"
        ],
        "downstream_blocked": True,
        "production_accepted": False,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    return decision_template


def create_pending_role_decisions(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Create pending role decision templates for Character Director and Workflow TD.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with decision template creation results
    """
    project_path = Path(project_root)
    role_decisions_dir = project_path / "output" / "control" / "role_decisions"
    role_decisions_dir.mkdir(parents=True, exist_ok=True)
    
    # Load project data
    work_orders = load_work_orders(project_root)
    character_card = load_character_card(project_root)
    workflow_card = load_workflow_card(project_root)
    
    # Determine blocked shot from work orders or artifact index
    blocked_shot = "shot01"
    
    # Create decision templates
    character_director_decision = create_character_director_decision_template(
        project_root, character_card, blocked_shot
    )
    workflow_td_decision = create_workflow_td_decision_template(
        project_root, workflow_card, blocked_shot
    )
    
    # Save decision templates
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    
    with open(char_decision_path, 'w') as f:
        json.dump(character_director_decision, f, indent=2)
    
    with open(workflow_decision_path, 'w') as f:
        json.dump(workflow_td_decision, f, indent=2)
    
    # Update artifact index
    update_artifact_index(project_root, char_decision_path, workflow_decision_path)
    
    # Update episode ledger
    update_episode_ledger(project_root)
    
    result = {
        "status": "completed",
        "project_root": project_root,
        "downstream_blocked": True,
        "decision_templates_created": 2,
        "decision_templates": [
            {
                "role": character_director_decision["role"],
                "decision_path": str(char_decision_path),
                "decision_status": character_director_decision["decision_status"]
            },
            {
                "role": workflow_td_decision["role"],
                "decision_path": str(workflow_decision_path),
                "decision_status": workflow_td_decision["decision_status"]
            }
        ]
    }
    
    return result


def validate_role_decisions(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Validate role decision status and determine if downstream can proceed.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with validation results
    """
    project_path = Path(project_root)
    role_decisions_dir = project_path / "output" / "control" / "role_decisions"
    
    # Check if decision templates exist
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    
    pending_roles = []
    missing_approvals = []
    decision_ready = True
    
    # Check Character Director decision
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            char_decision = json.load(f)
        
        if char_decision.get("decision_status") == "pending":
            pending_roles.append("Character Director")
            missing_approvals.append("character_identity_approval")
            decision_ready = False
    else:
        pending_roles.append("Character Director")
        missing_approvals.append("character_identity_approval")
        decision_ready = False
    
    # Check Workflow TD decision
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_decision = json.load(f)
        
        if workflow_decision.get("decision_status") == "pending":
            pending_roles.append("Workflow TD / ComfyUI Technical Director")
            missing_approvals.append("workflow_fit_approval")
            decision_ready = False
    else:
        pending_roles.append("Workflow TD / ComfyUI Technical Director")
        missing_approvals.append("workflow_fit_approval")
        decision_ready = False
    
    # Determine overall status
    status = "blocked" if not decision_ready else "ready"
    downstream_blocked = not decision_ready
    
    result = {
        "status": status,
        "decision_ready": decision_ready,
        "downstream_blocked": downstream_blocked,
        "pending_roles": pending_roles,
        "missing_approvals": missing_approvals,
        "production_accepted": False if downstream_blocked else True
    }
    
    return result


def update_artifact_index(
    project_root: str,
    char_decision_path: Path,
    workflow_decision_path: Path
) -> None:
    """Update artifact_index.json with role decision information."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add role_decisions section
    artifact_index["role_decisions"] = {
        "character_director_decision": str(char_decision_path.relative_to(Path(project_root))),
        "workflow_td_decision": str(workflow_decision_path.relative_to(Path(project_root))),
        "decision_status": "pending",
        "downstream_blocked": True
    }
    
    # Ensure downstream_blocked is true
    artifact_index["downstream_blocked"] = True
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def update_episode_ledger(project_root: str) -> None:
    """Update episode_ledger.json with role decision template creation event."""
    ledger_path = Path(project_root) / "output" / "control" / "episode_ledger.json"
    
    if not ledger_path.exists():
        # Create ledger if it doesn't exist
        ledger = {
            "events": [],
            "episode_id": "ep01"
        }
    else:
        with open(ledger_path, 'r') as f:
            try:
                ledger = json.load(f)
                # Ensure events key exists
                if "events" not in ledger:
                    ledger["events"] = []
            except json.JSONDecodeError:
                # If file is corrupted, create new ledger
                ledger = {
                    "events": [],
                    "episode_id": "ep01"
                }
    
    # Add role decision template creation event
    event = {
        "event_type": "role_decision_templates_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roles": [
            "Character Director",
            "Workflow TD / ComfyUI Technical Director"
        ],
        "decision_status": "pending",
        "downstream_blocked": True,
        "comfyui_generation": False,
        "pipeline_action_rerun": False
    }
    
    ledger["events"].append(event)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)
