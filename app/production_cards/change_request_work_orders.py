"""
Production Role Decision Change Request Work Orders Module

Provides work order creation for decision change requests so the orchestrator
can assign concrete tasks to Workflow TD and Character Director after routed
change requests.

This is a read-only work order creation that does NOT:
- Execute workflow changes
- Rebuild references
- Apply decisions
- Open retry gate
- Mark production_accepted=true
- Run ComfyUI or generation
- Mutate role_decisions/
- Mutate final artifacts
- Create new generated references
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_change_request_routes(project_root: str) -> Dict[str, Any]:
    """
    Load change request routing result from the project.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with routing result
    """
    from app.production_cards.change_request_router import route_decision_change_requests
    
    return route_decision_change_requests(project_root)


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


def create_workflow_td_change_work_order(route: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a work order for Workflow TD to change the identity workflow.
    
    Args:
        route: The workflow change request routing result
    
    Returns:
        Dictionary with work order structure
    """
    work_order = {
        "work_order_type": "workflow_change_order",
        "role": "Workflow TD / ComfyUI Technical Director",
        "source_request": route.get("request_type", "workflow_change_request"),
        "source_decision": route.get("source_decision", "request_workflow_change"),
        "blocked_shot": route.get("blocked_shot", "shot01"),
        "reason": route.get("reason", "identity_qa_failed"),
        "required_action": route.get("recommended_action", "revise_identity_workflow_strategy"),
        "required_generation_mode": route.get("required_generation_mode", "gorynych_identity"),
        "legacy_reference_locked_allowed_for_production": route.get("legacy_reference_locked_allowed_for_production", False),
        "required_outputs": [
            "updated_workflow_strategy",
            "workflow_audit",
            "required_nodes",
            "required_models",
            "preflight_result",
            "output_collection_contract"
        ],
        "execution_performed": False,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return work_order


def create_character_director_reference_rebuild_work_order(route: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a work order for Character Director to rebuild the reference strategy.
    
    Args:
        route: The reference rebuild request routing result
    
    Returns:
        Dictionary with work order structure
    """
    work_order = {
        "work_order_type": "reference_rebuild_order",
        "role": "Character Director",
        "source_request": route.get("request_type", "reference_rebuild_request"),
        "source_decision": route.get("source_decision", "request_reference_rebuild"),
        "blocked_shot": route.get("blocked_shot", "shot01"),
        "reason": route.get("reason", "identity_qa_failed"),
        "required_action": route.get("recommended_action", "rebuild_or_update_identity_reference_strategy"),
        "required_generation_mode": route.get("required_generation_mode", "gorynych_identity"),
        "required_outputs": [
            "updated_character_identity_rules",
            "updated_reference_strategy",
            "identity_acceptance_criteria",
            "reference_rebuild_notes"
        ],
        "execution_performed": False,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return work_order


def create_work_order_summary(routes: List[Dict[str, Any]], artifact_index: Dict[str, Any]) -> str:
    """
    Create a markdown summary of the change request work orders.
    
    Args:
        routes: List of routing results
        artifact_index: Current artifact index state
    
    Returns:
        Markdown summary string
    """
    summary = "# Change Request Work Order Summary\n\n"
    
    summary += "## Current Change Request Routing\n\n"
    
    for route in routes:
        summary += f"### {route.get('request_type', 'unknown')}\n"
        summary += f"- **Source Role**: {route.get('source_role', 'unknown')}\n"
        summary += f"- **Target Role**: {route.get('target_role', 'unknown')}\n"
        summary += f"- **Required Action**: {route.get('recommended_action', 'unknown')}\n"
        summary += f"- **Reason**: {route.get('reason', 'unknown')}\n"
        summary += f"- **Blocks Retry**: {route.get('blocks_retry', True)}\n\n"
    
    summary += "## Each Role's Required Work\n\n"
    
    for route in routes:
        role = route.get('target_role', 'unknown')
        action = route.get('recommended_action', 'unknown')
        
        summary += f"### {role}\n"
        summary += f"- **Task**: {action}\n"
        
        if route.get('request_type') == 'workflow_change_request':
            summary += "- **Required Outputs**:\n"
            summary += "  - updated_workflow_strategy\n"
            summary += "  - workflow_audit\n"
            summary += "  - required_nodes\n"
            summary += "  - required_models\n"
            summary += "  - preflight_result\n"
            summary += "  - output_collection_contract\n"
            summary += "- **Required Generation Mode**: gorynych_identity\n"
            summary += "- **Legacy Reference Locked**: Not allowed for production\n"
        elif route.get('request_type') == 'reference_rebuild_request':
            summary += "- **Required Outputs**:\n"
            summary += "  - updated_character_identity_rules\n"
            summary += "  - updated_reference_strategy\n"
            summary += "  - identity_acceptance_criteria\n"
            summary += "  - reference_rebuild_notes\n"
            summary += "- **Required Generation Mode**: gorynych_identity\n"
        
        summary += "\n"
    
    summary += "## Why Retry Remains Blocked\n\n"
    summary += "Retry generation is blocked because:\n"
    summary += "- Role decisions remain pending (not yet approved)\n"
    summary += "- Change requests have been created but not yet executed\n"
    summary += "- Workflow TD must revise the identity workflow strategy\n"
    summary += "- Character Director must rebuild or update the reference strategy\n"
    summary += "- No generation has been authorized\n\n"
    
    summary += "## What Must Happen Before Decisions Can Be Resubmitted\n\n"
    summary += "Before role decisions can be resubmitted for approval:\n"
    summary += "1. Workflow TD must complete the workflow change work order\n"
    summary += "2. Character Director must complete the reference rebuild work order\n"
    summary += "3. Both roles must provide the required outputs\n"
    summary += "4. New decision drafts can then be created with updated evidence\n"
    summary += "5. Decisions must be approved (not request changes)\n\n"
    
    summary += "## No Generation Authorized\n\n"
    summary += "This work order creation does NOT authorize any generation:\n"
    summary += "- No ComfyUI execution will occur\n"
    summary += "- No frames will be generated\n"
    summary += "- No references will be rebuilt\n"
    summary += "- No workflow execution outputs will be created\n"
    summary += "- This is a planning step only\n\n"
    
    summary += "## Current State\n\n"
    summary += f"- **Retry Gate Open**: {artifact_index.get('retry_gate_open', False)}\n"
    summary += f"- **Production Accepted**: {artifact_index.get('production_accepted', False)}\n"
    summary += f"- **Downstream Blocked**: {artifact_index.get('downstream_blocked', True)}\n"
    summary += f"- **Role Decisions Status**: {artifact_index.get('role_decisions', {}).get('decision_status', 'pending')}\n"
    
    return summary


def append_episode_ledger_event(
    project_root: str,
    event_type: str,
    work_orders_created: int,
    execution_performed: bool,
    apply_performed: bool,
    retry_gate_open: bool,
    production_accepted: bool,
    downstream_blocked: bool
) -> None:
    """
    Append an event to the episode ledger.
    
    Args:
        project_root: Path to the project root
        event_type: Type of event
        work_orders_created: Number of work orders created
        execution_performed: Whether execution was performed
        apply_performed: Whether apply was performed
        retry_gate_open: Whether retry gate is open
        production_accepted: Whether production is accepted
        downstream_blocked: Whether downstream is blocked
    """
    ledger = load_episode_ledger(project_root)
    
    event = {
        "event_type": event_type,
        "work_orders_created": work_orders_created,
        "execution_performed": execution_performed,
        "apply_performed": apply_performed,
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


def update_artifact_index_for_work_orders(
    project_root: str,
    result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with work order information (passive pointer only).
    
    This records the work order creation without opening retry or applying decisions.
    
    Args:
        project_root: Path to the project root
        result: The result of create_change_request_work_orders
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add change_request_work_orders section as passive pointer
    artifact_index["change_request_work_orders"] = {
        "status": "created",
        "work_orders_created": result.get("work_orders_created", 0),
        "execution_performed": result.get("execution_performed", False),
        "apply_performed": result.get("apply_performed", False),
        "ready_for_apply": result.get("ready_for_apply", False),
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


def create_change_request_work_orders(project_root: str) -> Dict[str, Any]:
    """
    Create work orders for routed decision change requests.
    
    This provides concrete role work orders for Workflow TD and Character Director
    after routed change requests, without executing workflow changes, rebuilding
    references, applying decisions, or opening retry generation.
    
    This is a read-only work order creation that does NOT:
    - Execute workflow changes
    - Rebuild references
    - Apply decisions
    - Open retry gate
    - Mark production_accepted=true
    - Run ComfyUI or generation
    - Mutate role_decisions/
    - Mutate final artifacts
    - Create new generated references
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with work order creation result
    """
    # Load change request routing
    routing_result = load_change_request_routes(project_root)
    
    # Load artifact index to check current state
    artifact_index = load_artifact_index(project_root)
    
    # Create output directory
    work_orders_dir = Path(project_root) / "output" / "control" / "change_request_work_orders"
    work_orders_dir.mkdir(parents=True, exist_ok=True)
    
    # Create work orders based on routes
    routes = routing_result.get("routes", [])
    work_orders_created = 0
    
    for route in routes:
        request_type = route.get("request_type")
        
        if request_type == "workflow_change_request":
            work_order = create_workflow_td_change_work_order(route)
            work_order_path = work_orders_dir / "workflow_td_identity_workflow_change_order.json"
            with open(work_order_path, 'w') as f:
                json.dump(work_order, f, indent=2)
            work_orders_created += 1
        elif request_type == "reference_rebuild_request":
            work_order = create_character_director_reference_rebuild_work_order(route)
            work_order_path = work_orders_dir / "character_director_reference_rebuild_order.json"
            with open(work_order_path, 'w') as f:
                json.dump(work_order, f, indent=2)
            work_orders_created += 1
    
    # Create work order summary
    summary = create_work_order_summary(routes, artifact_index)
    summary_path = work_orders_dir / "CHANGE_REQUEST_WORK_ORDER_SUMMARY.md"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    # Build result
    result = {
        "status": "completed",
        "work_orders_created": work_orders_created,
        "execution_performed": False,
        "apply_performed": False,
        "ready_for_apply": False,
        "can_retry_generation": False,
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True)
    }
    
    # Update artifact index with passive pointer
    update_artifact_index_for_work_orders(project_root, result)
    
    # Append event to episode ledger
    append_episode_ledger_event(
        project_root,
        "change_request_work_orders_created",
        result["work_orders_created"],
        result["execution_performed"],
        result["apply_performed"],
        result["retry_gate_open"],
        result["production_accepted"],
        result["downstream_blocked"]
    )
    
    return result


def validate_change_request_work_orders(project_root: str) -> Dict[str, Any]:
    """
    Validate that change request work orders exist and are correctly structured.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with validation result
    """
    work_orders_dir = Path(project_root) / "output" / "control" / "change_request_work_orders"
    
    if not work_orders_dir.exists():
        return {
            "status": "invalid",
            "work_orders_found": 0,
            "validation_errors": ["Work orders directory does not exist"]
        }
    
    work_orders = []
    validation_errors = []
    
    # Check workflow TD work order
    workflow_order_path = work_orders_dir / "workflow_td_identity_workflow_change_order.json"
    if workflow_order_path.exists():
        with open(workflow_order_path, 'r') as f:
            work_order = json.load(f)
        
        # Validate structure
        if work_order.get("work_order_type") != "workflow_change_order":
            validation_errors.append("Workflow TD work order has incorrect work_order_type")
        if work_order.get("execution_performed") != False:
            validation_errors.append("Workflow TD work order has execution_performed=true")
        if work_order.get("apply_performed") != False:
            validation_errors.append("Workflow TD work order has apply_performed=true")
        if work_order.get("retry_gate_open") != False:
            validation_errors.append("Workflow TD work order has retry_gate_open=true")
        if work_order.get("production_accepted") != False:
            validation_errors.append("Workflow TD work order has production_accepted=true")
        if work_order.get("downstream_blocked") != True:
            validation_errors.append("Workflow TD work order has downstream_blocked=false")
        
        work_orders.append(work_order)
    else:
        validation_errors.append("Workflow TD work order file does not exist")
    
    # Check Character Director work order
    character_order_path = work_orders_dir / "character_director_reference_rebuild_order.json"
    if character_order_path.exists():
        with open(character_order_path, 'r') as f:
            work_order = json.load(f)
        
        # Validate structure
        if work_order.get("work_order_type") != "reference_rebuild_order":
            validation_errors.append("Character Director work order has incorrect work_order_type")
        if work_order.get("execution_performed") != False:
            validation_errors.append("Character Director work order has execution_performed=true")
        if work_order.get("apply_performed") != False:
            validation_errors.append("Character Director work order has apply_performed=true")
        if work_order.get("retry_gate_open") != False:
            validation_errors.append("Character Director work order has retry_gate_open=true")
        if work_order.get("production_accepted") != False:
            validation_errors.append("Character Director work order has production_accepted=true")
        if work_order.get("downstream_blocked") != True:
            validation_errors.append("Character Director work order has downstream_blocked=false")
        
        work_orders.append(work_order)
    else:
        validation_errors.append("Character Director work order file does not exist")
    
    # Check summary
    summary_path = work_orders_dir / "CHANGE_REQUEST_WORK_ORDER_SUMMARY.md"
    if not summary_path.exists():
        validation_errors.append("Work order summary file does not exist")
    
    # Determine next required roles
    next_required_roles = []
    for work_order in work_orders:
        role = work_order.get("role")
        if role and role not in next_required_roles:
            next_required_roles.append(role)
    
    # Load artifact index to check state
    artifact_index = load_artifact_index(project_root)
    
    # Build result
    result = {
        "status": "valid" if not validation_errors else "invalid",
        "work_orders_found": len(work_orders),
        "next_required_roles": next_required_roles,
        "execution_performed": all(wo.get("execution_performed", False) for wo in work_orders),
        "ready_for_apply": False,
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True),
        "validation_errors": validation_errors
    }
    
    return result
