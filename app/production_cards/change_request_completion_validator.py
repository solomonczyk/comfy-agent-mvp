"""
Production Change Request Completion Validator Module

Validates submitted change request completion files before they are allowed
to trigger resubmission of role decisions, without executing workflow changes,
rebuilding references, applying decisions, or opening retry generation.

This is a read-only validation that does NOT:
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


def load_submitted_completions(project_root: str, completion_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Load submitted change request completion files.

    Supports both .COMPLETION_TEMPLATE.json (templates) and .SUBMITTED.json (completed).

    Args:
        project_root: Path to the project root
        completion_root: Optional custom path to load completions from (for fixture validation)

    Returns:
        Dictionary with workflow_completion and character_completion
    """
    if completion_root:
        completions_dir = Path(completion_root)
    else:
        completions_dir = Path(project_root) / "output" / "control" / "change_request_completions"

    workflow_completion = {}
    character_completion = {}

    # Look for Workflow TD completion (prefer .SUBMITTED.json, fall back to .COMPLETION_TEMPLATE.json)
    workflow_submitted_path = completions_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    workflow_template_path = completions_dir / "workflow_td_identity_workflow_change.COMPLETION_TEMPLATE.json"
    
    if workflow_submitted_path.exists():
        with open(workflow_submitted_path, 'r') as f:
            workflow_completion = json.load(f)
    elif workflow_template_path.exists():
        with open(workflow_template_path, 'r') as f:
            workflow_completion = json.load(f)

    # Look for Character Director completion (prefer .SUBMITTED.json, fall back to .COMPLETION_TEMPLATE.json)
    character_submitted_path = completions_dir / "character_director_reference_rebuild.SUBMITTED.json"
    character_template_path = completions_dir / "character_director_reference_rebuild.COMPLETION_TEMPLATE.json"
    
    if character_submitted_path.exists():
        with open(character_submitted_path, 'r') as f:
            character_completion = json.load(f)
    elif character_template_path.exists():
        with open(character_template_path, 'r') as f:
            character_completion = json.load(f)

    return {
        "workflow_completion": workflow_completion,
        "character_completion": character_completion
    }


def load_artifact_index(project_root: str) -> Dict[str, Any]:
    """Load artifact index to check current project state."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            return json.load(f)
    
    return {}


def validate_workflow_td_completion_submission(
    completion: Dict[str, Any],
    work_order: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate Workflow TD completion submission for safety and completeness.

    Rejects if:
    - completion_status != submitted
    - selected_resolution is null
    - selected_resolution not in allowed_resolutions
    - required outputs are missing
    - production_accepted=true
    - retry_gate_open=true
    - apply_performed=true
    - legacy_reference_locked_allowed_for_production=true
    - current_required_generation_mode != gorynych_identity
    - execution_performed=true without required output evidence
    - source_work_order mismatch
    - role mismatch
    - blocked_shot mismatch

    Args:
        completion: Workflow TD completion data
        work_order: Workflow TD work order data

    Returns:
        Validation result dict with valid flag and rejection reasons
    """
    result = {
        "role": "Workflow TD / ComfyUI Technical Director",
        "valid": False,
        "rejection_reasons": [],
        "is_complete": False
    }

    if not completion:
        result["rejection_reasons"].append("completion_not_found")
        return result

    # Reject completion_status != submitted
    completion_status = completion.get("completion_status")
    if completion_status != "submitted":
        result["rejection_reasons"].append(f"completion_status_not_submitted: {completion_status}")
        result["is_complete"] = False
        return result

    result["is_complete"] = True

    # Check selected_resolution
    selected_resolution = completion.get("selected_resolution")
    if selected_resolution is None:
        result["rejection_reasons"].append("selected_resolution_null")
        result["is_complete"] = False
    else:
        allowed_resolutions = completion.get("allowed_resolutions", [])
        if selected_resolution not in allowed_resolutions:
            result["rejection_reasons"].append(f"selected_resolution_not_allowed: {selected_resolution}")

    # Check required outputs
    required_outputs = completion.get("required_outputs", [])
    outputs_provided = completion.get("outputs_provided", {})
    missing_outputs = []
    for output in required_outputs:
        if output not in outputs_provided or not outputs_provided[output]:
            missing_outputs.append(output)
    if missing_outputs:
        result["rejection_reasons"].append(f"missing_required_outputs: {missing_outputs}")

    # Reject production_accepted=true
    if completion.get("production_accepted"):
        result["rejection_reasons"].append("production_accepted_true_rejected")

    # Reject retry_gate_open=true
    if completion.get("retry_gate_open"):
        result["rejection_reasons"].append("retry_gate_open_true_rejected")

    # Reject apply_performed=true
    if completion.get("apply_performed"):
        result["rejection_reasons"].append("apply_performed_true_rejected")

    # Reject legacy_reference_locked_allowed_for_production=true
    if completion.get("legacy_reference_locked_allowed_for_production"):
        result["rejection_reasons"].append("legacy_reference_locked_true_rejected")

    # Reject non-gorynych mode
    generation_mode = completion.get("current_required_generation_mode")
    if generation_mode != "gorynych_identity":
        result["rejection_reasons"].append(f"generation_mode_not_gorynych: {generation_mode}")

    # Check execution_performed evidence
    if completion.get("execution_performed"):
        # If execution_performed=true, required outputs must have evidence
        if missing_outputs:
            result["rejection_reasons"].append("execution_performed_true_without_output_evidence")

    # Check source_work_order match
    source_work_order = completion.get("source_work_order")
    expected_source = "workflow_td_identity_workflow_change_order.json"
    if source_work_order != expected_source:
        result["rejection_reasons"].append(f"source_work_order_mismatch: expected {expected_source}")

    # Check role match
    role = completion.get("role")
    expected_role = "Workflow TD / ComfyUI Technical Director"
    if role != expected_role:
        result["rejection_reasons"].append(f"role_mismatch: expected {expected_role}")

    # Check blocked_shot match against work order
    blocked_shot = completion.get("blocked_shot")
    expected_shot = work_order.get("blocked_shot", "shot01")
    if blocked_shot != expected_shot:
        result["rejection_reasons"].append(f"blocked_shot_mismatch: expected {expected_shot}")

    # Determine validity
    result["valid"] = len(result["rejection_reasons"]) == 0

    return result


