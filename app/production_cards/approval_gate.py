"""
Production Role Approval Gate Module

Validates role decisions to determine if blocked shot01 may proceed to retry generation
after Character Director and Workflow TD decisions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_role_decisions(project_root: str, decisions_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Load role decision templates from project or custom decisions root.
    
    Args:
        project_root: Path to the project root
        decisions_root: Optional custom path to load decisions from (for fixture validation)
    
    Returns:
        Dictionary with character_director_decision and workflow_td_decision
    """
    if decisions_root:
        role_decisions_dir = Path(decisions_root)
    else:
        role_decisions_dir = Path(project_root) / "output" / "control" / "role_decisions"
    
    character_director_decision = {}
    workflow_td_decision = {}
    
    # Look for character director decision
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    if not char_decision_path.exists():
        # Try with .approved.json suffix for fixtures
        char_decision_path = role_decisions_dir / "character_director_identity_decision.approved.json"
    
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            character_director_decision = json.load(f)
    
    # Look for workflow TD decision
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    if not workflow_decision_path.exists():
        # Try with .approved.json suffix for fixtures
        workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.approved.json"
    
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_td_decision = json.load(f)
    
    return {
        "character_director_decision": character_director_decision,
        "workflow_td_decision": workflow_td_decision
    }


def evaluate_character_director_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate Character Director decision for approval.
    
    Character Director approval is valid only if:
    - decision_status = "decided"
    - selected_decision = "approve"
    - approved_character_identity_rules exists or is referenced
    - approved_reference_strategy exists or is referenced
    - identity_acceptance_criteria exists or is referenced
    """
    if not decision:
        return {
            "role": "Character Director",
            "approved": False,
            "reason": "decision_not_found"
        }
    
    decision_status = decision.get("decision_status")
    selected_decision = decision.get("selected_decision")
    required_artifacts = decision.get("required_artifacts", [])
    
    # Check decision status
    if decision_status != "decided":
        return {
            "role": "Character Director",
            "approved": False,
            "reason": "decision_pending",
            "current_status": decision_status
        }
    
    # Check selected decision
    if selected_decision != "approve":
        return {
            "role": "Character Director",
            "approved": False,
            "reason": "decision_not_approved",
            "selected_decision": selected_decision
        }
    
    # Check required artifacts
    missing_artifacts = []
    # Define expected artifact names for Character Director
    expected_char_artifacts = [
        "approved_character_identity_rules",
        "approved_reference_strategy",
        "identity_acceptance_criteria"
    ]
    
    if isinstance(required_artifacts, dict):
        # For dict format, check if all expected artifacts have non-empty values
        for artifact in expected_char_artifacts:
            if artifact not in required_artifacts or not required_artifacts[artifact]:
                missing_artifacts.append(artifact)
    else:
        # If it's a list, check if artifact keys exist in decision
        for artifact in required_artifacts:
            if artifact not in decision or not decision[artifact]:
                missing_artifacts.append(artifact)
    
    if missing_artifacts:
        return {
            "role": "Character Director",
            "approved": False,
            "reason": "missing_artifacts",
            "missing_artifacts": missing_artifacts
        }
    
    return {
        "role": "Character Director",
        "approved": True,
        "reason": "approved"
    }


def evaluate_workflow_td_decision(decision: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate Workflow TD decision for approval.
    
    Workflow TD approval is valid only if:
    - decision_status = "decided"
    - selected_decision = "approve_workflow"
    - current_required_generation_mode = "gorynych_identity"
    - legacy_reference_locked_allowed_for_production = false
    - workflow_audit exists or is referenced
    - required_nodes exists or is referenced
    - required_models exists or is referenced
    - preflight_result exists or is referenced
    - output_collection_contract exists or is referenced
    """
    if not decision:
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "decision_not_found"
        }
    
    decision_status = decision.get("decision_status")
    selected_decision = decision.get("selected_decision")
    generation_mode = decision.get("current_required_generation_mode")
    legacy_allowed = decision.get("legacy_reference_locked_allowed_for_production")
    required_artifacts = decision.get("required_artifacts", [])
    
    # Check decision status
    if decision_status != "decided":
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "decision_pending",
            "current_status": decision_status
        }
    
    # Check selected decision
    if selected_decision != "approve_workflow":
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "decision_not_approved",
            "selected_decision": selected_decision
        }
    
    # Check generation mode
    if generation_mode != "gorynych_identity":
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "invalid_generation_mode",
            "current_mode": generation_mode,
            "required_mode": "gorynych_identity"
        }
    
    # Check legacy reference locked
    if legacy_allowed == True:
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "legacy_reference_locked_not_allowed",
            "legacy_reference_locked_allowed_for_production": legacy_allowed
        }
    
    # Check required artifacts
    missing_artifacts = []
    # Define expected artifact names for Workflow TD
    expected_workflow_artifacts = [
        "workflow_audit",
        "required_nodes",
        "required_models",
        "preflight_result",
        "output_collection_contract"
    ]
    
    if isinstance(required_artifacts, dict):
        # For dict format, check if all expected artifacts have non-empty values
        for artifact in expected_workflow_artifacts:
            if artifact not in required_artifacts or not required_artifacts[artifact]:
                missing_artifacts.append(artifact)
    else:
        # If it's a list, check if artifact keys exist in decision
        for artifact in required_artifacts:
            if artifact not in decision or not decision[artifact]:
                missing_artifacts.append(artifact)
    
    if missing_artifacts:
        return {
            "role": "Workflow TD / ComfyUI Technical Director",
            "approved": False,
            "reason": "missing_artifacts",
            "missing_artifacts": missing_artifacts
        }
    
    return {
        "role": "Workflow TD / ComfyUI Technical Director",
        "approved": True,
        "reason": "approved"
    }


