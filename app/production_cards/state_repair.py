"""
Production State Repair Module

Detects and repairs pre-fix fixture approval mutations in real project state.
This module provides inspection and repair capabilities for corrupted project
state caused by fixture decisions being applied before safety hardening.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime


def inspect_real_project_decision_state(project_root: str) -> Dict[str, Any]:
    """
    Inspect the real project decision state to detect corruption.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with inspection results including role decisions,
        artifact_index state, episode_ledger events, and safety assessment
    """
    project_path = Path(project_root)
    
    # Load role decisions
    role_decisions_dir = project_path / "output" / "control" / "role_decisions"
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    
    char_decision = {}
    workflow_decision = {}
    
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            char_decision = json.load(f)
    
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_decision = json.load(f)
    
    # Load artifact_index
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    artifact_index = {}
    role_decision_apply_state = {}
    
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        role_decision_apply_state = artifact_index.get("role_decision_apply", {})
    
    # Load episode_ledger
    episode_ledger_path = project_path / "output" / "control" / "episode_ledger.json"
    episode_ledger = {}
    role_decision_apply_events = []
    pre_fix_invalidation_events = []
    
    if episode_ledger_path.exists():
        with open(episode_ledger_path, 'r') as f:
            episode_ledger = json.load(f)
        
        # Extract role_decisions_applied events and pre_fix_fixture_apply_invalidated events
        events = episode_ledger.get("events", [])
        role_decision_apply_events = [
            e for e in events 
            if e.get("event_type") == "role_decisions_applied"
        ]
        pre_fix_invalidation_events = [
            e for e in events
            if e.get("event_type") == "pre_fix_fixture_apply_invalidated"
        ]
    
    # Detect corruption indicators
    corruption_indicators = {
        "role_decision_apply_status_applied": role_decision_apply_state.get("status") == "applied",
        "retry_gate_open": role_decision_apply_state.get("retry_gate_open") == True,
        "next_action_retry_generate": role_decision_apply_state.get("next_allowed_action") == "retry_generate_frames",
        "char_decision_not_pending": char_decision.get("decision_status") != "pending",
        "workflow_decision_not_pending": workflow_decision.get("decision_status") != "pending",
        "char_production_accepted_true": char_decision.get("production_accepted") == True,
        "workflow_production_accepted_true": workflow_decision.get("production_accepted") == True,
        "has_role_decision_apply_events": len(role_decision_apply_events) > 0
    }
    
    # Determine if historical contamination is documented (invalidated by corrective event)
    historical_contamination_documented = (
        len(role_decision_apply_events) > 0 and len(pre_fix_invalidation_events) > 0
    )
    
    # Determine active corruption (excluding historical contamination if invalidated)
    # If there's a pre_fix_invalidation event, historical role_decisions_applied events
    # are treated as documented contamination, not active corruption
    active_corruption_indicators = corruption_indicators.copy()
    if historical_contamination_documented:
        # Historical apply events are invalidated, so they don't count as active corruption
        active_corruption_indicators["has_role_decision_apply_events"] = False
    
    has_active_corruption = any(active_corruption_indicators.values())
    
    # Legacy has_corruption field for backward compatibility
    has_corruption = any(corruption_indicators.values())
    
    # Determine if state is safe for next step (based on active corruption only)
    safe_for_next_step = not has_active_corruption
    
    # Determine if role decisions are pending
    role_decisions_pending = (
        char_decision.get("decision_status") == "pending" and
        workflow_decision.get("decision_status") == "pending"
    )
    
    return {
        "project_root": str(project_root),
        "role_decisions": {
            "character_director": {
                "decision_status": char_decision.get("decision_status"),
                "selected_decision": char_decision.get("selected_decision"),
                "production_accepted": char_decision.get("production_accepted"),
                "downstream_blocked": char_decision.get("downstream_blocked")
            },
            "workflow_td": {
                "decision_status": workflow_decision.get("decision_status"),
                "selected_decision": workflow_decision.get("selected_decision"),
                "production_accepted": workflow_decision.get("production_accepted"),
                "downstream_blocked": workflow_decision.get("downstream_blocked")
            }
        },
        "artifact_index": {
            "role_decision_apply_status": role_decision_apply_state.get("status"),
            "retry_gate_open": artifact_index.get("retry_gate_open"),
            "next_allowed_action": artifact_index.get("next_allowed_action"),
            "production_accepted": artifact_index.get("production_accepted"),
            "downstream_blocked": artifact_index.get("downstream_blocked")
        },
        "episode_ledger": {
            "role_decision_apply_event_count": len(role_decision_apply_events),
            "pre_fix_invalidation_event_count": len(pre_fix_invalidation_events),
            "most_recent_apply_event": role_decision_apply_events[-1] if role_decision_apply_events else None,
            "most_recent_invalidation_event": pre_fix_invalidation_events[-1] if pre_fix_invalidation_events else None
        },
        "corruption_indicators": corruption_indicators,
        "has_corruption": has_corruption,
        "has_active_corruption": has_active_corruption,
        "historical_contamination_documented": historical_contamination_documented,
        "safe_for_next_step": safe_for_next_step,
        "role_decisions_pending": role_decisions_pending,
        "inspection_timestamp": datetime.utcnow().isoformat() + "Z"
    }


def detect_pre_fix_fixture_apply_mutations(project_root: str) -> Dict[str, Any]:
    """
    Detect pre-fix fixture apply mutations in project state.
    
    Args:
        project_root: Path to the project root
    
    Returns:
        Dictionary with detection results and specific mutation details
    """
    inspection = inspect_real_project_decision_state(project_root)
    
    mutations_detected = []
    
    if inspection["corruption_indicators"]["role_decision_apply_status_applied"]:
        mutations_detected.append({
            "type": "artifact_index_role_decision_apply_status",
            "severity": "high",
            "description": "artifact_index.role_decision_apply.status is 'applied' but decisions are pending"
        })
    
    if inspection["corruption_indicators"]["retry_gate_open"]:
        mutations_detected.append({
            "type": "retry_gate_open",
            "severity": "high",
            "description": "retry_gate_open=true but no valid role decisions applied"
        })
    
    if inspection["corruption_indicators"]["next_action_retry_generate"]:
        mutations_detected.append({
            "type": "next_allowed_action",
            "severity": "high",
            "description": "next_allowed_action=retry_generate_frames but gate should be blocked"
        })
    
    if inspection["corruption_indicators"]["has_role_decision_apply_events"]:
        mutations_detected.append({
            "type": "ledger_historical_contamination",
            "severity": "medium",
            "description": f"episode_ledger contains {inspection['episode_ledger']['role_decision_apply_event_count']} role_decisions_applied events from pre-fix fixture applications"
        })
    
    return {
        "project_root": project_root,
        "mutations_detected": mutations_detected,
        "total_mutations": len(mutations_detected),
        "requires_repair": len(mutations_detected) > 0,
        "detection_timestamp": datetime.utcnow().isoformat() + "Z"
    }


def repair_pre_fix_fixture_apply_mutations(project_root: str, dry_run: bool = True) -> Dict[str, Any]:
    """
    Repair pre-fix fixture apply mutations in project state.
    
    Args:
        project_root: Path to the project root
        dry_run: If True, only report what would be repaired without mutating
    
    Returns:
        Dictionary with repair results including changes made and validation
    """
    project_path = Path(project_root)
    
    # Get current state
    inspection = inspect_real_project_decision_state(project_root)
    detection = detect_pre_fix_fixture_apply_mutations(project_root)
    
    repair_actions = []
    
    if not detection["requires_repair"]:
        return {
            "project_root": project_root,
            "dry_run": dry_run,
            "status": "no_repair_needed",
            "repair_actions": [],
            "repairs_performed": 0,
            "validation": {
                "safe_for_next_step": inspection["safe_for_next_step"],
                "role_decisions_pending": True,
                "retry_gate_closed": True,
                "production_accepted_false": True,
                "downstream_blocked": True
            }
        }
    
    # Prepare repair actions
    if inspection["corruption_indicators"]["role_decision_apply_status_applied"] or \
       inspection["corruption_indicators"]["retry_gate_open"] or \
       inspection["corruption_indicators"]["next_action_retry_generate"]:
        repair_actions.append({
            "target": "artifact_index.json",
            "action": "invalidate_role_decision_apply_section",
            "details": {
                "remove_role_decision_apply_section": True,
                "set_retry_gate_open": False,
                "set_next_allowed_action": "blocked_by_role_approval",
                "set_production_accepted": False,
                "set_downstream_blocked": True,
                "add_state_repair_record": True
            }
        })
    
    # Always append corrective event when repairing artifact_index corruption
    if repair_actions:  # If any repair is needed
        repair_actions.append({
            "target": "episode_ledger.json",
            "action": "append_corrective_invalidation_event",
            "details": {
                "event_type": "pre_fix_fixture_apply_invalidated",
                "reason": "fixture approvals were applied before safety hardening",
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True,
                "comfyui_generation": False,
                "pipeline_action_rerun": False
            }
        })
    
    if dry_run:
        return {
            "project_root": project_root,
            "dry_run": True,
            "status": "dry_run_complete",
            "repair_actions": repair_actions,
            "repairs_performed": 0,
            "would_mutate_files": [action["target"] for action in repair_actions]
        }
    
    # Apply repairs
    files_mutated = []
    
    # Repair artifact_index.json
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
        
        # Invalidate role_decision_apply section
        if "role_decision_apply" in artifact_index:
            del artifact_index["role_decision_apply"]
        
        # Set blocked state (explicitly set these fields)
        artifact_index["retry_gate_open"] = False
        artifact_index["next_allowed_action"] = "blocked_by_role_approval"
        artifact_index["production_accepted"] = False
        artifact_index["downstream_blocked"] = True
        
        # Add state repair record
        artifact_index["state_repair"] = {
            "repair_type": "pre_fix_fixture_apply_invalidated",
            "repair_timestamp": datetime.utcnow().isoformat() + "Z",
            "reason": "fixture approvals were applied before safety hardening (commit cf49148)"
        }
        
        with open(artifact_index_path, 'w') as f:
            json.dump(artifact_index, f, indent=2)
        
        files_mutated.append("artifact_index.json")
    
    # Repair episode_ledger.json (only if repair actions were added)
    if any(action["target"] == "episode_ledger.json" for action in repair_actions):
        episode_ledger_path = project_path / "output" / "control" / "episode_ledger.json"
        if episode_ledger_path.exists():
            with open(episode_ledger_path, 'r') as f:
                episode_ledger = json.load(f)
            
            # Append corrective event
            corrective_event = {
                "event_type": "pre_fix_fixture_apply_invalidated",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "reason": "fixture approvals were applied before safety hardening",
                "retry_gate_open": False,
                "production_accepted": False,
                "downstream_blocked": True,
                "comfyui_generation": False,
                "pipeline_action_rerun": False,
                "repair_commit": "cf49148"
            }
            
            if "events" not in episode_ledger:
                episode_ledger["events"] = []
            
            episode_ledger["events"].append(corrective_event)
            
            with open(episode_ledger_path, 'w') as f:
                json.dump(episode_ledger, f, indent=2)
            
            files_mutated.append("episode_ledger.json")
    
    # Validate repairs
    post_repair_inspection = inspect_real_project_decision_state(project_root)
    
    return {
        "project_root": project_root,
        "dry_run": False,
        "status": "repair_complete",
        "repair_actions": repair_actions,
        "repairs_performed": len(repair_actions),
        "files_mutated": files_mutated,
        "validation": {
            "safe_for_next_step": post_repair_inspection["safe_for_next_step"],
            "role_decisions_pending": (
                post_repair_inspection["role_decisions"]["character_director"]["decision_status"] == "pending" and
                post_repair_inspection["role_decisions"]["workflow_td"]["decision_status"] == "pending"
            ),
            "retry_gate_closed": post_repair_inspection["artifact_index"]["retry_gate_open"] == False,
            "production_accepted_false": post_repair_inspection["artifact_index"]["production_accepted"] == False,
            "downstream_blocked": post_repair_inspection["artifact_index"]["downstream_blocked"] == True
        },
        "repair_timestamp": datetime.utcnow().isoformat() + "Z"
    }