def validate_character_director_completion_submission(
    completion: Dict[str, Any],
    work_order: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Validate Character Director completion submission for safety and completeness.

    Rejects if:
    - completion_status != submitted
    - selected_resolution is null
    - selected_resolution not in allowed_resolutions
    - required outputs are missing
    - production_accepted=true
    - retry_gate_open=true
    - apply_performed=true
    - execution_performed=true without required output evidence
    - source_work_order mismatch
    - role mismatch
    - blocked_shot mismatch

    Args:
        completion: Character Director completion data
        work_order: Character Director work order data

    Returns:
        Validation result dict with valid flag and rejection reasons
    """
    result = {
        "role": "Character Director",
        "valid": False,
        "rejection_reasons": [],
        "is_complete": False
    }

    if not completion:
        result["rejection_reasons"].append("completion_not_found")
        return result

    # Reject completion_status != submitted
    completion_status = completion.get("completion_status")
    if completion_status != "submitted":
        result["rejection_reasons"].append(f"completion_status_not_submitted: {completion_status}")
        result["is_complete"] = False
        return result

    result["is_complete"] = True

    # Check selected_resolution
    selected_resolution = completion.get("selected_resolution")
    if selected_resolution is None:
        result["rejection_reasons"].append("selected_resolution_null")
        result["is_complete"] = False
    else:
        allowed_resolutions = completion.get("allowed_resolutions", [])
        if selected_resolution not in allowed_resolutions:
            result["rejection_reasons"].append(f"selected_resolution_not_allowed: {selected_resolution}")

    # Check required outputs
    required_outputs = completion.get("required_outputs", [])
    outputs_provided = completion.get("outputs_provided", {})
    missing_outputs = []
    for output in required_outputs:
        if output not in outputs_provided or not outputs_provided[output]:
            missing_outputs.append(output)
    if missing_outputs:
        result["rejection_reasons"].append(f"missing_required_outputs: {missing_outputs}")

    # Reject production_accepted=true
    if completion.get("production_accepted"):
        result["rejection_reasons"].append("production_accepted_true_rejected")

    # Reject retry_gate_open=true
    if completion.get("retry_gate_open"):
        result["rejection_reasons"].append("retry_gate_open_true_rejected")

    # Reject apply_performed=true
    if completion.get("apply_performed"):
        result["rejection_reasons"].append("apply_performed_true_rejected")

    # Check execution_performed evidence
    if completion.get("execution_performed"):
        # If execution_performed=true, required outputs must have evidence
        if missing_outputs:
            result["rejection_reasons"].append("execution_performed_true_without_output_evidence")

    # Check source_work_order match
    source_work_order = completion.get("source_work_order")
    expected_source = "character_director_reference_rebuild_order.json"
    if source_work_order != expected_source:
        result["rejection_reasons"].append(f"source_work_order_mismatch: expected {expected_source}")

    # Check role match
    role = completion.get("role")
    expected_role = "Character Director"
    if role != expected_role:
        result["rejection_reasons"].append(f"role_mismatch: expected {expected_role}")

    # Check blocked_shot match against work order
    blocked_shot = completion.get("blocked_shot")
    expected_shot = work_order.get("blocked_shot", "shot01")
    if blocked_shot != expected_shot:
        result["rejection_reasons"].append(f"blocked_shot_mismatch: expected {expected_shot}")

    # Determine validity
    result["valid"] = len(result["rejection_reasons"]) == 0

    return result


def compare_completion_against_contract(completion: Dict[str, Any], work_order: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare completion against the original work order contract to detect tampering.

    Args:
        completion: Completion data to validate
        work_order: Original work order contract

    Returns:
        Comparison result with contract_compliance flag
    """
    # Compare critical fields
    critical_fields = [
        "role",
        "blocked_shot",
        "required_generation_mode"
    ]

    mismatches = []
    for field in critical_fields:
        if completion.get(field) != work_order.get(field):
            mismatches.append(f"{field}_mismatch")

    return {
        "contract_compliant": len(mismatches) == 0,
        "mismatches": mismatches
    }


def validate_submitted_change_request_completions(
    project_root: str,
    completion_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Validate submitted change request completions and determine if ready for resubmission.

    This is a read-only validation that does NOT mutate the project.

    For blank templates (completion_status=template):
    - Returns status="awaiting_completion_input"
    - submitted_completions_ready=false
    - retry_gate_open=false
    - production_accepted=false
    - downstream_blocked=true

    For completed submitted completions:
    - Returns status="valid"
    - submitted_completions_ready=true
    - would_allow_new_role_decision_drafts=true
    - execution_performed=true
    - retry_gate_open=false
    - production_accepted=false
    - downstream_blocked=true
    - real_project_mutated=false

    Args:
        project_root: Path to the project root
        completion_root: Optional custom path to load completions from (for fixture validation)

    Returns:
        Dictionary with validation results
    """
    # Load work orders
    work_orders = load_change_request_work_orders(project_root)

    # Load completions
    completions = load_submitted_completions(project_root, completion_root)
    workflow_completion = completions["workflow_completion"]
    character_completion = completions["character_completion"]

    # Load artifact index to check current state
    artifact_index = load_artifact_index(project_root)

    # Validate each completion against its work order
    workflow_validation = validate_workflow_td_completion_submission(
        workflow_completion,
        work_orders.get("workflow_td", {})
    )
    character_validation = validate_character_director_completion_submission(
        character_completion,
        work_orders.get("character_director", {})
    )

    # Count valid and complete completions
    valid_completions = 0
    complete_completions = 0
    all_rejection_reasons = []

    if workflow_validation["valid"]:
        valid_completions += 1
    if workflow_validation["is_complete"]:
        complete_completions += 1
    all_rejection_reasons.extend([f"workflow_td: {r}" for r in workflow_validation["rejection_reasons"]])

    if character_validation["valid"]:
        valid_completions += 1
    if character_validation["is_complete"]:
        complete_completions += 1
    all_rejection_reasons.extend([f"character_director: {r}" for r in character_validation["rejection_reasons"]])

    # Determine overall status
    if complete_completions == 0:
        # Both completions are blank (completion_status=template)
        status = "awaiting_completion_input"
        submitted_completions_ready = False
        would_allow_new_role_decision_drafts = False
        execution_performed = False
    elif valid_completions == 2:
        # Both completions are valid and complete
        status = "valid"
        submitted_completions_ready = True
        would_allow_new_role_decision_drafts = True
        execution_performed = True
    else:
        # Some completions are invalid or incomplete
        status = "invalid"
        submitted_completions_ready = False
        would_allow_new_role_decision_drafts = False
        execution_performed = False

    # Build result
    result = {
        "status": status,
        "submitted_completions_ready": submitted_completions_ready,
        "valid_completions": valid_completions,
        "complete_completions": complete_completions,
        "missing_or_incomplete_completions": [],
        "rejection_reasons": all_rejection_reasons,
        "ready_for_resubmission": submitted_completions_ready,
        "execution_performed": execution_performed,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True
    }

    # Add missing/incomplete completions list
    if not workflow_completion:
        result["missing_or_incomplete_completions"].append("workflow_change_completion")
    elif not workflow_validation["is_complete"]:
        result["missing_or_incomplete_completions"].append("workflow_change_completion")

    if not character_completion:
        result["missing_or_incomplete_completions"].append("reference_rebuild_completion")
    elif not character_validation["is_complete"]:
        result["missing_or_incomplete_completions"].append("reference_rebuild_completion")

    # Add what-if analysis for valid completions
    if status == "valid":
        result["would_allow_new_role_decision_drafts"] = True
        result["retry_gate_open"] = False
        result["production_accepted"] = False
        result["downstream_blocked"] = True
        result["real_project_mutated"] = False

    return result
