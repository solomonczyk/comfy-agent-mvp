"""
Production Work Orders Module

Converts production routing output into concrete role work orders for blocked issues.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_routes(project_root: str) -> Dict[str, Any]:
    """Load the production routing output."""
    router_output_path = Path(project_root) / "output" / "control" / "production_routing.json"
    if router_output_path.exists():
        with open(router_output_path, 'r') as f:
            return json.load(f)
    
    # If routing output doesn't exist, use router to generate it
    from app.production_cards.router import ProductionRouter
    router = ProductionRouter()
    return router.route_project_cards(project_root)


def load_relevant_cards(project_root: str) -> Dict[str, Any]:
    """Load relevant cards for work order generation."""
    cards_dir = Path(project_root) / "cards"
    cards = {}
    
    # Load shot cards
    shots_dir = cards_dir / "shots"
    if shots_dir.exists():
        for shot_file in shots_dir.glob("*.json"):
            with open(shot_file, 'r') as f:
                cards[shot_file.stem] = json.load(f)
    
    # Load character card
    character_file = cards_dir / "characters" / "character_card.json"
    if character_file.exists():
        with open(character_file, 'r') as f:
            cards["character_card"] = json.load(f)
    
    # Load workflow card
    workflow_file = cards_dir / "workflows" / "workflow_card.json"
    if workflow_file.exists():
        with open(workflow_file, 'r') as f:
            cards["workflow_card"] = json.load(f)
    
    return cards


def create_character_director_work_order(
    project_root: str,
    blocked_shot: Dict[str, Any],
    character_card: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a Character Director work order for identity review."""
    work_order = {
        "role": "Character Director",
        "work_order_type": "identity_review",
        "blocked_shot": blocked_shot.get("card_id"),
        "character_name": character_card.get("name", "Unknown"),
        "character_reference": character_card.get("reference_character", "Unknown"),
        "display_name": character_card.get("display_name", "Unknown"),
        "issue": blocked_shot.get("blocking_reason", "identity_qa_failed"),
        "frame_qc_passed": blocked_shot.get("frame_qc_passed", False),
        "identity_consistency_passed": blocked_shot.get("identity_consistency_passed", False),
        "production_accepted": blocked_shot.get("production_accepted", False),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "required_decision": {
            "options": [
                "approve",
                "reject",
                "request_new_reference",
                "request_workflow_change"
            ],
            "description": "Character Director must approve the character identity strategy or request changes"
        },
        "required_artifacts": {
            "approved_character_identity_rules": "Character identity consistency rules for the project",
            "approved_reference_strategy": "Strategy for character reference across shots",
            "identity_acceptance_criteria": "Criteria for accepting character identity as valid"
        },
        "handoff_to": "Workflow TD / ComfyUI Technical Director",
        "downstream_blocked": True,
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    return work_order


def create_workflow_td_work_order(
    project_root: str,
    blocked_shot: Dict[str, Any],
    workflow_card: Dict[str, Any]
) -> Dict[str, Any]:
    """Create a Workflow TD work order for identity workflow review."""
    work_order = {
        "role": "Workflow TD / ComfyUI Technical Director",
        "work_order_type": "identity_workflow_review",
        "blocked_shot": blocked_shot.get("card_id"),
        "issue": blocked_shot.get("blocking_reason", "identity_qa_failed"),
        "current_required_generation_mode": workflow_card.get("generation_mode", "gorynych_identity"),
        "legacy_reference_locked_allowed_for_production": workflow_card.get("legacy_reference_locked_allowed_for_production", False),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "required_decision": {
            "options": [
                "approve_workflow",
                "reject_workflow",
                "request_missing_nodes",
                "request_missing_models",
                "request_reference_rebuild"
            ],
            "description": "Workflow TD must approve the identity workflow or request necessary changes"
        },
        "required_artifacts": {
            "workflow_audit": "Audit of the current identity workflow configuration",
            "required_nodes": "List of required nodes for identity consistency",
            "required_models": "List of required models for character identity",
            "preflight_result": "Preflight validation result for the workflow",
            "output_collection_contract": "Contract for collecting workflow outputs"
        },
        "handoff_to": "Image Generation Agent (only after Character Director approval)",
        "downstream_blocked": True,
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    return work_order


def create_character_director_markdown(work_order: Dict[str, Any]) -> str:
    """Create a human-readable markdown summary for Character Director."""
    md = f"""# Character Director Work Order: Identity Review

## Role: {work_order['role']}

## Blocked Shot
- **Shot ID:** {work_order['blocked_shot']}
- **Issue:** {work_order['issue']}

## Character Information
- **Character Name:** {work_order['character_name']}
- **Display Name:** {work_order['display_name']}
- **Reference Character:** {work_order['character_reference']}

## Current Status
- **Frame QC Passed:** {work_order['frame_qc_passed']}
- **Identity Consistency Passed:** {work_order['identity_consistency_passed']}
- **Production Accepted:** {work_order['production_accepted']}

## Required Decision
You must choose one of the following:
{chr(10).join(f"- {option}" for option in work_order['required_decision']['options'])}

**Description:** {work_order['required_decision']['description']}

## Required Artifacts
- **approved_character_identity_rules:** {work_order['required_artifacts']['approved_character_identity_rules']}
- **approved_reference_strategy:** {work_order['required_artifacts']['approved_reference_strategy']}
- **identity_acceptance_criteria:** {work_order['required_artifacts']['identity_acceptance_criteria']}

## Handoff
After completion, hand off to: {work_order['handoff_to']}

## Downstream Status
**Blocked:** {work_order['downstream_blocked']}

## Created At
{work_order['created_at']}
"""
    return md


def create_workflow_td_markdown(work_order: Dict[str, Any]) -> str:
    """Create a human-readable markdown summary for Workflow TD."""
    md = f"""# Workflow TD Work Order: Identity Workflow Review

## Role: {work_order['role']}

## Blocked Shot
- **Shot ID:** {work_order['blocked_shot']}
- **Issue:** {work_order['issue']}

## Current Workflow Configuration
- **Required Generation Mode:** {work_order['current_required_generation_mode']}
- **Legacy Reference Locked Allowed:** {work_order['legacy_reference_locked_allowed_for_production']}

## Required Decision
You must choose one of the following:
{chr(10).join(f"- {option}" for option in work_order['required_decision']['options'])}

**Description:** {work_order['required_decision']['description']}

## Required Artifacts
- **workflow_audit:** {work_order['required_artifacts']['workflow_audit']}
- **required_nodes:** {work_order['required_artifacts']['required_nodes']}
- **required_models:** {work_order['required_artifacts']['required_models']}
- **preflight_result:** {work_order['required_artifacts']['preflight_result']}
- **output_collection_contract:** {work_order['required_artifacts']['output_collection_contract']}

## Handoff
After completion, hand off to: {work_order['handoff_to']}

## Downstream Status
**Blocked:** {work_order['downstream_blocked']}

## Created At
{work_order['created_at']}
"""
    return md


def update_artifact_index(project_root: str, work_orders: List[Dict[str, Any]]) -> None:
    """Update artifact_index.json with work order information."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add work orders section
    artifact_index["work_orders"] = {
        "character_director_work_order": "output/control/work_orders/character_director_identity_review.json",
        "workflow_td_work_order": "output/control/work_orders/workflow_td_identity_workflow_review.json"
    }
    
    # Add current blocking roles
    artifact_index["current_blocking_roles"] = [
        "Character Director",
        "Workflow TD / ComfyUI Technical Director"
    ]
    
    # Ensure downstream_blocked is true
    artifact_index["downstream_blocked"] = True
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def update_episode_ledger(project_root: str, work_orders: List[Dict[str, Any]]) -> None:
    """Update episode_ledger.json with work order creation event."""
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
    
    # Add work order creation event
    event = {
        "event_type": "role_work_orders_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roles": [wo["role"] for wo in work_orders],
        "reason": "identity_qa_failed",
        "downstream_blocked": True,
        "comfyui_generation": False,
        "pipeline_action_rerun": False,
        "work_order_count": len(work_orders)
    }
    
    ledger["events"].append(event)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)


def create_work_orders(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Create work orders for blocked production issues.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with work order creation results
    """
    project_path = Path(project_root)
    work_orders_dir = project_path / "output" / "control" / "work_orders"
    work_orders_dir.mkdir(parents=True, exist_ok=True)
    
    # Load routes and cards
    routes = load_routes(project_root)
    cards = load_relevant_cards(project_root)
    
    # Find blocked shot
    blocked_shot = None
    for shot_id, shot_card in cards.items():
        if shot_id != "character_card" and shot_id != "workflow_card":
            if shot_card.get("blocking_reason") == "identity_qa_failed":
                blocked_shot = shot_card
                break
    
    if not blocked_shot:
        return {
            "status": "no_blocked_shot",
            "project_root": project_root,
            "work_orders_created": 0
        }
    
    # Get character and workflow cards
    character_card = cards.get("character_card", {})
    workflow_card = cards.get("workflow_card", {})
    
    # Create work orders
    character_director_work_order = create_character_director_work_order(
        project_root, blocked_shot, character_card
    )
    workflow_td_work_order = create_workflow_td_work_order(
        project_root, blocked_shot, workflow_card
    )
    
    work_orders = [character_director_work_order, workflow_td_work_order]
    
    # Save JSON work orders
    char_director_path = work_orders_dir / "character_director_identity_review.json"
    workflow_td_path = work_orders_dir / "workflow_td_identity_workflow_review.json"
    
    with open(char_director_path, 'w') as f:
        json.dump(character_director_work_order, f, indent=2)
    
    with open(workflow_td_path, 'w') as f:
        json.dump(workflow_td_work_order, f, indent=2)
    
    # Create markdown summaries
    char_director_md = work_orders_dir / "character_director_identity_review.md"
    workflow_td_md = work_orders_dir / "workflow_td_identity_workflow_review.md"
    
    with open(char_director_md, 'w') as f:
        f.write(create_character_director_markdown(character_director_work_order))
    
    with open(workflow_td_md, 'w') as f:
        f.write(create_workflow_td_markdown(workflow_td_work_order))
    
    # Update artifact index and episode ledger
    update_artifact_index(project_root, work_orders)
    update_episode_ledger(project_root, work_orders)
    
    result = {
        "status": "completed",
        "project_root": project_root,
        "downstream_blocked": True,
        "work_orders_created": len(work_orders),
        "work_orders": [
            {
                "role": wo["role"],
                "work_order_path": str(char_director_path if wo["role"] == "Character Director" else workflow_td_path),
                "blocking_reason": wo["issue"],
                "required_output": "character_identity_approval" if wo["role"] == "Character Director" else "workflow_fit_approval"
            }
            for wo in work_orders
        ]
    }
    
    return result
