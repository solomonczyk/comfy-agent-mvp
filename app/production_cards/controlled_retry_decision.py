"""
Controlled Retry Decision Module

Reviews failed QA state and determines whether another controlled retry can be authorized.
This is a decision/state planning layer that does NOT execute generation or downstream actions.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_qa_state(project_root: str) -> Dict[str, Any]:
    """
    Load QA state from artifact_index.json and episode_ledger.json.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with QA state including verdict, failure reasons, retry attempt
    """
    project_path = Path(project_root)
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    ledger_path = project_path / "output" / "control" / "episode_ledger.json"
    
    if not artifact_index_path.exists():
        return {
            "qa_verdict": None,
            "qa_failed": False,
            "failure_reasons": [],
            "retry_attempt": 0,
            "frame_count": 0
        }
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Extract QA state from shots section
    qa_state = {
        "qa_verdict": artifact_index.get("overall_episode_state"),
        "qa_failed": artifact_index.get("overall_episode_state") == "qa_failed",
        "failure_reasons": [],
        "retry_attempt": 1,  # Default to 1 if not explicitly tracked
        "frame_count": 0
    }
    
    # Extract from shots section
    shots = artifact_index.get("shots", [])
    for shot in shots:
        if shot.get("shot_id") == "shot01":
            qa_state["qa_verdict"] = shot.get("qa_verdict")
            qa_state["qa_failed"] = shot.get("qa_verdict") == "qa_failed"
            qa_state["frame_count"] = shot.get("frames_generated", 0)
            break
    
    # Extract failure reasons from episode_ledger QA review events
    # This is the authoritative source for failure reasons after retry attempts
    if ledger_path.exists():
        with open(ledger_path, 'r') as f:
            ledger = json.load(f)
        
        events = ledger.get("events", [])
        # Find the most recent qa_review event
        qa_review_events = [
            e for e in events 
            if e.get("event_type") == "qa_review"
        ]
        
        if qa_review_events:
            most_recent_qa_review = qa_review_events[-1]
            qa_state["failure_reasons"] = most_recent_qa_review.get("failure_reasons", [])
            # Extract retry attempt from the QA review event
            qa_state["retry_attempt"] = most_recent_qa_review.get("retry_attempt", 1)
    
    # Fallback: extract from identity QA report if no QA review event found
    if not qa_state["failure_reasons"]:
        for shot in shots:
            if shot.get("shot_id") == "shot01":
                identity_qa_report_path = shot.get("identity_qa_report_path")
                if identity_qa_report_path:
                    qa_report_path = project_path / identity_qa_report_path
                    if qa_report_path.exists():
                        with open(qa_report_path, 'r') as f:
                            qa_report = json.load(f)
                        qa_state["failure_reasons"] = qa_report.get("failure_reasons", [])
                break
    
    return qa_state


def evaluate_retry_authorization(qa_state: Dict[str, Any], project_root: str) -> Dict[str, Any]:
    """
    Evaluate whether another controlled retry should be authorized.
    
    Decision logic:
    - If retry_attempt >= 3: block retry (too many attempts)
    - If failure reasons are uncorrectable: block retry
    - If role decisions are not applied: block retry
    - Otherwise: authorize retry
    
    Args:
        qa_state: QA state dictionary
        project_root: Path to the project root
    
    Returns:
        Dictionary with authorization decision
    """
    from app.production_cards.state_repair import inspect_real_project_decision_state
    
    # Inspect project state to check role decisions
    project_state = inspect_real_project_decision_state(project_root)
    
    # Extract role decision status
    char_decision_status = project_state.get("role_decisions", {}).get("character_director", {}).get("decision_status")
    workflow_decision_status = project_state.get("role_decisions", {}).get("workflow_td", {}).get("decision_status")
    
    char_selected_decision = project_state.get("role_decisions", {}).get("character_director", {}).get("selected_decision")
    workflow_selected_decision = project_state.get("role_decisions", {}).get("workflow_td", {}).get("selected_decision")
    
    # Determine if role decisions are ready
    role_decisions_ready = (
        char_decision_status == "decided" and char_selected_decision == "approve" and
        workflow_decision_status == "decided" and workflow_selected_decision == "approve_workflow"
    )
    
    # Check retry attempt count
    retry_attempt = qa_state.get("retry_attempt", 1)
    
    # Check failure reasons for correctability
    failure_reasons = qa_state.get("failure_reasons", [])
    uncorrectable_failures = [
        "corrupted_reference",
        "missing_reference",
        "invalid_character_definition",
        "workflow_incompatible"
    ]
    
    has_uncorrectable_failures = any(
        reason in uncorrectable_failures for reason in failure_reasons
    )
    
    # Decision logic
    if retry_attempt >= 3:
        decision = "block_retry"
        reason = "max_retry_attempts_exceeded"
        retry_gate_open = False
        next_allowed_action = "manual_review"
        corrective_retry_plan = None
    elif has_uncorrectable_failures:
        decision = "block_retry"
        reason = "uncorrectable_failures_detected"
        retry_gate_open = False
        next_allowed_action = "manual_review"
        corrective_retry_plan = None
    elif not role_decisions_ready:
        decision = "block_retry"
        reason = "role_decisions_not_ready"
        retry_gate_open = False
        next_allowed_action = "await_role_decisions"
        corrective_retry_plan = None
    else:
        decision = "authorize_retry"
        reason = "correctable_failures_with_role_decisions"
        retry_gate_open = True
        next_allowed_action = "retry_generate_frames"
        # Build corrective retry plan based on failure reasons
        corrective_retry_plan = {
            "identity_consistency": "strengthen single-character identity lock and reduce multi-face/multi-subject drift",
            "visual_quality": "reduce haze, banding, and texture-collapse artifacts",
            "composition": "preserve intended character framing and prevent background/texture dominance",
            "acceptance_target": "stable single-character frames suitable for qa_review before assemble_scene"
        }
    
    return {
        "decision": decision,
        "reason": reason,
        "retry_gate_open": retry_gate_open,
        "next_allowed_action": next_allowed_action,
        "next_retry_attempt": retry_attempt + 1 if decision == "authorize_retry" else retry_attempt,
        "role_decisions_ready": role_decisions_ready,
        "has_uncorrectable_failures": has_uncorrectable_failures,
        "current_retry_attempt": retry_attempt,
        "failure_reasons": failure_reasons,
        "corrective_retry_plan": corrective_retry_plan
    }


def make_controlled_retry_decision(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Make a controlled retry decision based on failed QA state.
    
    This is a decision/state planning function that does NOT execute generation
    or downstream actions. It only determines whether another retry is authorized.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with retry decision and state updates
    """
    project_path = Path(project_root)
    
    # Load QA state
    qa_state = load_qa_state(project_root)
    
    # Evaluate retry authorization
    authorization = evaluate_retry_authorization(qa_state, project_root)
    
    # Build decision result
    result = {
        "status": "retry_decision_made",
        "decision": authorization["decision"],
        "reason": authorization["reason"],
        "retry_gate_open": authorization["retry_gate_open"],
        "next_allowed_action": authorization["next_allowed_action"],
        "next_retry_attempt": authorization["next_retry_attempt"],
        "production_accepted": False,
        "requires_operator_confirmation": True,
        "downstream_blocked": not authorization["retry_gate_open"],
        "current_retry_attempt": authorization["current_retry_attempt"],
        "failure_reasons": authorization["failure_reasons"],
        "corrective_retry_plan": authorization["corrective_retry_plan"],
        "role_decisions_ready": authorization["role_decisions_ready"],
        "comfyui_generation": False,
        "generation_performed": False,
        "retry_generate_frames_executed": False,
        "qa_review_executed": False,
        "assemble_scene_executed": False,
        "audio_executed": False,
        "render_executed": False,
        "downstream_actions_executed": False
    }
    
    return result


