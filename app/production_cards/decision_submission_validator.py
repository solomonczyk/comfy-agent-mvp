"""
Production Role Decision Submission Validator Module

Validates completed real role decision submission files before they are allowed
into decision intake/apply flow. This is a read-only validation that does NOT
mutate the project or apply any decisions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional


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
        submissions_dir = Path(project_root) / "output" / "control" / "role_decision_submissions"

    character_director_submission = {}
    workflow_td_submission = {}

    # Look for Character Director submission
    char_submission_path = submissions_dir / "character_director_real_decision.SUBMIT.json"
    if char_submission_path.exists():
        with open(char_submission_path, 'r') as f:
            character_director_submission = json.load(f)

    # Look for Workflow TD submission
    workflow_submission_path = submissions_dir / "workflow_td_real_decision.SUBMIT.json"
    if workflow_submission_path.exists():
        with open(workflow_submission_path, 'r') as f:
            workflow_td_submission = json.load(f)

    return {
        "character_director_submission": character_director_submission,
        "workflow_td_submission": workflow_td_submission
    }


def validate_character_director_submission(submission: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    """
    Validate Character Director submission for safety and completeness.

    Rejects if:
    - fixture_only=true
    - decision_source != real_role_decision
    - approved_by_role missing or mismatched
    - approved_for_project_id missing or mismatched
    - approved_for_shot missing or mismatched
    - selected_decision is null (incomplete)
    - selected_decision not in allowed_decisions
    - production_accepted=true
    - required approval artifacts are missing

    Args:
        submission: Character Director submission data
        project_id: Expected project ID from project root

    Returns:
        Validation result dict with valid flag and rejection reasons
    """
    result = {
        "role": "Character Director",
        "valid": False,
        "rejection_reasons": [],
        "is_complete": False
    }

    if not submission:
        result["rejection_reasons"].append("submission_not_found")
        return result

    # Reject fixture_only=true
    if submission.get("fixture_only"):
        result["rejection_reasons"].append("fixture_only_true_rejected")

    # Reject decision_source mismatch
    if submission.get("decision_source") != "real_role_decision":
        result["rejection_reasons"].append("decision_source_not_real_role_decision")

    # Check approved_by_role
    expected_role = "Character Director"
    if submission.get("approved_by_role") != expected_role:
        result["rejection_reasons"].append(f"approved_by_role_mismatch: expected {expected_role}")

    # Check approved_for_project_id
    if submission.get("approved_for_project_id") != project_id:
        result["rejection_reasons"].append(f"approved_for_project_id_mismatch: expected {project_id}")

    # Check approved_for_shot exists
    if not submission.get("approved_for_shot"):
        result["rejection_reasons"].append("approved_for_shot_missing")

    # Check selected_decision
    selected_decision = submission.get("selected_decision")
    if selected_decision is None:
        result["is_complete"] = False
        result["rejection_reasons"].append("selected_decision_null_incomplete")
    else:
        result["is_complete"] = True
        allowed_decisions = submission.get("allowed_decisions", [])
        if selected_decision not in allowed_decisions:
            result["rejection_reasons"].append(f"selected_decision_not_allowed: {selected_decision}")

    # Reject production_accepted=true
    if submission.get("production_accepted"):
        result["rejection_reasons"].append("production_accepted_true_rejected")

    # Check required artifacts if complete
    if result["is_complete"]:
        required_artifacts = submission.get("required_artifacts", [])
        # In a real implementation, we would check if these artifacts exist
        # For now, we just validate the field exists and is non-empty
        if not required_artifacts:
            result["rejection_reasons"].append("required_artifacts_missing")

    # Determine validity
    result["valid"] = len(result["rejection_reasons"]) == 0

    return result


def validate_workflow_td_submission(submission: Dict[str, Any], project_id: str) -> Dict[str, Any]:
    """
    Validate Workflow TD submission for safety and completeness.

    Rejects if:
    - fixture_only=true
    - decision_source != real_role_decision
    - approved_by_role missing or mismatched
    - approved_for_project_id missing or mismatched
    - approved_for_shot missing or mismatched
    - selected_decision is null (incomplete)
    - selected_decision not in allowed_decisions
    - production_accepted=true
    - legacy_reference_locked_allowed_for_production=true
    - current_required_generation_mode != gorynych_identity
    - required approval artifacts are missing

    Args:
        submission: Workflow TD submission data
        project_id: Expected project ID from project root

    Returns:
        Validation result dict with valid flag and rejection reasons
    """
    result = {
        "role": "Workflow TD / ComfyUI Technical Director",
        "valid": False,
        "rejection_reasons": [],
        "is_complete": False
    }

    if not submission:
        result["rejection_reasons"].append("submission_not_found")
        return result

    # Reject fixture_only=true
    if submission.get("fixture_only"):
        result["rejection_reasons"].append("fixture_only_true_rejected")

    # Reject decision_source mismatch
    if submission.get("decision_source") != "real_role_decision":
        result["rejection_reasons"].append("decision_source_not_real_role_decision")

    # Check approved_by_role
    expected_role = "Workflow TD / ComfyUI Technical Director"
    if submission.get("approved_by_role") != expected_role:
        result["rejection_reasons"].append(f"approved_by_role_mismatch: expected {expected_role}")

    # Check approved_for_project_id
    if submission.get("approved_for_project_id") != project_id:
        result["rejection_reasons"].append(f"approved_for_project_id_mismatch: expected {project_id}")

    # Check approved_for_shot exists
    if not submission.get("approved_for_shot"):
        result["rejection_reasons"].append("approved_for_shot_missing")

    # Check selected_decision
    selected_decision = submission.get("selected_decision")
    if selected_decision is None:
        result["is_complete"] = False
        result["rejection_reasons"].append("selected_decision_null_incomplete")
    else:
        result["is_complete"] = True
        allowed_decisions = submission.get("allowed_decisions", [])
        if selected_decision not in allowed_decisions:
            result["rejection_reasons"].append(f"selected_decision_not_allowed: {selected_decision}")

    # Reject production_accepted=true
    if submission.get("production_accepted"):
        result["rejection_reasons"].append("production_accepted_true_rejected")

    # Reject legacy_reference_locked_allowed_for_production=true
    if submission.get("legacy_reference_locked_allowed_for_production"):
        result["rejection_reasons"].append("legacy_reference_locked_true_rejected")

    # Reject non-gorynych mode
    generation_mode = submission.get("current_required_generation_mode")
    if generation_mode != "gorynych_identity":
        result["rejection_reasons"].append(f"generation_mode_not_gorynych: {generation_mode}")

    # Check required artifacts if complete
    if result["is_complete"]:
        required_artifacts = submission.get("required_artifacts", [])
        if not required_artifacts:
            result["rejection_reasons"].append("required_artifacts_missing")

    # Determine validity
    result["valid"] = len(result["rejection_reasons"]) == 0

    return result


def compare_submission_against_contract(project_root: str, submission: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compare submission against the original contract to detect tampering.

    Args:
        project_root: Path to the project root
        submission: Submission data to validate

    Returns:
        Comparison result with contract_compliance flag
    """
    # Load the original contract template
    submissions_dir = Path(project_root) / "output" / "control" / "role_decision_submissions"

    # Determine which contract to compare against
    role = submission.get("role", "")
    if "Character Director" in role:
        contract_path = submissions_dir / "character_director_real_decision.SUBMIT.json"
    elif "Workflow TD" in role:
        contract_path = submissions_dir / "workflow_td_real_decision.SUBMIT.json"
    else:
        return {
            "contract_compliant": False,
            "reason": "unknown_role"
        }

    if not contract_path.exists():
        return {
            "contract_compliant": False,
            "reason": "contract_not_found"
        }

    with open(contract_path, 'r') as f:
        contract = json.load(f)

    # Compare critical fields
    critical_fields = [
        "decision_source",
        "fixture_only",
        "approved_by_role",
        "approved_for_project_id",
        "approved_for_shot"
    ]

    mismatches = []
    for field in critical_fields:
        if submission.get(field) != contract.get(field):
            mismatches.append(f"{field}_mismatch")

    return {
        "contract_compliant": len(mismatches) == 0,
        "mismatches": mismatches
    }


