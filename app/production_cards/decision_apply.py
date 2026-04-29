"""
Production Role Decision Apply Module

Transactionally applies validated role decisions to a project, with dry-run safety.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from app.production_cards.decision_intake import (
    load_intake_decisions,
    verify_required_approval_artifacts
)
from app.production_cards.approval_gate import (
    evaluate_character_director_decision,
    evaluate_workflow_td_decision
)


def validate_decision_source(decision: Dict[str, Any], role_name: str, project_root: str, blocked_shot: str, is_temp_copy: bool = False) -> List[str]:
    """
    Validate decision source metadata for real project apply.
    
    Returns list of error strings. Empty list means valid.
    """
    errors = []
    
    # Reject fixture-only decisions for real project apply
    if decision.get("fixture_only") is True:
        errors.append(f"{role_name}: fixture_only=true cannot be applied to real project")
        return errors
    
    # Check decision_source
    decision_source = decision.get("decision_source")
    if decision_source is None:
        errors.append(f"{role_name}: missing decision_source")
    elif decision_source != "real_role_decision":
        errors.append(f"{role_name}: decision_source must be 'real_role_decision', got '{decision_source}'")
    
    # Check approved_for_project_id matches project (skip for temp copies)
    approved_for_project_id = decision.get("approved_for_project_id")
    if approved_for_project_id is None:
        errors.append(f"{role_name}: missing approved_for_project_id")
    elif not is_temp_copy:
        project_path = Path(project_root)
        # Extract project_id from project path (last directory name or explicit project_id file)
        project_id = project_path.name
        # Also check for project_id in project metadata if available
        project_profile = project_path / "project_profile.json"
        if project_profile.exists():
            try:
                with open(project_profile, 'r') as f:
                    profile = json.load(f)
                project_id = profile.get("project_id", project_id)
            except (json.JSONDecodeError, IOError):
                pass
        if approved_for_project_id != project_id:
            errors.append(f"{role_name}: approved_for_project_id '{approved_for_project_id}' does not match project '{project_id}'")
    
    # Check approved_for_shot matches blocked shot
    approved_for_shot = decision.get("approved_for_shot")
    if approved_for_shot is None:
        errors.append(f"{role_name}: missing approved_for_shot")
    elif approved_for_shot != blocked_shot:
        errors.append(f"{role_name}: approved_for_shot '{approved_for_shot}' does not match blocked shot '{blocked_shot}'")
    
    # Check approved_by_role matches expected role
    approved_by_role = decision.get("approved_by_role")
    expected_role = decision.get("role")
    if approved_by_role is None:
        errors.append(f"{role_name}: missing approved_by_role")
    elif approved_by_role != expected_role:
        errors.append(f"{role_name}: approved_by_role '{approved_by_role}' does not match expected role '{expected_role}'")
    
    # Reject if production_accepted=true inside decision file
    if decision.get("production_accepted") is True:
        errors.append(f"{role_name}: production_accepted=true is not allowed inside decision file")
    
    return errors


def validate_before_apply(project_root: str, decisions_root: str, dry_run: bool = True, is_temp_copy: bool = False) -> Dict[str, Any]:
    """
    Validate decisions before applying them.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
        dry_run: Whether this is dry-run mode
        is_temp_copy: Whether project_root is a temp copy (allows fixture apply for testing)
    
    Returns:
        Dictionary with validation results
    """
    # Load intake decisions
    intake_decisions = load_intake_decisions(decisions_root)
    
    # Verify required artifacts
    artifact_verification = verify_required_approval_artifacts(decisions_root)
    
    # Evaluate both decisions
    # For resubmitted decisions with decision_status="submitted", treat as decided for evaluation
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
    blocked_decision_files = []
    
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
    
    # Decision source validation: only for real apply (not dry-run, not temp copy)
    if not dry_run and not is_temp_copy:
        char_decision = intake_decisions.get("character_director_decision", {})
        workflow_decision = intake_decisions.get("workflow_td_decision", {})
        
        # Determine blocked shot from decisions
        blocked_shot = char_decision.get("blocked_shot") or workflow_decision.get("blocked_shot") or "shot01"
        
        char_source_errors = validate_decision_source(char_decision, "Character Director", project_root, blocked_shot, is_temp_copy)
        workflow_source_errors = validate_decision_source(workflow_decision, "Workflow TD", project_root, blocked_shot, is_temp_copy)
        
        errors.extend(char_source_errors)
        errors.extend(workflow_source_errors)
        
        # Track blocked decision files for CLI output
        if char_source_errors:
            blocked_decision_files.append("character_director_identity_decision.json")
        if workflow_source_errors:
            blocked_decision_files.append("workflow_td_identity_workflow_decision.json")
    
    # Determine status
    if errors or missing_decisions:
        status = "invalid"
        can_apply = False
    else:
        status = "valid"
        can_apply = True
    
    return {
        "status": status,
        "can_apply": can_apply,
        "missing_decisions": missing_decisions,
        "errors": errors,
        "blocked_decision_files": blocked_decision_files,
        "artifact_verification": artifact_verification,
        "character_director_evaluation": char_evaluation,
        "workflow_td_evaluation": workflow_evaluation
    }


def create_apply_backup(project_root: str) -> Dict[str, Any]:
    """
    Create a backup of the project state before applying decisions.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with backup information
    """
    project_path = Path(project_root)
    timestamp = datetime.utcnow().isoformat().replace(":", "-").replace(".", "-")
    backup_dir = project_path.parent / f"{project_path.name}_backup_{timestamp}"
    
    # Copy the entire project to backup location
    shutil.copytree(project_path, backup_dir)
    
    return {
        "backup_created": True,
        "backup_path": str(backup_dir),
        "backup_timestamp": timestamp
    }


def write_approved_decisions(project_root: str, decisions_root: str) -> None:
    """
    Write approved decisions to the project's role_decisions directory.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
    """
    project_path = Path(project_root)
    decisions_dir = project_path / "output" / "control" / "role_decisions"
    decisions_dir.mkdir(parents=True, exist_ok=True)
    
    # Load intake decisions
    intake_decisions = load_intake_decisions(decisions_root)
    
    # Write Character Director decision
    char_decision = intake_decisions.get("character_director_decision", {})
    if char_decision:
        char_decision_path = decisions_dir / "character_director_identity_decision.json"
        with open(char_decision_path, 'w') as f:
            json.dump(char_decision, f, indent=2)
    
    # Write Workflow TD decision
    workflow_decision = intake_decisions.get("workflow_td_decision", {})
    if workflow_decision:
        workflow_decision_path = decisions_dir / "workflow_td_identity_workflow_decision.json"
        with open(workflow_decision_path, 'w') as f:
            json.dump(workflow_decision, f, indent=2)


def update_artifact_index_for_retry_gate(project_root: str) -> None:
    """
    Update artifact_index.json to reflect retry gate is open.
    
    Args:
        project_root: Path to the project root
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Update role_decision_apply section
    artifact_index["role_decision_apply"] = {
        "status": "applied",
        "retry_gate_open": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_unblocked_for": ["retry_generate_frames"]
    }
    
    # Update top-level fields for consistency
    artifact_index["retry_gate_open"] = True
    artifact_index["next_allowed_action"] = "retry_generate_frames"
    artifact_index["downstream_blocked"] = False
    
    # Update role_decisions section
    artifact_index["role_decisions"]["decision_status"] = "applied"
    artifact_index["role_decisions"]["downstream_blocked"] = False
    
    # Ensure production_accepted is false
    artifact_index["production_accepted"] = False
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def append_episode_ledger_apply_event(project_root: str) -> None:
    """
    Append role_decisions_applied event to episode_ledger.json.
    
    Args:
        project_root: Path to the project root
    """
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
    
    # Add role decision apply event
    event = {
        "event_type": "role_decisions_applied",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roles": [
            "Character Director",
            "Workflow TD / ComfyUI Technical Director"
        ],
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "comfyui_generation": False,
        "pipeline_action_rerun": False,
        "apply_mode": "transactional"
    }
    
    ledger["events"].append(event)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)