def apply_controlled_retry_decision(project_root: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Apply controlled retry decision to project state.
    
    Updates artifact_index.json and episode_ledger.json with the decision.
    Does NOT execute generation or downstream actions.
    
    Args:
        project_root: Path to the project root
        dry_run: If True, only report what would be applied without mutating
    
    Returns:
        Dictionary with apply results
    """
    project_path = Path(project_root)
    
    # Make the decision
    decision = make_controlled_retry_decision(project_root, json_output=True)
    
    if dry_run:
        return {
            "status": "dry_run_complete",
            "dry_run": True,
            "decision": decision,
            "would_mutate_files": ["artifact_index.json", "episode_ledger.json"]
        }
    
    # Apply the decision to artifact_index.json
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        # Update top-level fields
        artifact_index["retry_gate_open"] = decision["retry_gate_open"]
        artifact_index["next_allowed_action"] = decision["next_allowed_action"]
        artifact_index["downstream_blocked"] = decision["downstream_blocked"]
        artifact_index["production_accepted"] = decision["production_accepted"]
        
        # Add controlled retry decision section
        artifact_index["controlled_retry_decision"] = {
            "status": decision["status"],
            "decision": decision["decision"],
            "reason": decision["reason"],
            "retry_gate_open": decision["retry_gate_open"],
            "next_allowed_action": decision["next_allowed_action"],
            "next_retry_attempt": decision["next_retry_attempt"],
            "current_retry_attempt": decision["current_retry_attempt"],
            "failure_reasons": decision["failure_reasons"],
            "corrective_retry_plan": decision["corrective_retry_plan"],
            "requires_operator_confirmation": decision["requires_operator_confirmation"],
            "decision_timestamp": datetime.utcnow().isoformat() + "Z"
        }
        
        with open(artifact_index_path, 'w') as f:
            json.dump(artifact_index, f, indent=2)
    
    # Append decision event to episode_ledger.json
    ledger_path = project_path / "output" / "control" / "episode_ledger.json"
    
    if ledger_path.exists():
        with open(ledger_path, 'r') as f:
            ledger = json.load(f)
        
        if "events" not in ledger:
            ledger["events"] = []
        
        # Add controlled retry decision event
        event = {
            "event_type": "controlled_retry_decision",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "source": "qa_failed_retry_frames",
            "previous_retry_attempt": decision["current_retry_attempt"],
            "qa_verdict": "qa_failed",
            "decision": decision["decision"],
            "next_retry_attempt": decision["next_retry_attempt"],
            "failure_reasons": decision["failure_reasons"],
            "corrective_retry_plan": decision["corrective_retry_plan"],
            "retry_gate_open": decision["retry_gate_open"],
            "next_allowed_action": decision["next_allowed_action"],
            "production_accepted": decision["production_accepted"],
            "comfyui_generation": False,
            "generation_performed": False,
            "retry_generate_frames_executed": False,
            "qa_review_executed": False,
            "assemble_scene_executed": False,
            "audio_executed": False,
            "render_executed": False,
            "downstream_actions_executed": False
        }
        
        ledger["events"].append(event)
        
        with open(ledger_path, 'w') as f:
            json.dump(ledger, f, indent=2)
    
    return {
        "status": "decision_applied",
        "dry_run": False,
        "decision": decision,
        "files_mutated": ["artifact_index.json", "episode_ledger.json"],
        "decision_timestamp": datetime.utcnow().isoformat() + "Z"
    }
