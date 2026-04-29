"""
Production Role Decision Intake Module

Validates role decision files in dry-run mode before applying them to the real project.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.production_cards.approval_gate import (
    load_role_decisions,
    evaluate_character_director_decision,
    evaluate_workflow_td_decision
)


def load_intake_decisions(decisions_root: str) -> Dict[str, Any]:
    """
    Load role decision files from intake directory for validation.
    
    Supports both standard intake decision files and resubmitted decision files
    with embedded artifacts in completion_evidence.
    
    Args:
        decisions_root: Path to directory containing decision files
    
    Returns:
        Dictionary with character_director_decision and workflow_td_decision
    """
    decisions_dir = Path(decisions_root).resolve()
    
    character_director_decision = {}
    workflow_td_decision = {}
    
    # Try standard intake decision files first
    for filename in ["character_director_identity_decision.json", "character_director_identity_decision.approved.json"]:
        char_decision_path = decisions_dir / filename
        if char_decision_path.exists():
            with open(char_decision_path, 'r') as f:
                character_director_decision = json.load(f)
            break
    
    for filename in ["workflow_td_identity_workflow_decision.json", "workflow_td_identity_workflow_decision.approved.json"]:
        workflow_decision_path = decisions_dir / filename
        if workflow_decision_path.exists():
            with open(workflow_decision_path, 'r') as f:
                workflow_td_decision = json.load(f)
            break
    
    # If standard files not found, try resubmitted decision files with embedded artifacts
    if not character_director_decision:
        for filename in ["character_director_real_decision.SUBMITTED.json", "character_director_resubmitted_decision.SUBMITTED.json"]:
            char_decision_path = decisions_dir / filename
            if char_decision_path.exists():
                with open(char_decision_path, 'r') as f:
                    character_director_decision = json.load(f)
                # Extract embedded artifacts from completion_evidence
                if "completion_evidence" in character_director_decision:
                    character_director_decision["required_artifacts"] = character_director_decision["completion_evidence"]
                break
    
    if not workflow_td_decision:
        for filename in ["workflow_td_real_decision.SUBMITTED.json", "workflow_td_resubmitted_decision.SUBMITTED.json"]:
            workflow_decision_path = decisions_dir / filename
            if workflow_decision_path.exists():
                with open(workflow_decision_path, 'r') as f:
                    workflow_td_decision = json.load(f)
                # Extract embedded artifacts from completion_evidence
                if "completion_evidence" in workflow_td_decision:
                    workflow_td_decision["required_artifacts"] = workflow_td_decision["completion_evidence"]
                break
    
    return {
        "character_director_decision": character_director_decision,
        "workflow_td_decision": workflow_td_decision
    }


def compare_against_pending_decisions(project_root: str, decisions_root: str) -> Dict[str, Any]:
    """
    Compare intake decisions against pending decisions in real project.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
    
    Returns:
        Dictionary with comparison results
    """
    intake_decisions = load_intake_decisions(decisions_root)
    real_decisions = load_role_decisions(project_root)
    
    comparison = {
        "intake_decisions_found": [],
        "real_decisions_pending": [],
        "comparison": {}
    }
    
    # Check Character Director
    char_intake = intake_decisions.get("character_director_decision", {})
    char_real = real_decisions.get("character_director_decision", {})
    
    if char_intake:
        comparison["intake_decisions_found"].append("character_director")
        comparison["comparison"]["character_director"] = {
            "intake_status": char_intake.get("decision_status"),
            "real_status": char_real.get("decision_status"),
            "intake_decision": char_intake.get("selected_decision"),
            "real_decision": char_real.get("selected_decision")
        }
    
    if char_real and char_real.get("decision_status") == "pending":
        comparison["real_decisions_pending"].append("character_director")
    
    # Check Workflow TD
    workflow_intake = intake_decisions.get("workflow_td_decision", {})
    workflow_real = real_decisions.get("workflow_td_decision", {})
    
    if workflow_intake:
        comparison["intake_decisions_found"].append("workflow_td")
        comparison["comparison"]["workflow_td"] = {
            "intake_status": workflow_intake.get("decision_status"),
            "real_status": workflow_real.get("decision_status"),
            "intake_decision": workflow_intake.get("selected_decision"),
            "real_decision": workflow_real.get("selected_decision")
        }
    
    if workflow_real and workflow_real.get("decision_status") == "pending":
        comparison["real_decisions_pending"].append("workflow_td")
    
    return comparison


def verify_required_approval_artifacts(decisions_root: str) -> Dict[str, Any]:
    """
    Verify that intake decisions have all required approval artifacts.
    
    Supports both standard artifact names and resubmission completion_evidence naming.
    
    Args:
        decisions_root: Path to directory containing intake decision files
    
    Returns:
        Dictionary with artifact verification results
    """
    intake_decisions = load_intake_decisions(decisions_root)
    
    verification = {
        "character_director_artifacts": {"valid": True, "missing": []},
        "workflow_td_artifacts": {"valid": True, "missing": []}
    }
    
    # Verify Character Director artifacts
    char_decision = intake_decisions.get("character_director_decision", {})
    expected_char_artifacts = [
        "approved_character_identity_rules",
        "approved_reference_strategy",
        "identity_acceptance_criteria"
    ]
    
    # Also support resubmission naming convention
    resubmission_char_artifacts = [
        "updated_character_identity_rules",
        "updated_reference_strategy",
        "identity_acceptance_criteria"
    ]
    
    required_artifacts = char_decision.get("required_artifacts", {})
    if isinstance(required_artifacts, dict):
        for artifact in expected_char_artifacts:
            if artifact not in required_artifacts or not required_artifacts[artifact]:
                # Check resubmission naming convention
                resubmission_idx = expected_char_artifacts.index(artifact)
                resubmission_name = resubmission_char_artifacts[resubmission_idx]
                if resubmission_name in required_artifacts and required_artifacts[resubmission_name]:
                    continue  # Found in resubmission format
                verification["character_director_artifacts"]["valid"] = False
                verification["character_director_artifacts"]["missing"].append(artifact)
    else:
        verification["character_director_artifacts"]["valid"] = False
        verification["character_director_artifacts"]["missing"].extend(expected_char_artifacts)
    
    # Verify Workflow TD artifacts
    workflow_decision = intake_decisions.get("workflow_td_decision", {})
    expected_workflow_artifacts = [
        "workflow_audit",
        "required_nodes",
        "required_models",
        "preflight_result",
        "output_collection_contract"
    ]
    
    # Also support resubmission naming convention
    resubmission_workflow_artifacts = [
        "workflow_audit",
        "required_nodes",
        "required_models",
        "preflight_result",
        "output_collection_contract"
    ]
    
    required_artifacts = workflow_decision.get("required_artifacts", {})
    if isinstance(required_artifacts, dict):
        for artifact in expected_workflow_artifacts:
            if artifact not in required_artifacts or not required_artifacts[artifact]:
                verification["workflow_td_artifacts"]["valid"] = False
                verification["workflow_td_artifacts"]["missing"].append(artifact)
    else:
        verification["workflow_td_artifacts"]["valid"] = False
        verification["workflow_td_artifacts"]["missing"].extend(expected_workflow_artifacts)
    
    return verification


def validate_decision_intake(project_root: str, decisions_root: str) -> Dict[str, Any]:
    """
    Validate role decision intake in dry-run mode.
    
    This function validates decision files before applying them to the real project.
    It never writes to the real project - it only validates and reports what would happen.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
    
    Returns:
        Dictionary with dry-run validation results
    """
    # Load intake decisions
    intake_decisions = load_intake_decisions(decisions_root)
    
    # Compare against pending decisions
    comparison = compare_against_pending_decisions(project_root, decisions_root)
    
    # Verify required artifacts
    artifact_verification = verify_required_approval_artifacts(decisions_root)
    
    # Evaluate both decisions using existing approval gate logic
    # For resubmitted decisions with decision_status="submitted", treat as decided for dry-run
    char_decision = intake_decisions.get("character_director_decision", {})
    if char_decision.get("decision_status") == "submitted":
        # Create a copy with decision_status="decided" for evaluation compatibility
        char_decision_eval = char_decision.copy()
        char_decision_eval["decision_status"] = "decided"
        # Normalize artifact names from resubmission format to standard format
        if "required_artifacts" in char_decision_eval and isinstance(char_decision_eval["required_artifacts"], dict):
            artifacts = char_decision_eval["required_artifacts"]
            if "updated_character_identity_rules" in artifacts:
                artifacts["approved_character_identity_rules"] = artifacts["updated_character_identity_rules"]
            if "updated_reference_strategy" in artifacts:
                artifacts["approved_reference_strategy"] = artifacts["updated_reference_strategy"]
        char_evaluation = evaluate_character_director_decision(char_decision_eval)
    else:
        char_evaluation = evaluate_character_director_decision(char_decision)
    
    workflow_decision = intake_decisions.get("workflow_td_decision", {})
    if workflow_decision.get("decision_status") == "submitted":
        # Create a copy with decision_status="decided" for evaluation compatibility
        workflow_decision_eval = workflow_decision.copy()
        workflow_decision_eval["decision_status"] = "decided"
        workflow_evaluation = evaluate_workflow_td_decision(workflow_decision_eval)
    else:
        workflow_evaluation = evaluate_workflow_td_decision(workflow_decision)
    
    # Determine overall validity
    errors = []
    missing_decisions = []
    
    # Check for missing decisions
    if not intake_decisions.get("character_director_decision"):
        missing_decisions.append("character_director")
        errors.append("Character Director decision file not found")
    
    if not intake_decisions.get("workflow_td_decision"):
        missing_decisions.append("workflow_td")
        errors.append("Workflow TD decision file not found")
    
    # Check for artifact issues
    if not artifact_verification["character_director_artifacts"]["valid"]:
        errors.append(
            f"Character Director missing artifacts: {artifact_verification['character_director_artifacts']['missing']}"
        )
    
    if not artifact_verification["workflow_td_artifacts"]["valid"]:
        errors.append(
            f"Workflow TD missing artifacts: {artifact_verification['workflow_td_artifacts']['missing']}"
        )
    
    # Check for approval validity
    if char_evaluation.get("reason") != "approved":
        errors.append(f"Character Director decision not approved: {char_evaluation.get('reason')}")
    
    if workflow_evaluation.get("reason") != "approved":
        errors.append(f"Workflow TD decision not approved: {workflow_evaluation.get('reason')}")
    
    # Determine if retry generation would be allowed if applied
    would_allow_retry_generation = (
        char_evaluation.get("approved", False) and 
        workflow_evaluation.get("approved", False)
    )
    
    # Determine status
    if errors or missing_decisions:
        status = "invalid"
    else:
        status = "valid"
    
    # Build result
    result = {
        "status": status,
        "dry_run": True,
        "would_allow_retry_generation": would_allow_retry_generation,
        "would_apply_decisions": len(comparison["intake_decisions_found"]),
        "next_allowed_action_if_applied": "retry_generate_frames" if would_allow_retry_generation else None,
        "production_accepted_after_apply": False,  # Approval to retry does NOT mean production accepted
        "real_project_mutated": False,
        "intake_decisions_found": comparison["intake_decisions_found"],
        "real_decisions_pending": comparison["real_decisions_pending"],
        "missing_decisions": missing_decisions,
        "errors": errors,
        "artifact_verification": artifact_verification,
        "character_director_evaluation": char_evaluation,
        "workflow_td_evaluation": workflow_evaluation
    }
    
    return result
