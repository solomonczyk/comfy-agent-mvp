"""
Production Change Request Execution Plan Module

Creates concrete execution plans for unresolved change request work orders before any
workflow change, reference rebuild, completion submission, apply, or retry generation
is allowed.

This is a read-only execution plan creation that does NOT:
- Execute workflow changes
- Rebuild references
- Apply decisions
- Open retry gate
- Mark production_accepted=true
- Run ComfyUI or generation
- Mutate role_decisions/
- Mutate final artifacts
- Create new generated references
- Submit completions
- Set execution_performed=true
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


def load_completion_contracts(project_root: str) -> Dict[str, Any]:
    """
    Load change request completion contracts from the project.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with completion contract data
    """
    completions_dir = Path(project_root) / "output" / "control" / "change_request_completions"
    
    completions = {}
    
    # Load Workflow TD completion template
    workflow_template_path = completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
    if workflow_template_path.exists():
        with open(workflow_template_path, 'r') as f:
            completions["workflow_td"] = json.load(f)
    
    # Load Character Director completion template
    character_template_path = completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
    if character_template_path.exists():
        with open(character_template_path, 'r') as f:
            completions["character_director"] = json.load(f)
    
    return completions


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


def create_workflow_td_execution_plan(work_order: Dict[str, Any], completion_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an execution plan for Workflow TD workflow change work order.
    
    Args:
        work_order: The Workflow TD work order
        completion_template: The Workflow TD completion template
    
    Returns:
        Dictionary with execution plan structure
    """
    plan = {
        "plan_type": "workflow_td_change_request_execution_plan",
        "role": "Workflow TD / ComfyUI Technical Director",
        "source_work_order": "workflow_td_identity_workflow_change_order.json",
        "source_completion_template": "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json",
        "blocked_shot": work_order.get("blocked_shot", "shot01"),
        "reason": work_order.get("reason", "identity_qa_failed"),
        "execution_status": "planned",
        "execution_performed": False,
        "required_generation_mode": work_order.get("required_generation_mode", "gorynych_identity"),
        "legacy_reference_locked_allowed_for_production": work_order.get("legacy_reference_locked_allowed_for_production", False),
        "planned_steps": [
            "audit_current_identity_workflow_strategy",
            "verify_required_nodes",
            "verify_required_models",
            "define_updated_workflow_strategy",
            "define_preflight_requirements",
            "define_output_collection_contract"
        ],
        "required_outputs_before_completion": [
            "updated_workflow_strategy",
            "workflow_audit",
            "required_nodes",
            "required_models",
            "preflight_result",
            "output_collection_contract"
        ],
        "completion_submission_allowed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return plan


def create_character_director_execution_plan(work_order: Dict[str, Any], completion_template: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create an execution plan for Character Director reference rebuild work order.
    
    Args:
        work_order: The Character Director work order
        completion_template: The Character Director completion template
    
    Returns:
        Dictionary with execution plan structure
    """
    plan = {
        "plan_type": "character_director_reference_rebuild_execution_plan",
        "role": "Character Director",
        "source_work_order": "character_director_reference_rebuild_order.json",
        "source_completion_template": "character_director_reference_rebuild.COMPLETION_TEMPLATE.json",
        "blocked_shot": work_order.get("blocked_shot", "shot01"),
        "reason": work_order.get("reason", "identity_qa_failed"),
        "execution_status": "planned",
        "execution_performed": False,
        "planned_steps": [
            "review_identity_failure_evidence",
            "review_current_character_identity_rules",
            "define_updated_reference_strategy",
            "define_identity_acceptance_criteria",
            "write_reference_rebuild_notes"
        ],
        "required_outputs_before_completion": [
            "updated_character_identity_rules",
            "updated_reference_strategy",
            "identity_acceptance_criteria",
            "reference_rebuild_notes"
        ],
        "completion_submission_allowed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return plan


def create_execution_plan_summary(work_orders: Dict[str, Any], execution_plans: Dict[str, Any], artifact_index: Dict[str, Any]) -> str:
    """
    Create a markdown summary of the change request execution plans.
    
    Args:
        work_orders: Dictionary of work orders
        execution_plans: Dictionary of execution plans
        artifact_index: Current artifact index state
    
    Returns:
        Markdown summary string
    """
    summary = "# Change Request Execution Plan\n\n"
    
    summary += "## Overview\n\n"
    summary += "This document provides concrete execution plans for unresolved change request work orders. "
    summary += "These are plans for future execution—no work has been performed yet.\n\n"
    
    summary += "## Unresolved Work Orders\n\n"
    
    if "workflow_td" in work_orders:
        workflow_order = work_orders["workflow_td"]
        summary += f"### Workflow TD / ComfyUI Technical Director\n"
        summary += f"- **Work Order**: {workflow_order.get('required_action', 'unknown')}\n"
        summary += f"- **Blocked Shot**: {workflow_order.get('blocked_shot', 'shot01')}\n"
        summary += f"- **Reason**: {workflow_order.get('reason', 'unknown')}\n"
        summary += f"- **Required Generation Mode**: {workflow_order.get('required_generation_mode', 'gorynych_identity')}\n\n"
    
    if "character_director" in work_orders:
        character_order = work_orders["character_director"]
        summary += f"### Character Director\n"
        summary += f"- **Work Order**: {character_order.get('required_action', 'unknown')}\n"
        summary += f"- **Blocked Shot**: {character_order.get('blocked_shot', 'shot01')}\n"
        summary += f"- **Reason**: {character_order.get('reason', 'unknown')}\n\n"
    
    summary += "## Planned Steps\n\n"
    
    if "workflow_td" in execution_plans:
        workflow_plan = execution_plans["workflow_td"]
        summary += f"### Workflow TD / ComfyUI Technical Director\n\n"
        summary += "Planned steps:\n"
        for step in workflow_plan.get("planned_steps", []):
            summary += f"1. {step}\n"
        summary += "\n"
    
    if "character_director" in execution_plans:
        character_plan = execution_plans["character_director"]
        summary += f"### Character Director\n\n"
        summary += "Planned steps:\n"
        for step in character_plan.get("planned_steps", []):
            summary += f"1. {step}\n"
        summary += "\n"
    
    summary += "## Required Outputs Before Completion\n\n"
    
    if "workflow_td" in execution_plans:
        workflow_plan = execution_plans["workflow_td"]
        summary += f"### Workflow TD / ComfyUI Technical Director\n\n"
        summary += "Required outputs:\n"
        for output in workflow_plan.get("required_outputs_before_completion", []):
            summary += f"- {output}\n"
        summary += "\n"
    
    if "character_director" in execution_plans:
        character_plan = execution_plans["character_director"]
        summary += f"### Character Director\n\n"
        summary += "Required outputs:\n"
        for output in character_plan.get("required_outputs_before_completion", []):
            summary += f"- {output}\n"
        summary += "\n"
    
    summary += "## Why Execution Remains Planned\n\n"
    summary += "Execution remains planned (not performed) because:\n"
    summary += "- These are execution plans, not actual execution\n"
    summary += "- No workflow changes have been made\n"
    summary += "- No reference rebuild has been performed\n"
    summary += "- No required outputs have been produced\n"
    summary += "- execution_status is 'planned', not 'executed'\n"
    summary += "- execution_performed is false\n\n"
    
    summary += "## Why Retry Remains Blocked\n\n"
    summary += "Retry generation is blocked because:\n"
    summary += "- Execution plans are not yet executed\n"
    summary += "- Required outputs have not been provided\n"
    summary += "- Completion submissions have not been made\n"
    summary += "- Role decisions remain pending (not yet resubmitted)\n"
    summary += "- No generation has been authorized\n\n"
    
    summary += "## What Must Happen Before Retry Can Be Authorized\n\n"
    summary += "Before retry generation can be authorized:\n"
    summary += "1. Workflow TD must execute their execution plan\n"
    summary += "2. Character Director must execute their execution plan\n"
    summary += "3. Both roles must provide the required outputs\n"
    summary += "4. Both roles must submit their completion files\n"
    summary += "5. Completions must be validated\n"
    summary += "6. New role decision drafts can be created with updated evidence\n"
    summary += "7. Role decisions must be submitted and approved (not request changes)\n\n"
    
    summary += "## No Generation Authorized\n\n"
    summary += "This execution plan creation does NOT authorize any generation:\n"
    summary += "- No ComfyUI execution will occur\n"
    summary += "- No frames will be generated\n"
    summary += "- No references will be rebuilt\n"
    summary += "- No workflow execution outputs will be created\n"
    summary += "- This is a planning step only\n\n"
    
    summary += "## Current State\n\n"
    summary += f"- **Execution Status**: planned\n"
    summary += f"- **Execution Performed**: False\n"
    summary += f"- **Completion Submission Allowed**: False\n"
    summary += f"- **Ready for Resubmission**: {artifact_index.get('change_request_completion_contracts', {}).get('ready_for_resubmission', False)}\n"
    summary += f"- **Retry Gate Open**: {artifact_index.get('retry_gate_open', False)}\n"
    summary += f"- **Production Accepted**: {artifact_index.get('production_accepted', False)}\n"
    summary += f"- **Downstream Blocked**: {artifact_index.get('downstream_blocked', True)}\n"
    
    return summary


def append_episode_ledger_event(
    project_root: str,
    event_type: str,
    execution_plans_created: int,
    execution_performed: bool,
    completion_submission_allowed: bool,
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
        execution_plans_created: Number of execution plans created
        execution_performed: Whether execution was performed
        completion_submission_allowed: Whether completion submission is allowed
        ready_for_resubmission: Whether ready for resubmission
        retry_gate_open: Whether retry gate is open
        production_accepted: Whether production is accepted
        downstream_blocked: Whether downstream is blocked
    """
    ledger = load_episode_ledger(project_root)
    
    event = {
        "event_type": event_type,
        "execution_plans_created": execution_plans_created,
        "execution_performed": execution_performed,
        "completion_submission_allowed": completion_submission_allowed,
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


def update_artifact_index_for_execution_plan(
    project_root: str,
    result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with execution plan information (passive pointer only).
    
    This records the execution plan creation without opening retry or applying decisions.
    
    Args:
        project_root: Path to the project root
        result: The result of create_change_request_execution_plan
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add change_request_execution_plan section as passive pointer
    artifact_index["change_request_execution_plan"] = {
        "status": "created",
        "execution_plans_created": result.get("execution_plans_created", 0),
        "execution_performed": result.get("execution_performed", False),
        "completion_submission_allowed": result.get("completion_submission_allowed", False),
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


def create_change_request_execution_plan(project_root: str) -> Dict[str, Any]:
    """
    Create execution plans for unresolved change request work orders.
    
    This provides concrete execution plans for Workflow TD and Character Director
    work orders without executing workflow changes, rebuilding references, applying
    decisions, or opening retry generation.
    
    This is a read-only execution plan creation that does NOT:
    - Execute workflow changes
    - Rebuild references
    - Apply decisions
    - Open retry gate
    - Mark production_accepted=true
    - Run ComfyUI or generation
    - Mutate role_decisions/
    - Mutate final artifacts
    - Create new generated references
    - Submit completions
    - Set execution_performed=true
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with execution plan creation result
    """
    # Load change request work orders
    work_orders = load_change_request_work_orders(project_root)
    
    # Load completion contracts
    completion_contracts = load_completion_contracts(project_root)
    
    # Load artifact index to check current state
    artifact_index = load_artifact_index(project_root)
    
    # Create output directory
    execution_plan_dir = Path(project_root) / "output" / "control" / "change_request_execution_plan"
    execution_plan_dir.mkdir(parents=True, exist_ok=True)
    
    # Create execution plans based on work orders
    execution_plans = {}
    execution_plans_created = 0
    
    if "workflow_td" in work_orders:
        plan = create_workflow_td_execution_plan(
            work_orders["workflow_td"],
            completion_contracts.get("workflow_td", {})
        )
        plan_path = execution_plan_dir / "workflow_td_identity_workflow_execution_plan.json"
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        execution_plans["workflow_td"] = plan
        execution_plans_created += 1
    
    if "character_director" in work_orders:
        plan = create_character_director_execution_plan(
            work_orders["character_director"],
            completion_contracts.get("character_director", {})
        )
        plan_path = execution_plan_dir / "character_director_reference_rebuild_execution_plan.json"
        with open(plan_path, 'w') as f:
            json.dump(plan, f, indent=2)
        execution_plans["character_director"] = plan
        execution_plans_created += 1
    
    # Create execution plan summary
    summary = create_execution_plan_summary(work_orders, execution_plans, artifact_index)
    summary_path = execution_plan_dir / "CHANGE_REQUEST_EXECUTION_PLAN.md"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    # Build result
    result = {
        "status": "completed",
        "execution_plans_created": execution_plans_created,
        "execution_performed": False,
        "completion_submission_allowed": False,
        "ready_for_resubmission": False,
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True)
    }
    
    # Update artifact index with passive pointer
    update_artifact_index_for_execution_plan(project_root, result)
    
    # Append event to episode ledger
    append_episode_ledger_event(
        project_root,
        "change_request_execution_plan_created",
        result["execution_plans_created"],
        result["execution_performed"],
        result["completion_submission_allowed"],
        result["ready_for_resubmission"],
        result["retry_gate_open"],
        result["production_accepted"],
        result["downstream_blocked"]
    )
    
    return result


def validate_change_request_execution_plan(project_root: str) -> Dict[str, Any]:
    """
    Validate that change request execution plans exist and are correctly structured.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with validation result
    """
    execution_plan_dir = Path(project_root) / "output" / "control" / "change_request_execution_plan"
    
    if not execution_plan_dir.exists():
        return {
            "status": "invalid",
            "execution_plans_found": 0,
            "validation_errors": ["Execution plan directory does not exist"]
        }
    
    execution_plans = []
    validation_errors = []
    
    # Check Workflow TD execution plan
    workflow_plan_path = execution_plan_dir / "workflow_td_identity_workflow_execution_plan.json"
    if workflow_plan_path.exists():
        with open(workflow_plan_path, 'r') as f:
            plan = json.load(f)
        
        # Validate structure
        if plan.get("plan_type") != "workflow_td_change_request_execution_plan":
            validation_errors.append("Workflow TD plan has incorrect plan_type")
        if plan.get("execution_status") != "planned":
            validation_errors.append("Workflow TD plan has execution_status != planned")
        if plan.get("execution_performed") != False:
            validation_errors.append("Workflow TD plan has execution_performed=true")
        if plan.get("completion_submission_allowed") != False:
            validation_errors.append("Workflow TD plan has completion_submission_allowed=true")
        if plan.get("retry_gate_open") != False:
            validation_errors.append("Workflow TD plan has retry_gate_open=true")
        if plan.get("production_accepted") != False:
            validation_errors.append("Workflow TD plan has production_accepted=true")
        if plan.get("downstream_blocked") != True:
            validation_errors.append("Workflow TD plan has downstream_blocked=false")
        
        execution_plans.append(plan)
    else:
        validation_errors.append("Workflow TD execution plan file does not exist")
    
    # Check Character Director execution plan
    character_plan_path = execution_plan_dir / "character_director_reference_rebuild_execution_plan.json"
    if character_plan_path.exists():
        with open(character_plan_path, 'r') as f:
            plan = json.load(f)
        
        # Validate structure
        if plan.get("plan_type") != "character_director_reference_rebuild_execution_plan":
            validation_errors.append("Character Director plan has incorrect plan_type")
        if plan.get("execution_status") != "planned":
            validation_errors.append("Character Director plan has execution_status != planned")
        if plan.get("execution_performed") != False:
            validation_errors.append("Character Director plan has execution_performed=true")
        if plan.get("completion_submission_allowed") != False:
            validation_errors.append("Character Director plan has completion_submission_allowed=true")
        if plan.get("retry_gate_open") != False:
            validation_errors.append("Character Director plan has retry_gate_open=true")
        if plan.get("production_accepted") != False:
            validation_errors.append("Character Director plan has production_accepted=true")
        if plan.get("downstream_blocked") != True:
            validation_errors.append("Character Director plan has downstream_blocked=false")
        
        execution_plans.append(plan)
    else:
        validation_errors.append("Character Director execution plan file does not exist")
    
    # Check summary
    summary_path = execution_plan_dir / "CHANGE_REQUEST_EXECUTION_PLAN.md"
    if not summary_path.exists():
        validation_errors.append("Execution plan summary file does not exist")
    
    # Load artifact index to check state
    artifact_index = load_artifact_index(project_root)
    
    # Build result
    result = {
        "status": "valid" if not validation_errors else "invalid",
        "execution_plans_found": len(execution_plans),
        "execution_performed": all(ep.get("execution_performed", False) for ep in execution_plans),
        "completion_submission_allowed": all(ep.get("completion_submission_allowed", False) for ep in execution_plans),
        "ready_for_resubmission": all(ep.get("ready_for_resubmission", False) for ep in execution_plans),
        "retry_gate_open": artifact_index.get("retry_gate_open", False),
        "production_accepted": artifact_index.get("production_accepted", False),
        "downstream_blocked": artifact_index.get("downstream_blocked", True),
        "validation_errors": validation_errors
    }
    
    return result
