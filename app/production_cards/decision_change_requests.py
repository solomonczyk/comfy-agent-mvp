"""
Production Role Decision Change Requests Module

Converts submitted decision outcomes into concrete change request artifacts
so the system can act on request_workflow_change and request_reference_rebuild
without opening retry generation or applying decisions.

This is a read-only artifact creation that does NOT:
- Apply decisions
- Open retry gate
- Mark production_accepted=true
- Run ComfyUI or generation
- Mutate role_decisions/
- Mutate final artifacts
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def load_submitted_decision_outcome(
    project_root: str,
    submission_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Load the submitted decision outcome from the decision_submission_outcome module.
    
    This reuses the outcome evaluation from RC2-PRODCARDS2P.
    
    Args:
        project_root: Path to the project root
        submission_root: Optional custom path to load submissions from
    
    Returns:
        Dictionary with the submitted decision outcome
    """
    from app.production_cards.decision_submission_outcome import evaluate_submitted_decision_outcome
    
    return evaluate_submitted_decision_outcome(project_root, submission_root)


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


def create_workflow_change_request(
    project_root: str,
    submitted_outcome: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a workflow change request based on Character Director's request_workflow_change.
    
    Args:
        project_root: Path to the project root
        submitted_outcome: The submitted decision outcome
    
    Returns:
        Dictionary with workflow change request
    """
    request = {
        "request_type": "workflow_change_request",
        "source_role": "Character Director",
        "source_decision": submitted_outcome.get("character_director_outcome", "request_workflow_change"),
        "blocked_shot": "shot01",
        "reason": "identity_qa_failed",
        "target_role": "Workflow TD / ComfyUI Technical Director",
        "required_generation_mode": "gorynych_identity",
        "legacy_reference_locked_allowed_for_production": False,
        "required_action": "revise_identity_workflow_strategy",
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return request


def create_reference_rebuild_request(
    project_root: str,
    submitted_outcome: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Create a reference rebuild request based on Workflow TD's request_reference_rebuild.
    
    Args:
        project_root: Path to the project root
        submitted_outcome: The submitted decision outcome
    
    Returns:
        Dictionary with reference rebuild request
    """
    request = {
        "request_type": "reference_rebuild_request",
        "source_role": "Workflow TD / ComfyUI Technical Director",
        "source_decision": submitted_outcome.get("workflow_td_outcome", "request_reference_rebuild"),
        "blocked_shot": "shot01",
        "reason": "identity_qa_failed",
        "target_role": "Character Director",
        "required_action": "rebuild_or_update_identity_reference_strategy",
        "required_generation_mode": "gorynych_identity",
        "legacy_reference_locked_allowed_for_production": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return request


def create_change_request_summary(
    project_root: str,
    submitted_outcome: Dict[str, Any],
    workflow_request: Dict[str, Any],
    reference_request: Dict[str, Any]
) -> str:
    """
    Create a markdown summary of the change requests.
    
    Args:
        project_root: Path to the project root
        submitted_outcome: The submitted decision outcome
        workflow_request: The workflow change request
        reference_request: The reference rebuild request
    
    Returns:
        Markdown string with change request summary
    """
    summary = f"""# Decision Change Request Summary

## Current Submitted Decision Outcomes

- **Character Director Outcome**: {submitted_outcome.get('character_director_outcome', 'unknown')}
- **Workflow TD Outcome**: {submitted_outcome.get('workflow_td_outcome', 'unknown')}
- **Overall Status**: {submitted_outcome.get('status', 'unknown')}

## Why Retry Remains Blocked

The retry gate remains closed because the submitted decisions are change requests, not approvals:
- `ready_for_apply`: {submitted_outcome.get('ready_for_apply', False)}
- `can_retry_generation`: {submitted_outcome.get('can_retry_generation', False)}
- `retry_gate_open`: {submitted_outcome.get('retry_gate_open', False)}

Before retry generation can proceed, the following change requests must be resolved.

## Next Required Actions by Role

### Workflow TD / ComfyUI Technical Director

**Request Type**: {workflow_request.get('request_type')}
**Source Role**: {workflow_request.get('source_role')}
**Required Action**: {workflow_request.get('required_action')}

The Character Director has requested a workflow change. The Workflow TD must revise the identity workflow strategy to address the identity QA failure.

### Character Director

**Request Type**: {reference_request.get('request_type')}
**Source Role**: {reference_request.get('source_role')}
**Required Action**: {reference_request.get('required_action')}

The Workflow TD has requested a reference rebuild. The Character Director must rebuild or update the identity reference strategy to address the identity QA failure.

## What Must Be Resolved Before Approval/Apply

1. Workflow TD revises identity workflow strategy
2. Character Director reviews updated workflow strategy
3. Character Director rebuilds or updates identity reference strategy
4. Workflow TD reviews updated reference strategy
5. Both roles submit new decisions with `selected_decision=approve` or `approve_workflow`
6. Required artifacts are complete and validated

## Generation Authorization

**Generation Authorized**: False
**Reason**: Submitted decisions are change requests, not approvals. No ComfyUI execution has been authorized.

## Project State

- `production_accepted`: {submitted_outcome.get('production_accepted', False)}
- `downstream_blocked`: {submitted_outcome.get('downstream_blocked', True)}
- `apply_performed`: {submitted_outcome.get('apply_performed', False)}

No apply, generation, or downstream action has been executed.
"""
    
    return summary


def append_episode_ledger_event(
    project_root: str,
    event_type: str,
    reason: str,
    ready_for_apply: bool,
    retry_gate_open: bool,
    production_accepted: bool,
    downstream_blocked: bool
) -> None:
    """
    Append an event to the episode ledger.
    
    Args:
        project_root: Path to the project root
        event_type: Type of event
        reason: Reason for the event
        ready_for_apply: Whether ready for apply
        retry_gate_open: Whether retry gate is open
        production_accepted: Whether production is accepted
        downstream_blocked: Whether downstream is blocked
    """
    ledger = load_episode_ledger(project_root)
    
    event = {
        "event_type": event_type,
        "reason": reason,
        "ready_for_apply": ready_for_apply,
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


def update_artifact_index_for_change_requests(
    project_root: str,
    result: Dict[str, Any]
) -> None:
    """
    Update artifact_index.json with change request creation (passive pointer only).
    
    This records the change request creation without opening retry or applying decisions.
    
    Args:
        project_root: Path to the project root
        result: The result of create_decision_change_request_pack
    """
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add decision_change_requests section as passive pointer
    artifact_index["decision_change_requests"] = {
        "status": "created",
        "change_requests_created": result.get("change_requests_created", 0),
        "outcome_status": result.get("outcome_status"),
        "ready_for_apply": result.get("ready_for_apply", False),
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


def create_decision_change_request_pack(
    project_root: str,
    submission_root: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a decision change request pack from submitted decision outcomes.
    
    This converts submitted decision outcomes into concrete change request artifacts
    so the system can act on request_workflow_change and request_reference_rebuild
    without opening retry generation or applying decisions.
    
    This is a read-only artifact creation that does NOT:
    - Apply decisions
    - Open retry gate
    - Mark production_accepted=true
    - Run ComfyUI or generation
    - Mutate role_decisions/
    - Mutate final artifacts
    
    Args:
        project_root: Path to the project root
        submission_root: Optional custom path to load submissions from
    
    Returns:
        Dictionary with creation result
    """
    project_path = Path(project_root)
    
    # Load submitted decision outcome
    submitted_outcome = load_submitted_decision_outcome(project_root, submission_root)
    
    # Create output directory
    change_requests_dir = project_path / "output" / "control" / "decision_change_requests"
    change_requests_dir.mkdir(parents=True, exist_ok=True)
    
    # Create workflow change request if needed
    workflow_request = None
    if submitted_outcome.get("character_director_outcome") == "request_workflow_change":
        workflow_request = create_workflow_change_request(project_root, submitted_outcome)
        
        workflow_request_path = change_requests_dir / "workflow_change_request.json"
        with open(workflow_request_path, 'w') as f:
            json.dump(workflow_request, f, indent=2)
    
    # Create reference rebuild request if needed
    reference_request = None
    if submitted_outcome.get("workflow_td_outcome") == "request_reference_rebuild":
        reference_request = create_reference_rebuild_request(project_root, submitted_outcome)
        
        reference_request_path = change_requests_dir / "reference_rebuild_request.json"
        with open(reference_request_path, 'w') as f:
            json.dump(reference_request, f, indent=2)
    
    # Create change request summary
    summary = create_change_request_summary(
        project_root,
        submitted_outcome,
        workflow_request or {},
        reference_request or {}
    )
    
    summary_path = change_requests_dir / "CHANGE_REQUEST_SUMMARY.md"
    with open(summary_path, 'w') as f:
        f.write(summary)
    
    # Count change requests created
    change_requests_created = 0
    if workflow_request:
        change_requests_created += 1
    if reference_request:
        change_requests_created += 1
    
    # Update artifact index with passive pointer
    result = {
        "status": "completed",
        "change_requests_created": change_requests_created,
        "outcome_status": submitted_outcome.get("status"),
        "ready_for_apply": submitted_outcome.get("ready_for_apply", False),
        "can_retry_generation": submitted_outcome.get("can_retry_generation", False),
        "retry_gate_open": submitted_outcome.get("retry_gate_open", False),
        "production_accepted": submitted_outcome.get("production_accepted", False),
        "downstream_blocked": submitted_outcome.get("downstream_blocked", True),
        "apply_performed": submitted_outcome.get("apply_performed", False),
        "generation_authorized": False
    }
    
    update_artifact_index_for_change_requests(project_root, result)
    
    # Append event to episode ledger
    append_episode_ledger_event(
        project_root,
        "decision_change_requests_created",
        "submitted_role_decisions_requested_changes",
        result["ready_for_apply"],
        result["retry_gate_open"],
        result["production_accepted"],
        result["downstream_blocked"]
    )
    
    return result


def validate_decision_change_request_pack(project_root: str) -> Dict[str, Any]:
    """
    Validate the decision change request pack.
    
    Checks that:
    - Change request files exist
    - Change requests are valid
    - Ready for apply is false
    - Retry gate remains closed
    - Production accepted remains false
    - Downstream remains blocked
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with validation result
    """
    project_path = Path(project_root)
    change_requests_dir = project_path / "output" / "control" / "decision_change_requests"
    
    result = {
        "status": "valid",
        "change_requests_found": 0,
        "next_required_roles": [],
        "ready_for_apply": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "validation_errors": []
    }
    
    # Check workflow change request
    workflow_request_path = change_requests_dir / "workflow_change_request.json"
    if workflow_request_path.exists():
        with open(workflow_request_path, 'r') as f:
            workflow_request = json.load(f)
        
        result["change_requests_found"] += 1
        result["next_required_roles"].append(workflow_request.get("target_role"))
        
        # Validate workflow request
        if workflow_request.get("retry_gate_open"):
            result["status"] = "invalid"
            result["validation_errors"].append("workflow_change_request has retry_gate_open=true")
        
        if workflow_request.get("production_accepted"):
            result["status"] = "invalid"
            result["validation_errors"].append("workflow_change_request has production_accepted=true")
        
        if not workflow_request.get("downstream_blocked"):
            result["status"] = "invalid"
            result["validation_errors"].append("workflow_change_request has downstream_blocked=false")
    
    # Check reference rebuild request
    reference_request_path = change_requests_dir / "reference_rebuild_request.json"
    if reference_request_path.exists():
        with open(reference_request_path, 'r') as f:
            reference_request = json.load(f)
        
        result["change_requests_found"] += 1
        if reference_request.get("target_role") not in result["next_required_roles"]:
            result["next_required_roles"].append(reference_request.get("target_role"))
        
        # Validate reference request
        if reference_request.get("retry_gate_open"):
            result["status"] = "invalid"
            result["validation_errors"].append("reference_rebuild_request has retry_gate_open=true")
        
        if reference_request.get("production_accepted"):
            result["status"] = "invalid"
            result["validation_errors"].append("reference_rebuild_request has production_accepted=true")
        
        if not reference_request.get("downstream_blocked"):
            result["status"] = "invalid"
            result["validation_errors"].append("reference_rebuild_request has downstream_blocked=false")
    
    # Check summary
    summary_path = change_requests_dir / "CHANGE_REQUEST_SUMMARY.md"
    if not summary_path.exists():
        result["status"] = "invalid"
        result["validation_errors"].append("CHANGE_REQUEST_SUMMARY.md not found")
    
    # Verify artifact_index state
    artifact_index = load_artifact_index(project_root)
    
    if artifact_index.get("retry_gate_open"):
        result["status"] = "invalid"
        result["validation_errors"].append("artifact_index has retry_gate_open=true")
    
    if artifact_index.get("production_accepted"):
        result["status"] = "invalid"
        result["validation_errors"].append("artifact_index has production_accepted=true")
    
    if not artifact_index.get("downstream_blocked", True):
        result["status"] = "invalid"
        result["validation_errors"].append("artifact_index has downstream_blocked=false")
    
    # Verify role_decisions remain pending
    role_decisions_dir = project_path / "output" / "control" / "role_decisions"
    
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            char_decision = json.load(f)
        
        if char_decision.get("decision_status") != "pending":
            result["status"] = "invalid"
            result["validation_errors"].append(f"character_director decision_status is {char_decision.get('decision_status')}, not pending")
    
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_decision = json.load(f)
        
        if workflow_decision.get("decision_status") != "pending":
            result["status"] = "invalid"
            result["validation_errors"].append(f"workflow_td decision_status is {workflow_decision.get('decision_status')}, not pending")
    
    return result