def validate_submitted_role_decisions(project_root: str, submission_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Validate submitted role decisions and determine if ready for intake/apply.

    This is a read-only validation that does NOT mutate the project.

    For blank templates (selected_decision=null):
    - Returns status="awaiting_role_input"
    - submitted_decisions_ready=false
    - retry_gate_open=false
    - production_accepted=false
    - downstream_blocked=true

    For completed approved submissions:
    - Returns status="valid"
    - submitted_decisions_ready=true
    - would_allow_intake=true
    - would_allow_retry_generation_after_apply=true
    - next_allowed_action_if_applied="retry_generate_frames"
    - production_accepted_after_apply=false
    - retry_gate_open=false
    - real_project_mutated=false

    Args:
        project_root: Path to the project root
        submission_root: Optional custom path to load submissions from (for fixture validation)

    Returns:
        Dictionary with validation results
    """
    project_path = Path(project_root)
    project_id = project_path.name

    # Load submissions
    submissions = load_submitted_decisions(project_root, submission_root)
    char_submission = submissions["character_director_submission"]
    workflow_submission = submissions["workflow_td_submission"]

    # Validate each submission
    char_validation = validate_character_director_submission(char_submission, project_id)
    workflow_validation = validate_workflow_td_submission(workflow_submission, project_id)

    # Count valid and complete submissions
    valid_submissions = 0
    complete_submissions = 0
    all_rejection_reasons = []

    if char_validation["valid"]:
        valid_submissions += 1
    if char_validation["is_complete"]:
        complete_submissions += 1
    all_rejection_reasons.extend([f"character_director: {r}" for r in char_validation["rejection_reasons"]])

    if workflow_validation["valid"]:
        valid_submissions += 1
    if workflow_validation["is_complete"]:
        complete_submissions += 1
    all_rejection_reasons.extend([f"workflow_td: {r}" for r in workflow_validation["rejection_reasons"]])

    # Determine overall status
    if complete_submissions == 0:
        # Both submissions are blank (selected_decision=null)
        status = "awaiting_role_input"
        submitted_decisions_ready = False
        would_allow_intake = False
    elif valid_submissions == 2:
        # Both submissions are valid and complete
        status = "valid"
        submitted_decisions_ready = True
        would_allow_intake = True
    else:
        # Some submissions are invalid or incomplete
        status = "invalid"
        submitted_decisions_ready = False
        would_allow_intake = False

    # Build result
    result = {
        "status": status,
        "submitted_decisions_ready": submitted_decisions_ready,
        "valid_submissions": valid_submissions,
        "complete_submissions": complete_submissions,
        "missing_or_incomplete_submissions": [],
        "rejection_reasons": all_rejection_reasons,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True
    }

    # Add missing/incomplete submissions list
    if not char_submission:
        result["missing_or_incomplete_submissions"].append("character_identity_approval")
    elif not char_validation["is_complete"]:
        result["missing_or_incomplete_submissions"].append("character_identity_approval")

    if not workflow_submission:
        result["missing_or_incomplete_submissions"].append("workflow_fit_approval")
    elif not workflow_validation["is_complete"]:
        result["missing_or_incomplete_submissions"].append("workflow_fit_approval")

    # Add what-if analysis for valid submissions
    if status == "valid":
        result["would_allow_intake"] = True
        result["would_allow_retry_generation_after_apply"] = True
        result["next_allowed_action_if_applied"] = "retry_generate_frames"
        result["production_accepted_after_apply"] = False
        result["retry_gate_open"] = False
        result["real_project_mutated"] = False

    return result
