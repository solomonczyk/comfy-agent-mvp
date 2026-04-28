"""
Production Role Decision Change Request Router Module

Provides routing preview for decision change request artifacts so the orchestrator
can show the next required owner/action after submitted role decisions requested changes.

This is a read-only routing preview that does NOT:
- Apply decisions
- Open retry gate
- Mark production_accepted=true
- Run ComfyUI or generation
- Mutate role_decisions/
- Mutate final artifacts
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_decision_change_requests(project_root: str) -> List[Dict[str, Any]]:
    """
    Load decision change request artifacts from the project.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        List of decision change request dictionaries
    """
    change_requests_dir = Path(project_root) / "output" / "control" / "decision_change_requests"
    
    if not change_requests_dir.exists():
        return []
    
    change_requests = []
    
    # Load workflow_change_request.json
    workflow_request_path = change_requests_dir / "workflow_change_request.json"
    if workflow_request_path.exists():
        with open(workflow_request_path, 'r') as f:
            change_requests.append(json.load(f))
    
    # Load reference_rebuild_request.json
    reference_request_path = change_requests_dir / "reference_rebuild_request.json"
    if reference_request_path.exists():
        with open(reference_request_path, 'r') as f:
            change_requests.append(json.load(f))
    
    return change_requests


def load_artifact_index(project_root: str) -> Dict[str, Any]:
    """Load artifact index to check current project state."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            return json.load(f)
    
    return {}


def load_episode_ledger(project_root: str) -> Dict[str, Any]:
    """Load episode ledger to append events."""
    ledger_path = Path(project_root) / "output" / "control" / "episode_ledger.json"
    
    if ledger_path.exists():
        with open(ledger_path, 'r') as f:
            return json.load(f)
    
    return {"events": []}


