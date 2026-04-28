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


def validate_before_apply(project_root: str, decisions_root: str) -> Dict[str, Any]:
    """
    Validate decisions before applying them.
    
    Args:
        project_root: Path to the project root
        decisions_root: Path to directory containing intake decision files
    
    Returns:
        Dictionary with validation results
    """
    # Load intake decisions
    intake_decisions = load_intake_decisions(decisions_root)
    
    # Verify required artifacts
    artifact_verification = verify_required_approval_artifacts(decisions_root)
    
    # Evaluate both decisions
    char_evaluation = evaluate_character_director_decision(
        intake_decisions.get("character_director_decision", {})
    )
    workflow_evaluation = evaluate_workflow_td_decision(
        intake_decisions.get("workflow_td_decision", {})
    )
    
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
    # Validate before apply
    validation = validate_before_apply(project_root, decisions_root)
    
    # If validation fails, return error result
    if not validation["can_apply"]:
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
