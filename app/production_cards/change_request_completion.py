"""
Production Role Decision Change Request Completion Contracts Module

Provides completion templates/contracts for Workflow TD and Character Director
change request work orders so the orchestrator can track work order completion
status without executing workflow changes, rebuilding references, applying decisions,
or opening retry generation.

This is a read-only completion contract creation that does NOT:
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


def load_change_request_work_orders(project_root: str) -> Dict[str, Any]:
    """
    Load change request work orders from the project.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with work order data
    """
    work_orders_dir = Path(project_root) / "output" / "control" / "change_request_work_orders"
    
    work_orders = {}
    
    # Load Workflow TD work order
    workflow_order_path = work_orders_dir / "workflow_td_identity_workflow_change_order.json"
    if workflow_order_path.exists():
        with open(workflow_order_path, 'r') as f:
            work_orders["workflow_td"] = json.load(f)
    
    # Load Character Director work order
    character_order_path = work_orders_dir / "character_director_reference_rebuild_order.json"
    if character_order_path.exists():
        with open(character_order_path, 'r') as f:
            work_orders["character_director"] = json.load(f)
    
    return work_orders


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


def create_workflow_td_completion_template(work_order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a completion template for Workflow TD workflow change work order.
    
    Args:
        work_order: The Workflow TD work order
    
    Returns:
        Dictionary with completion template structure
    """
    template = {
        "completion_type": "workflow_change_completion",
        "role": "Workflow TD / ComfyUI Technical Director",
        "source_work_order": "workflow_td_identity_workflow_change_order.json",
        "blocked_shot": work_order.get("blocked_shot", "shot01"),
        "completion_status": "template",
        "execution_performed": False,
        "selected_resolution": None,
        "allowed_resolutions": [
            "workflow_strategy_updated",
            "missing_nodes_reported",
            "missing_models_reported",
            "reference_rebuild_required",
            "blocked"
        ],
        "required_outputs": [
            "updated_workflow_strategy",
            "workflow_audit",
            "required_nodes",
            "required_models",
            "preflight_result",
            "output_collection_contract"
        ],
        "current_required_generation_mode": work_order.get("required_generation_mode", "gorynych_identity"),
        "legacy_reference_locked_allowed_for_production": work_order.get("legacy_reference_locked_allowed_for_production", False),
        "ready_for_resubmission": False,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return template


def create_character_director_completion_template(work_order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a completion template for Character Director reference rebuild work order.
    
    Args:
        work_order: The Character Director work order
    
    Returns:
        Dictionary with completion template structure
    """
    template = {
        "completion_type": "reference_rebuild_completion",
        "role": "Character Director",
        "source_work_order": "character_director_reference_rebuild_order.json",
        "blocked_shot": work_order.get("blocked_shot", "shot01"),
        "completion_status": "template",
        "execution_performed": False,
        "selected_resolution": None,
        "allowed_resolutions": [
            "reference_strategy_updated",
            "identity_rules_updated",
            "new_reference_required",
            "workflow_change_required",
            "blocked"
        ],
        "required_outputs": [
            "updated_character_identity_rules",
            "updated_reference_strategy",
            "identity_acceptance_criteria",
            "reference_rebuild_notes"
        ],
        "ready_for_resubmission": False,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return template


def create_completion_instructions(work_orders: Dict[str, Any]) -> str:
    """
    Create markdown instructions for change request completion.
    
    Args:
        work_orders: Dictionary of work orders
    
    Returns:
        Markdown instructions string
    """
    instructions = "# Change Request Completion Instructions\n\n"
    
    instructions += "## Overview\n\n"
    instructions += "These completion templates provide formal contracts for Workflow TD and Character Director\n"
    instructions += "to complete their assigned work orders from the routed change requests. These are templates,\n"
    instructions += "not completions—no work has been executed yet.\n\n"
    
    instructions += "## Workflow TD / ComfyUI Technical Director\n\n"
    if "workflow_td" in work_orders:
        workflow_order = work_orders["workflow_td"]
        instructions += f"### Work Order: {workflow_order.get('required_action', 'unknown')}\n"
        instructions += f"### Required Generation Mode: {workflow_order.get('required_generation_mode', 'gorynych_identity')}\n\n"
        instructions += "### Required Outputs:\n"
        for output in workflow_order.get("required_outputs", []):
            instructions += f"- {output}\n"
        
        instructions += "\n### Allowed Resolutions:\n"
        instructions += "- **workflow_strategy_updated**: Workflow strategy has been revised and is ready for retry\n"
        instructions += "- **missing_nodes_reported**: Required nodes are missing and must be procured before retry\n"
        instructions += "- **missing_models_reported**: Required models are missing and must be procured before retry\n"
        instructions += "- **reference_rebuild_required**: Character Director must rebuild reference strategy first\n"
        instructions += "- **blocked**: Work cannot proceed due to external dependencies\n"
    
    instructions += "\n## Character Director\n\n"
    if "character_director" in work_orders:
        character_order = work_orders["character_director"]
        instructions += f"### Work Order: {character_order.get('required_action', 'unknown')}\n\n"
        instructions += "### Required Outputs:\n"
        for output in character_order.get("required_outputs", []):
            instructions += f"- {output}\n"
        
        instructions += "\n### Allowed Resolutions:\n"
        instructions += "- **reference_strategy_updated**: Reference strategy has been updated and is ready for retry\n"
        instructions += "- **identity_rules_updated**: Character identity rules have been updated\n"
        instructions += "- **new_reference_required**: New reference images must be created before retry\n"
        instructions += "- **workflow_change_required**: Workflow TD must revise workflow strategy first\n"
        instructions += "- **blocked**: Work cannot proceed due to external dependencies\n"
    
    instructions += "\n## Why These Are Templates, Not Completions\n\n"
    instructions += "These completion templates are NOT completions because:\n"
    instructions += "- No workflow execution has occurred\n"
    instructions += "- No reference rebuild has occurred\n"
    instructions += "- No required outputs have been provided\n"
    instructions += "- No resolution has been selected\n"
    instructions += "- completion_status is 'template', not 'completed'\n"
    instructions += "- selected_resolution is null\n\n"
    
    instructions += "## Why Retry Remains Blocked\n\n"
    instructions += "Retry generation is blocked because:\n"
    instructions += "- Completion templates are not yet completed\n"
    instructions += "- Required outputs have not been provided\n"
    instructions += "- No resolution has been selected\n"
    instructions += "- Role decisions remain pending (not yet resubmitted)\n"
    instructions += "- No generation has been authorized\n\n"
    
    instructions += "## What Must Happen Before Retry Can Be Authorized\n\n"
    instructions += "Before retry generation can be authorized:\n"
    instructions += "1. Workflow TD must complete their work order with required outputs\n"
    instructions += "2. Character Director must complete their work order with required outputs\n"
    instructions += "3. Both roles must select a valid resolution\n"
    instructions += "4. Completion status must change from 'template' to 'completed'\n"
    instructions += "5. New role decision drafts can be created with updated evidence\n"
    instructions += "6. Role decisions must be submitted and approved (not request changes)\n\n"
    
    instructions += "## No Generation Authorized\n\n"
    instructions += "This completion contract creation does NOT authorize any generation:\n"
    instructions += "- No ComfyUI execution will occur\n"
    instructions += "- No frames will be generated\n"
    instructions += "- No references will be rebuilt\n"
    instructions += "- No workflow execution outputs will be created\n"
    instructions += "- This is a planning step only\n\n"
    
    return instructions


def append_episode_ledger_event(
    project_root: str,
    event_type: str,
    completion_templates_created: int,
    execution_performed: bool,
    ready_for_resubmission: bool,
    retry_gate_open: bool,
    production_accepted: bool,
    downstream_blocked: bool
) -> None:
    """
    Append an event to the episode ledger.
    
    Args:
        project_root: Path to the project root
        event_type: Type of event
        completion_templates_created: Number of completion templates created
        execution_performed: Whether execution was performed
        ready_for_resubmission: Whether ready for resubmission
        retry_gate_open: Whether retry gate is open
        production_accepted: Whether production is accepted
        downstream_blocked: Whether downstream is blocked
    """
    ledger = load_episode_ledger(project_root)
    
    event = {
        "event_type": event_type,
        "completion_templates_created": completion_templates_created,
        "execution_performed": execution_performed,
        "ready_for_resubmission": ready_for_resubmission,
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


def update_artifact_index_for_completion_contracts(
    project_root: str,
    result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with completion contract information (passive pointer only).
    
    This records the completion contract creation without opening retry or applying decisions.
    
    Args:
        project_root: Path to the project root
        result: The result of create_change_request_completion_contracts
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add change_request_completion_contracts section as passive pointer
    artifact_index["change_request_completion_contracts"] = {
        "status": "created",
        "completion_templates_created": result.get("completion_templates_created", 0),
        "submitted_completions_found": result.get("submitted_completions_found", 0),
        "execution_performed": result.get("execution_performed", False),
        "ready_for_resubmission": result.get("ready_for_resubmission", False),
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


def create_change_request_completion_contracts(project_root: str) -> Dict[str, Any]:
    """
    Create completion templates/contracts for change request work orders.
    
    This provides formal completion contracts for Workflow TD and Character Director
    work orders without executing workflow changes, rebuilding references, applying
    decisions, or opening retry generation.
    
    This is a read-only completion contract creation that does NOT:
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
        Dictionary with completion contract creation result
    """
    # Load change request work orders
    work_orders = load_change_request_work_orders(project_root)
    
    # Load artifact index to check current state
    artifact_index = load_artifact_index(project_root)
    
    # Create output directory
    completions_dir = Path(project_root) / "output" / "control" / "change_request_completions"
    completions_dir.mkdir(parents=True, exist_ok=True)
    
    # Create completion templates based on work orders
    completion_templates_created = 0
    
    if "workflow_td" in work_orders:
        template = create_workflow_td_completion_template(work_orders["workflow_td"])
        template_path = completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        completion_templates_created += 1
    
    if "character_director" in work_orders:
        template = create_character_director_completion_template(work_orders["character_director"])
        template_path = completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
        with open(template_path, 'w') as f:
            json.dump(template, f, indent=2)
        completion_templates_created += 1
    
    # Create completion instructions
    instructions = create_completion_instructions(work_orders)
    instructions_path = completions_dir / "CHANGE_REQUEST_COMPLETION_INSTRUCTIONS.md"
    with open(instructions_path, 'w') as f:
        f.write(instructions)
    
    # Build result
    result = {
        "status": "completed",
        "completion_templates_created": completion_templates_created,
        "submitted_completions_found": 0,
        "execution_performed": False,
        "ready_for_resubmission": False,
        "ready_for_apply": False,
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True)
    }
    
    # Update artifact index with passive pointer
    update_artifact_index_for_completion_contracts(project_root, result)
    
    # Append event to episode ledger
    append_episode_ledger_event(
        project_root,
        "change_request_completion_contracts_created",
        result["completion_templates_created"],
        result["execution_performed"],
        result["ready_for_resubmission"],
        result["retry_gate_open"],
        result["production_accepted"],
        result["downstream_blocked"]
    )
    
    return result


def validate_change_request_completion_contracts(project_root: str) -> Dict[str, Any]:
    """
    Validate that change request completion contracts exist and are correctly structured.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with validation result
    """
    completions_dir = Path(project_root) / "output" / "control" / "change_request_completions"
    
    if not completions_dir.exists():
        return {
            "status": "invalid",
            "completion_templates_found": 0,
            "validation_errors": ["Completions directory does not exist"]
        }
    
    completion_templates = []
    submitted_completions = []
    validation_errors = []
    
    # Check Workflow TD completion template
    workflow_template_path = completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
    if workflow_template_path.exists():
        with open(workflow_template_path, 'r') as f:
            template = json.load(f)
        
        # Validate structure
        if template.get("completion_type") != "workflow_change_completion":
            validation_errors.append("Workflow TD template has incorrect completion_type")
        if template.get("completion_status") != "template":
            validation_errors.append("Workflow TD template has completion_status != template")
        if template.get("selected_resolution") is not None:
            validation_errors.append("Workflow TD template has selected_resolution != null")
        if template.get("execution_performed") != False:
            validation_errors.append("Workflow TD template has execution_performed=true")
        if template.get("ready_for_resubmission") != False:
            validation_errors.append("Workflow TD template has ready_for_resubmission=true")
        if template.get("retry_gate_open") != False:
            validation_errors.append("Workflow TD template has retry_gate_open=true")
        if template.get("production_accepted") != False:
            validation_errors.append("Workflow TD template has production_accepted=true")
        if template.get("downstream_blocked") != True:
            validation_errors.append("Workflow TD template has downstream_blocked=false")
        
        completion_templates.append(template)
    else:
        validation_errors.append("Workflow TD completion template file does not exist")
    
    # Check Character Director completion template
    character_template_path = completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
    if character_template_path.exists():
        with open(character_template_path, 'r') as f:
            template = json.load(f)
        
        # Validate structure
        if template.get("completion_type") != "reference_rebuild_completion":
            validation_errors.append("Character Director template has incorrect completion_type")
        if template.get("completion_status") != "template":
            validation_errors.append("Character Director template has completion_status != template")
        if template.get("selected_resolution") is not None:
            validation_errors.append("Character Director template has selected_resolution != null")
        if template.get("execution_performed") != False:
            validation_errors.append("Character Director template has execution_performed=true")
        if template.get("ready_for_resubmission") != False:
            validation_errors.append("Character Director template has ready_for_resubmission=true")
        if template.get("retry_gate_open") != False:
            validation_errors.append("Character Director template has retry_gate_open=true")
        if template.get("production_accepted") != False:
            validation_errors.append("Character Director template has production_accepted=true")
        if template.get("downstream_blocked") != True:
            validation_errors.append("Character Director template has downstream_blocked=false")
        
        completion_templates.append(template)
    else:
        validation_errors.append("Character Director completion template file does not exist")
    
    # Check instructions
    instructions_path = completions_dir / "CHANGE_REQUEST_COMPLETION_INSTRUCTIONS.md"
    if not instructions_path.exists():
        validation_errors.append("Completion instructions file does not exist")
    
    # Load artifact index to check state
    artifact_index = load_artifact_index(project_root)
    
    # Build result
    result = {
        "status": "valid" if not validation_errors else "invalid",
        "completion_templates_found": len(completion_templates),
        "submitted_completions_found": len(submitted_completions),
        "execution_performed": all(ct.get("execution_performed", False) for ct in completion_templates),
        "ready_for_resubmission": all(ct.get("ready_for_resubmission", False) for ct in completion_templates),
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True),
        "validation_errors": validation_errors
    }
    
    return result