def route_workflow_change_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route a workflow change request to the appropriate target.
    
    Args:
        request: The workflow change request
    
    Returns:
        Dictionary with routing information
    """
    route = {
        "request_type": request.get("request_type", "workflow_change_request"),
        "source_role": request.get("source_role", "Character Director"),
        "target_role": request.get("target_role", "Workflow TD / ComfyUI Technical Director"),
        "recommended_action": request.get("required_action", "revise_identity_workflow_strategy"),
        "reason": request.get("reason", "identity_qa_failed"),
        "blocks_retry": True,
        "routed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return route


def route_reference_rebuild_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route a reference rebuild request to the appropriate target.
    
    Args:
        request: The reference rebuild request
    
    Returns:
        Dictionary with routing information
    """
    route = {
        "request_type": request.get("request_type", "reference_rebuild_request"),
        "source_role": request.get("source_role", "Workflow TD / ComfyUI Technical Director"),
        "target_role": request.get("target_role", "Character Director"),
        "recommended_action": request.get("required_action", "rebuild_or_update_identity_reference_strategy"),
        "reason": request.get("reason", "identity_qa_failed"),
        "blocks_retry": True,
        "routed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return route


def determine_next_actions(routes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Determine next required actions based on routing results.
    
    Args:
        routes: List of routing results
    
    Returns:
        List of next actions with priority
    """
    next_actions = []
    
    # Priority 1: Workflow TD actions (workflow must be revised before reference)
    for route in routes:
        if route.get("target_role") == "Workflow TD / ComfyUI Technical Director":
            next_actions.append({
                "priority": 1,
                "role": route.get("target_role"),
                "task": route.get("recommended_action")
            })
    
    # Priority 2: Character Director actions (reference rebuild after workflow)
    for route in routes:
        if route.get("target_role") == "Character Director":
            next_actions.append({
                "priority": 2,
                "role": route.get("target_role"),
                "task": route.get("recommended_action")
            })
    
    return next_actions


def verify_no_route_to_image_generation(routes: List[Dict[str, Any]]) -> bool:
    """
    Verify that no route points to Image Generation Agent.
    
    Args:
        routes: List of routing results
    
    Returns:
        True if no route points to Image Generation Agent
    """
    for route in routes:
        target_role = route.get("target_role", "")
        if "Image Generation" in target_role or "Generate Frames" in target_role:
            return False
    
    return True


def append_episode_ledger_event(
    project_root: str,
    event_type: str,
    change_requests_found: int,
    retry_gate_open: bool,
    production_accepted: bool,
    downstream_blocked: bool
) -> None:
    """
    Append an event to the episode ledger.
    
    Args:
        project_root: Path to the project root
        event_type: Type of event
        change_requests_found: Number of change requests found
        retry_gate_open: Whether retry gate is open
        production_accepted: Whether production is accepted
        downstream_blocked: Whether downstream is blocked
    """
    ledger = load_episode_ledger(project_root)
    
    event = {
        "event_type": event_type,
        "change_requests_found": change_requests_found,
        "retry_gate_open": retry_gate_open,
        "production_accepted": production_accepted,
        "downstream_blocked": downstream_blocked,
        "comfyui_generation": False,
        "pipeline_action_rerun": False,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    if "events" not in ledger:
        ledger["events"] = []
    
    ledger["events"].append(event)
    
    ledger_path = Path(project_root) / "output" / "control" / "episode_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)


def update_artifact_index_for_routing(
    project_root: str,
    result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with routing information (passive pointer only).
    
    This records the routing without opening retry or applying decisions.
    
    Args:
        project_root: Path to the project root
        result: The result of route_decision_change_requests
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add decision_change_request_routing section as passive pointer
    artifact_index["decision_change_request_routing"] = {
        "status": result.get("status"),
        "change_requests_found": result.get("change_requests_found", 0),
        "retry_gate_open": result.get("retry_gate_open", False),
        "production_accepted": result.get("production_accepted", False),
        "downstream_blocked": result.get("downstream_blocked", True)
    }
    
    # Ensure critical state remains unchanged
    artifact_index["downstream_blocked"] = result.get("downstream_blocked", True)
    artifact_index["production_accepted"] = result.get("production_accepted", False)
    artifact_index["retry_gate_open"] = result.get("retry_gate_open", False)
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def route_decision_change_requests(project_root: str) -> Dict[str, Any]:
    """
    Route decision change requests to show the next required owner/action.
    
    This provides a routing preview for decision change request artifacts so the
    orchestrator can show the next required owner/action after submitted role
    decisions requested changes.
    
    This is a read-only routing preview that does NOT:
    - Apply decisions
    - Open retry gate
    - Mark production_accepted=true
    - Run ComfyUI or generation
    - Mutate role_decisions/
    - Mutate final artifacts
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with routing result
    """
    # Load decision change requests
    change_requests = load_decision_change_requests(project_root)
    
    # Load artifact index to check current state
    artifact_index = load_artifact_index(project_root)
    
    # Route each change request
    routes = []
    for request in change_requests:
        request_type = request.get("request_type")
        
        if request_type == "workflow_change_request":
            route = route_workflow_change_request(request)
            routes.append(route)
        elif request_type == "reference_rebuild_request":
            route = route_reference_rebuild_request(request)
            routes.append(route)
    
    # Determine next required actions
    next_actions = determine_next_actions(routes)
    
    # Verify no route to Image Generation Agent
    no_image_generation_route = verify_no_route_to_image_generation(routes)
    
    # Build result
    result = {
        "status": "blocked",
        "change_requests_found": len(change_requests),
        "ready_for_apply": False,
        "can_retry_generation": False,
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True),
        "routes": routes,
        "next_actions": next_actions,
        "no_image_generation_route": no_image_generation_route
    }
    
    # Update artifact index with passive pointer
    update_artifact_index_for_routing(project_root, result)
    
    # Append event to episode ledger
    append_episode_ledger_event(
        project_root,
        "decision_change_requests_routed",
        result["change_requests_found"],
        result["retry_gate_open"],
        result["production_accepted"],
        result["downstream_blocked"]
    )
    
    return result