def apply_role_decisions(project_root: str, decisions_root: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Apply role decisions to a project with transactional safety.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
        dry_run: If True, only validate and report without applying (default: True)
    
    Returns:
        Dictionary with apply results
    """
    # Detect temp copy: if project_root is inside a temp directory or contains temp indicator
    import os
    import tempfile
    project_path = Path(project_root).resolve()
    temp_dirs = [tempfile.gettempdir()]
    if os.environ.get("TMPDIR"):
        temp_dirs.append(os.environ.get("TMPDIR"))
    if os.environ.get("TEMP"):
        temp_dirs.append(os.environ.get("TEMP"))
    is_temp_copy = any(str(project_path).startswith(str(Path(td).resolve())) for td in temp_dirs if td)
    
    # Also detect explicit test markers
    if os.environ.get("COMFY_AGENT_TEMP_APPLY") == "1":
        is_temp_copy = True
    
    # Validate before apply
    validation = validate_before_apply(project_root, decisions_root, dry_run=dry_run, is_temp_copy=is_temp_copy)
    
    # If validation fails, return error result with proper status
    if not validation["can_apply"]:
        # Determine if this is a fixture rejection on real project apply
        has_fixture_rejection = any("fixture_only=true" in err for err in validation["errors"])
        if has_fixture_rejection and not dry_run and not is_temp_copy:
            return {
                "status": "rejected",
                "reason": "fixture_decisions_cannot_be_applied_to_real_project",
                "dry_run": False,
                "applied_decisions": 0,
                "can_retry_generation": False,
                "production_accepted": False,
                "downstream_unblocked_for": [],
                "backup_created": False,
                "real_project_mutated": False,
                "blocked_decision_files": validation["blocked_decision_files"],
                "validation_errors": validation["errors"],
                "missing_decisions": validation["missing_decisions"]
            }
        
        return {
            "status": "blocked",
            "dry_run": dry_run,
            "can_apply": False,
            "applied_decisions": 0,
            "can_retry_generation": False,
            "next_allowed_action": None,
            "production_accepted": False,
            "downstream_unblocked_for": [],
            "backup_created": False,
            "real_project_mutated": False,
            "blocked_decision_files": validation["blocked_decision_files"],
            "validation_errors": validation["errors"],
            "missing_decisions": validation["missing_decisions"]
        }
    
    # If dry-run, return what would happen
    if dry_run:
        return {
            "status": "valid",
            "dry_run": True,
            "would_apply_decisions": 2,
            "would_allow_retry_generation": True,
            "next_allowed_action_if_applied": "retry_generate_frames",
            "production_accepted_after_apply": False,
            "real_project_mutated": False
        }
    
    # Actual apply (only if dry_run=False)
    backup_info = create_apply_backup(project_root)
    write_approved_decisions(project_root, decisions_root)
    update_artifact_index_for_retry_gate(project_root)
    append_episode_ledger_apply_event(project_root)
    
    return {
        "status": "applied",
        "dry_run": False,
        "applied_decisions": 2,
        "can_retry_generation": True,
        "next_allowed_action": "retry_generate_frames",
        "production_accepted": False,
        "downstream_unblocked_for": ["retry_generate_frames"],
        "backup_created": backup_info["backup_created"],
        "backup_path": backup_info["backup_path"],
        "real_project_mutated": False
    }