def validate_role_approval_gate(project_root: str, json_output: bool = False, decisions_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate role approval gate to determine if blocked shot may retry generation.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
        decisions_root: Optional custom path to load decisions from (for fixture validation)
    
    Returns:
        Dictionary with gate validation results
    """
    # Load role decisions
    decisions = load_role_decisions(project_root, decisions_root)
    
    char_decision = decisions.get("character_director_decision", {})
    workflow_decision = decisions.get("workflow_td_decision", {})
    
    # Evaluate both decisions
    char_evaluation = evaluate_character_director_decision(char_decision)
    workflow_evaluation = evaluate_workflow_td_decision(workflow_decision)
    
    # Determine overall gate status
    required_approvals = [
        "character_identity_approval",
        "workflow_fit_approval"
    ]
    
    missing_approvals = []
    blocking_roles = []
    
    if not char_evaluation.get("approved"):
        missing_approvals.append("character_identity_approval")
        blocking_roles.append("Character Director")
    
    if not workflow_evaluation.get("approved"):
        missing_approvals.append("workflow_fit_approval")
        blocking_roles.append("Workflow TD / ComfyUI Technical Director")
    
    # Determine gate status
    can_retry_generation = len(missing_approvals) == 0
    
    if can_retry_generation:
        status = "ready_for_retry"
        downstream_blocked = False
        next_allowed_action = "retry_generate_frames"
    else:
        status = "blocked"
        downstream_blocked = True
        next_allowed_action = None
    
    result = {
        "status": status,
        "can_retry_generation": can_retry_generation,
        "downstream_blocked": downstream_blocked,
        "production_accepted": False,  # Approval to retry does NOT mean production accepted
        "required_approvals": required_approvals,
        "missing_approvals": missing_approvals,
        "blocking_roles": blocking_roles,
        "next_allowed_action": next_allowed_action,
        "character_director_evaluation": char_evaluation,
        "workflow_td_evaluation": workflow_evaluation
    }
    
    # Add fixture_mode flag if using custom decisions_root
    if decisions_root:
        result["fixture_mode"] = True
    
    return result


def authorize_controlled_retry_generation(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Authorize controlled retry generation after role decisions are applied.
    
    This is the final authorization checkpoint before retry generation execution.
    It validates that the project is ready for controlled retry generation but
    does NOT execute generation. Requires explicit operator confirmation.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with authorization status and validation results
    """
    from app.production_cards.state_repair import inspect_real_project_decision_state
    
    # Validate role approval gate
    gate_validation = validate_role_approval_gate(project_root, json_output=True)
    
    # Inspect real project state
    project_state = inspect_real_project_decision_state(project_root)
    
    # Extract key state indicators
    role_decisions_applied = (
        project_state.get("role_decisions", {}).get("character_director", {}).get("decision_status") == "decided" and
        project_state.get("role_decisions", {}).get("workflow_td", {}).get("decision_status") == "decided"
    )
    
    # Read from artifact_index directly to get the full structure, then check for rc2_prodcards3an section
    from pathlib import Path
    from json import load as json_load
    project_path = Path(project_root)
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json_load(f)
        
        # Check for rc2_prodcards3an section which contains current retry authorization
        if "rc2_prodcards3an" in artifact_index:
            rc2_prodcards3an = artifact_index["rc2_prodcards3an"]
            retry_gate_open = rc2_prodcards3an.get("retry_gate_open", False)
            next_allowed_action = rc2_prodcards3an.get("next_allowed_action")
            production_accepted = rc2_prodcards3an.get("production_accepted", False)
            assemble_scene_allowed = rc2_prodcards3an.get("assemble_scene_allowed", False)
            downstream_blocked = rc2_prodcards3an.get("downstream_blocked", True)
        else:
            # Fallback to top-level fields
            retry_gate_open = artifact_index.get("retry_gate_open", False)
            next_allowed_action = artifact_index.get("next_allowed_action")
            production_accepted = artifact_index.get("production_accepted", False)
            downstream_blocked = artifact_index.get("downstream_blocked", True)
            assemble_scene_allowed = artifact_index.get("assemble_scene_allowed", False)
    else:
        # Fallback to inspect output
        retry_gate_open = project_state.get("artifact_index", {}).get("retry_gate_open", False)
        next_allowed_action = project_state.get("artifact_index", {}).get("next_allowed_action")
        production_accepted = project_state.get("artifact_index", {}).get("production_accepted", False)
        downstream_blocked = project_state.get("artifact_index", {}).get("downstream_blocked", True)
        assemble_scene_allowed = False
    
    approval_gate_ready = gate_validation.get("status") == "ready_for_retry"
    
    # Check no generation executed
    comfyui_generation = False
    pipeline_action_rerun = False
    most_recent_apply_event = project_state.get("episode_ledger", {}).get("most_recent_apply_event", {})
    if most_recent_apply_event:
        comfyui_generation = most_recent_apply_event.get("comfyui_generation", False)
        pipeline_action_rerun = most_recent_apply_event.get("pipeline_action_rerun", False)
    
    # Determine overall readiness for controlled retry generation
    # Note: downstream_blocked is expected during retry generation, so we don't check it
    ready_for_retry_generation = (
        role_decisions_applied and
        retry_gate_open and
        next_allowed_action == "retry_generate_frames" and
        approval_gate_ready and
        not production_accepted and
        not comfyui_generation and
        not pipeline_action_rerun
    )
    
    return {
        "status": "authorization_required",
        "ready_for_retry_generation": ready_for_retry_generation,
        "requires_operator_confirmation": True,
        "retry_gate_open": retry_gate_open,
        "next_allowed_action": next_allowed_action,
        "role_decisions_applied": role_decisions_applied,
        "approval_gate_ready": approval_gate_ready,
        "production_accepted": production_accepted,
        "generation_performed": comfyui_generation or pipeline_action_rerun,
        "downstream_actions_executed": pipeline_action_rerun,
        "no_comfyui_execution": not comfyui_generation,
        "no_frame_generation": not comfyui_generation,
        "no_downstream_action": not pipeline_action_rerun
    }
