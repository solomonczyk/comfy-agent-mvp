"""
Production Role Decision Submission Outcome Gate Module

Evaluates submitted real role decisions to determine their outcome classification
before any apply or retry generation. Distinguishes approvals from change requests.

This is a read-only evaluation that does NOT apply decisions, does NOT open retry gate,
does NOT mark production_accepted=true, does NOT run ComfyUI or generation.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_submitted_decisions(project_root: str, submission_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Load submitted role decision files from submission directory.

    Args:
        project_root: Path to the project root
        submission_root: Optional custom path to load submissions from (for fixture validation)

    Returns:
        Dictionary with character_director_submission and workflow_td_submission
    """
    if submission_root:
        submissions_dir = Path(submission_root)
    else:
        submissions_dir = Path(project_root) / "output" / "control" / "role_decision_submissions" / "submitted"

    character_director_submission = {}
    workflow_td_submission = {}

    # Look for Character Director submission
    char_submitted_path = submissions_dir / "character_director_real_decision.SUBMITTED.json"
    
    if char_submitted_path.exists():
        with open(char_submitted_path, 'r') as f:
            character_director_submission = json.load(f)

    # Look for Workflow TD submission
    workflow_submitted_path = submissions_dir / "workflow_td_real_decision.SUBMITTED.json"
    
    if workflow_submitted_path.exists():
        with open(workflow_submitted_path, 'r') as f:
            workflow_td_submission = json.load(f)

    return {
        "character_director_submission": character_director_submission,
        "workflow_td_submission": workflow_td_submission
    }


def load_artifact_index(project_root: str) -> Dict[str, Any]:
    """Load artifact index to check current project state."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            return json.load(f)
    
    return {}


def load_role_decisions(project_root: str) -> Dict[str, Any]:
    """Load role decisions to verify they remain pending (not mutated by submissions)."""
    role_decisions_dir = Path(project_root) / "output" / "control" / "role_decisions"
    
    character_director_decision = {}
    workflow_td_decision = {}
    
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            character_director_decision = json.load(f)
    
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_td_decision = json.load(f)
    
    return {
        "character_director_decision": character_director_decision,
        "workflow_td_decision": workflow_td_decision
    }


def classify_character_director_outcome(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify Character Director submitted decision outcome.

    Returns outcome classification and whether it allows apply/retry.
    
    Character Director outcomes:
    - approve: approval_ready_for_apply (if artifacts complete)
    - reject: rejected
    - request_new_reference: changes_requested
    - request_workflow_change: changes_requested
    """
    if not submission:
        return {
            "outcome": "no_submission",
            "allows_apply": False,
            "allows_retry": False
        }
    
    selected_decision = submission.get("selected_decision")
    
    if selected_decision == "approve":
        # Check if required artifacts are complete
        required_artifacts = submission.get("required_artifacts", [])
        artifacts_complete = bool(required_artifacts)
        
        return {
            "outcome": "approve",
            "allows_apply": artifacts_complete,
            "allows_retry": artifacts_complete,
            "artifacts_complete": artifacts_complete
        }
    elif selected_decision == "reject":
        return {
            "outcome": "reject",
            "allows_apply": False,
            "allows_retry": False
        }
    elif selected_decision == "request_new_reference":
        return {
            "outcome": "request_new_reference",
            "allows_apply": False,
            "allows_retry": False
        }
    elif selected_decision == "request_workflow_change":
        return {
            "outcome": "request_workflow_change",
            "allows_apply": False,
            "allows_retry": False
        }
    else:
        return {
            "outcome": f"unknown_decision_{selected_decision}",
            "allows_apply": False,
            "allows_retry": False
        }


def classify_workflow_td_outcome(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Classify Workflow TD submitted decision outcome.

    Returns outcome classification and whether it allows apply/retry.
    
    Workflow TD outcomes:
    - approve_workflow: approval_ready_for_apply (if artifacts complete)
    - reject_workflow: rejected
    - request_missing_nodes: changes_requested
    - request_missing_models: changes_requested
    - request_reference_rebuild: changes_requested
    """
    if not submission:
        return {
            "outcome": "no_submission",
            "allows_apply": False,
            "allows_retry": False
        }
    
    selected_decision = submission.get("selected_decision")
    
    if selected_decision == "approve_workflow":
        # Check if required artifacts are complete
        required_artifacts = submission.get("required_artifacts", [])
        artifacts_complete = bool(required_artifacts)
        
        return {
            "outcome": "approve_workflow",
            "allows_apply": artifacts_complete,
            "allows_retry": artifacts_complete,
            "artifacts_complete": artifacts_complete
        }
    elif selected_decision == "reject_workflow":
        return {
            "outcome": "reject_workflow",
            "allows_apply": False,
            "allows_retry": False
        }
    elif selected_decision == "request_missing_nodes":
        return {
            "outcome": "request_missing_nodes",
            "allows_apply": False,
            "allows_retry": False
        }
    elif selected_decision == "request_missing_models":
        return {
            "outcome": "request_missing_models",
            "allows_apply": False,
            "allows_retry": False
        }
    elif selected_decision == "request_reference_rebuild":
        return {
            "outcome": "request_reference_rebuild",
            "allows_apply": False,
            "allows_retry": False
        }
    else:
        return {
            "outcome": f"unknown_decision_{selected_decision}",
            "allows_apply": False,
            "allows_retry": False
        }


def determine_next_required_role_actions(
    char_outcome: Dict[str, Any],
    workflow_outcome: Dict[str, Any]
) -> List[Dict[str, str]]:
    """
    Determine next required role actions based on submitted decision outcomes.
    
    Returns list of {role, action} tuples for follow-up work.
    """
    actions = []
    
    char_decision = char_outcome.get("outcome", "")
    workflow_decision = workflow_outcome.get("outcome", "")
    
    # Character Director actions
    if char_decision == "request_workflow_change":
        actions.append({
            "role": "Character Director",
            "action": "review_updated_identity_strategy_after_workflow_change"
        })
    elif char_decision == "request_new_reference":
        actions.append({
            "role": "Character Director",
            "action": "provide_new_character_reference"
        })
    elif char_decision == "reject":
        actions.append({
            "role": "Character Director",
            "action": "provide_rejection_reasoning_and_alternative"
        })
    
    # Workflow TD actions
    if workflow_decision == "request_reference_rebuild":
        actions.append({
            "role": "Workflow TD / ComfyUI Technical Director",
            "action": "rebuild_or_update_identity_workflow_reference_strategy"
        })
    elif workflow_decision == "request_missing_nodes":
        actions.append({
            "role": "Workflow TD / ComfyUI Technical Director",
            "action": "provide_or_install_missing_comfyui_nodes"
        })
    elif workflow_decision == "request_missing_models":
        actions.append({
            "role": "Workflow TD / ComfyUI Technical Director",
            "action": "provide_or_install_missing_models"
        })
    elif workflow_decision == "reject_workflow":
        actions.append({
            "role": "Workflow TD / ComfyUI Technical Director",
            "action": "provide_workflow_rejection_reasoning_and_alternative"
        })
    
    return actions


def validate_submission_safety(submission: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    """
    Validate submission for safety before outcome evaluation.
    
    Rejects if:
    - fixture_only=true
    - production_accepted=true
    - selected_decision missing
    - selected_decision outside allowed decisions
    """
    result = {
        "valid": True,
        "rejection_reasons": []
    }
    
    if not submission:
        result["valid"] = False
        result["rejection_reasons"].append("submission_not_found")
        return result
    
    # Reject fixture_only=true
    if submission.get("fixture_only"):
        result["valid"] = False
        result["rejection_reasons"].append("fixture_only_true_rejected")
    
    # Reject production_accepted=true
    if submission.get("production_accepted"):
        result["valid"] = False
        result["rejection_reasons"].append("production_accepted_true_rejected")
    
    # Check selected_decision
    selected_decision = submission.get("selected_decision")
    if selected_decision is None:
        result["valid"] = False
        result["rejection_reasons"].append("selected_decision_null")
    else:
        # Check if decision is in allowed list
        allowed_decisions = submission.get("allowed_decisions", [])
        if selected_decision not in allowed_decisions:
            result["valid"] = False
            result["rejection_reasons"].append(f"selected_decision_not_allowed: {selected_decision}")
    
    return result


def validate_workflow_td_specific_safety(submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate Workflow TD specific safety constraints.
    
    Rejects if:
    - legacy_reference_locked_allowed_for_production=true
    - generation_mode is not gorynych_identity
    """
    result = {
        "valid": True,
        "rejection_reasons": []
    }
    
    if not submission:
        result["valid"] = False
        result["rejection_reasons"].append("submission_not_found")
        return result
    
    # Reject legacy_reference_locked_allowed_for_production=true
    if submission.get("legacy_reference_locked_allowed_for_production"):
        result["valid"] = False
        result["rejection_reasons"].append("legacy_reference_locked_true_rejected")
    
    # Reject non-gorynych mode
    generation_mode = submission.get("current_required_generation_mode")
    if generation_mode != "gorynych_identity":
        result["valid"] = False
        result["rejection_reasons"].append(f"generation_mode_not_gorynych: {generation_mode}")
    
    return result


def verify_no_mutation_occurred(
    project_root: str,
    artifact_index: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Verify that no mutation occurred to critical project state by submissions.
    
    Checks:
    - role_decisions remain pending
    - retry_gate_open remains false
    - production_accepted remains false
    - downstream_blocked remains true
    """
    result = {
        "mutations_detected": False,
        "mutation_details": []
    }
    
    # Check artifact index state
    if artifact_index.get("retry_gate_open"):
        result["mutations_detected"] = True
        result["mutation_details"].append("retry_gate_open_is_true")
    
    if artifact_index.get("production_accepted"):
        result["mutations_detected"] = True
        result["mutation_details"].append("production_accepted_is_true")
    
    if not artifact_index.get("downstream_blocked", True):
        result["mutations_detected"] = True
        result["mutation_details"].append("downstream_blocked_is_false")
    
    # Check role_decisions remain pending
    role_decisions = load_role_decisions(project_root)
    
    char_decision = role_decisions.get("character_director_decision", {})
    if char_decision.get("decision_status") != "pending":
        result["mutations_detected"] = True
        result["mutation_details"].append(f"character_director_decision_status_is_{char_decision.get('decision_status')}")
    
    workflow_decision = role_decisions.get("workflow_td_decision", {})
    if workflow_decision.get("decision_status") != "pending":
        result["mutations_detected"] = True
        result["mutation_details"].append(f"workflow_td_decision_status_is_{workflow_decision.get('decision_status')}")
    
    return result


def update_artifact_index_for_outcome(
    project_root: str,
    outcome_result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with outcome evaluation (passive pointer only).
    
    This records the outcome evaluation without opening retry or applying decisions.
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add role_decision_outcome section as passive pointer
    artifact_index["role_decision_outcome"] = {
        "status": outcome_result.get("status"),
        "ready_for_apply": outcome_result.get("ready_for_apply"),
        "retry_gate_open": outcome_result.get("retry_gate_open"),
        "production_accepted": outcome_result.get("production_accepted"),
        "downstream_blocked": outcome_result.get("downstream_blocked"),
        "character_director_outcome": outcome_result.get("character_director_outcome"),
        "workflow_td_outcome": outcome_result.get("workflow_td_outcome"),
        "evaluated_at": datetime.utcnow().isoformat() + "Z"
    }
    
    # Ensure critical state remains unchanged
    artifact_index["downstream_blocked"] = outcome_result.get("downstream_blocked", True)
    artifact_index["production_accepted"] = outcome_result.get("production_accepted", False)
    artifact_index["retry_gate_open"] = outcome_result.get("retry_gate_open", False)
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def evaluate_submitted_decision_outcome(
    project_root: str,
    submission_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Evaluate submitted role decision outcomes to classify approvals vs change requests.
    
    This is a read-only evaluation that does NOT:
    - Apply decisions
    - Open retry gate
    - Mark production_accepted=true
    - Run ComfyUI or generation
    - Mutate role_decisions/
    - Mutate final artifacts
    
    For current non-approval submissions (request_workflow_change, request_reference_rebuild):
    - Returns status="changes_requested"
    - ready_for_apply=false
    - can_retry_generation=false
    - retry_gate_open=false
    - production_accepted=false
    - downstream_blocked=true
    
    For temp approval submissions (approve, approve_workflow with complete artifacts):
    - Returns status="approval_ready_for_apply"
    - ready_for_apply=true
    - can_retry_generation_after_apply=true
    - next_allowed_action_if_applied="retry_generate_frames"
    - production_accepted_after_apply=false
    - Still does NOT apply anything
    
    Rejects if:
    - submitted decisions invalid
    - selected_decision missing
    - selected_decision outside allowed decisions
    - production_accepted=true
    - fixture_only=true
    - Workflow TD legacy_reference_locked_allowed_for_production=true
    - Workflow TD generation mode is not gorynych_identity
    
    Args:
        project_root: Path to the project root
        submission_root: Optional custom path to load submissions from (for fixture validation)
    
    Returns:
        Dictionary with outcome evaluation result
    """
    project_path = Path(project_root)
    project_id = project_path.name
    
    # Load submissions
    submissions = load_submitted_decisions(project_root, submission_root)
    char_submission = submissions["character_director_submission"]
    workflow_submission = submissions["workflow_td_submission"]
    
    # Load current project state
    artifact_index = load_artifact_index(project_root)
    
    # Validate safety constraints
    char_safety = validate_submission_safety(char_submission, project_id)
    workflow_safety = validate_submission_safety(workflow_submission, project_id)
    workflow_specific_safety = validate_workflow_td_specific_safety(workflow_submission)
    
    # Collect all rejection reasons
    all_rejection_reasons = []
    all_rejection_reasons.extend([f"character_director: {r}" for r in char_safety["rejection_reasons"]])
    all_rejection_reasons.extend([f"workflow_td: {r}" for r in workflow_safety["rejection_reasons"]])
    all_rejection_reasons.extend([f"workflow_td_specific: {r}" for r in workflow_specific_safety["rejection_reasons"]])
    
    # If any safety check failed, reject
    if all_rejection_reasons:
        return {
            "status": "rejected",
            "submitted_decisions_valid": False,
            "ready_for_apply": False,
            "can_retry_generation": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True,
            "rejection_reasons": all_rejection_reasons,
            "apply_performed": False,
            "real_project_mutated": False
        }
    
    # Classify outcomes
    char_outcome = classify_character_director_outcome(char_submission)
    workflow_outcome = classify_workflow_td_outcome(workflow_submission)
    
    # Determine next required actions
    next_actions = determine_next_required_role_actions(char_outcome, workflow_outcome)
    
    # Check if both are approvals with complete artifacts
    both_approvals = (
        char_outcome["outcome"] == "approve" and
        workflow_outcome["outcome"] == "approve_workflow" and
        char_outcome.get("artifacts_complete", False) and
        workflow_outcome.get("artifacts_complete", False)
    )
    
    # Determine overall status
    if both_approvals:
        status = "approval_ready_for_apply"
        ready_for_apply = True
        can_retry_generation = False  # Only after apply
    else:
        status = "changes_requested"
        ready_for_apply = False
        can_retry_generation = False
    
    # Verify no mutation occurred
    mutation_check = verify_no_mutation_occurred(project_root, artifact_index)
    
    # Build result
    result = {
        "status": status,
        "submitted_decisions_valid": True,
        "ready_for_apply": ready_for_apply,
        "can_retry_generation": can_retry_generation,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "character_director_outcome": char_outcome["outcome"],
        "workflow_td_outcome": workflow_outcome["outcome"],
        "next_required_actions": next_actions,
        "apply_performed": False,
        "real_project_mutated": mutation_check["mutations_detected"],
        "mutation_details": mutation_check["mutation_details"]
    }
    
    # Add approval-specific fields if applicable
    if both_approvals:
        result["can_retry_generation_after_apply"] = True
        result["next_allowed_action_if_applied"] = "retry_generate_frames"
        result["production_accepted_after_apply"] = False
    
    # Update artifact index with outcome (passive pointer only)
    update_artifact_index_for_outcome(project_root, result)
    
    return result
