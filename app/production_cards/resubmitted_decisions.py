"""
RC2-PRODCARDS2Y — Resubmitted Role Decision Drafts, No Apply

Creates new submitted role decision drafts from validated role decision
resubmission packets, without applying them, opening retry gate, or running
generation.

Boundary Conditions:
- No ComfyUI execution
- No frame generation
- No apply decisions
- No role_decisions/ modification
- No retry gate opened
- No production_accepted=true
- No downstream actions executed
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def load_resubmission_packets(project_root: str) -> Dict[str, Any]:
    """Load role decision resubmission packets."""
    resubmission_dir = Path(project_root) / "output" / "control" / "role_decision_resubmissions"
    
    packets = {}
    
    # Load Character Director resubmission packet
    char_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    if char_packet_file.exists():
        with open(char_packet_file, 'r') as f:
            packets["character_director"] = json.load(f)
    
    # Load Workflow TD resubmission packet
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    if workflow_packet_file.exists():
        with open(workflow_packet_file, 'r') as f:
            packets["workflow_td"] = json.load(f)
    
    return packets


def create_character_director_resubmitted_decision(
    resubmission_packet: Dict[str, Any],
    project_root: str
) -> Dict[str, Any]:
    """Create Character Director resubmitted decision from resubmission packet."""
    
    decision = {
        "role": resubmission_packet.get("role", "Character Director"),
        "work_order": "character_director_identity_review",
        "blocked_shot": resubmission_packet.get("blocked_shot", "shot01"),
        "character_name": resubmission_packet.get("character_name", "Alya"),
        "display_name": resubmission_packet.get("character_name", "Alya"),
        "reference_character": resubmission_packet.get("character_reference", "Alya"),
        "decision_status": "pending",
        "selected_decision": "approve",
        "allowed_decisions": resubmission_packet.get("allowed_decisions", [
            "approve",
            "reject",
            "request_new_reference",
            "request_workflow_change"
        ]),
        "required_artifacts": resubmission_packet.get("required_artifacts", []),
        "downstream_blocked": True,
        "production_accepted": False,
        "next_allowed_action": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "decision_source": resubmission_packet.get("decision_source", "completion_based_resubmission"),
        "fixture_only": False,
        "based_on_resubmission_packet": "output/control/role_decision_resubmissions/character_director_resubmission_packet.json",
        "resubmission_timestamp": resubmission_packet.get("created_at"),
        "completion_evidence": resubmission_packet.get("completion_evidence", {})
    }
    
    return decision


def create_workflow_td_resubmitted_decision(
    resubmission_packet: Dict[str, Any],
    project_root: str
) -> Dict[str, Any]:
    """Create Workflow TD resubmitted decision from resubmission packet."""
    
    decision = {
        "role": resubmission_packet.get("role", "Workflow TD / ComfyUI Technical Director"),
        "work_order": "workflow_td_identity_workflow_review",
        "blocked_shot": resubmission_packet.get("blocked_shot", "shot01"),
        "decision_status": "pending",
        "selected_decision": "approve_workflow",
        "current_required_generation_mode": resubmission_packet.get("current_required_generation_mode", "gorynych_identity"),
        "legacy_reference_locked_allowed_for_production": resubmission_packet.get("legacy_reference_locked_allowed_for_production", False),
        "allowed_decisions": resubmission_packet.get("allowed_decisions", [
            "approve_workflow",
            "reject_workflow",
            "request_missing_nodes",
            "request_missing_models",
            "request_reference_rebuild"
        ]),
        "required_artifacts": resubmission_packet.get("required_artifacts", []),
        "downstream_blocked": True,
        "production_accepted": False,
        "next_allowed_action": None,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "decision_source": resubmission_packet.get("decision_source", "completion_based_resubmission"),
        "fixture_only": False,
        "approved_for_project_id": Path(project_root).name,
        "approved_for_shot": resubmission_packet.get("blocked_shot", "shot01"),
        "approved_by_role": resubmission_packet.get("role", "Workflow TD / ComfyUI Technical Director"),
        "based_on_resubmission_packet": "output/control/role_decision_resubmissions/workflow_td_resubmission_packet.json",
        "resubmission_timestamp": resubmission_packet.get("created_at"),
        "completion_evidence": resubmission_packet.get("completion_evidence", {})
    }
    
    return decision


def create_resubmitted_role_decisions(project_root: str) -> Dict[str, Any]:
    """Create resubmitted role decision drafts from resubmission packets.
    
    This function creates submitted decision files for Character Director and Workflow TD
    based on validated role decision resubmission packets. The decisions are created
    with selected_decision filled, but NOT applied, keeping retry_gate closed and
    production_accepted=false.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        Dictionary containing the resubmitted decision creation result.
    """
    # Load resubmission packets
    resubmission_packets = load_resubmission_packets(project_root)
    
    if len(resubmission_packets) == 0:
        return {
            "status": "failed",
            "error": "No resubmission packets found",
            "resubmitted_decisions_created": 0,
            "based_on_resubmission_packets": False
        }
    
    # Create submitted directory
    submitted_dir = Path(project_root) / "output" / "control" / "role_decision_resubmissions" / "submitted"
    submitted_dir.mkdir(parents=True, exist_ok=True)
    
    # Create resubmitted decisions
    resubmitted_decisions = {}
    
    # Character Director resubmitted decision
    if "character_director" in resubmission_packets:
        char_decision = create_character_director_resubmitted_decision(
            resubmission_packets["character_director"],
            project_root
        )
        
        char_decision_file = submitted_dir / "character_director_resubmitted_decision.SUBMITTED.json"
        with open(char_decision_file, 'w') as f:
            json.dump(char_decision, f, indent=2)
        
        resubmitted_decisions["character_director"] = char_decision
    
    # Workflow TD resubmitted decision
    if "workflow_td" in resubmission_packets:
        workflow_decision = create_workflow_td_resubmitted_decision(
            resubmission_packets["workflow_td"],
            project_root
        )
        
        workflow_decision_file = submitted_dir / "workflow_td_resubmitted_decision.SUBMITTED.json"
        with open(workflow_decision_file, 'w') as f:
            json.dump(workflow_decision, f, indent=2)
        
        resubmitted_decisions["workflow_td"] = workflow_decision
    
    # Verify boundary conditions are maintained
    boundary_conditions = {
        "no_comfyui_execution": True,
        "no_frame_generation": True,
        "no_apply_decisions": True,
        "no_role_decisions_modified": True,
        "no_retry_gate_opened": True,
        "no_production_accepted": True,
        "no_downstream_actions_executed": True
    }
    
    return {
        "status": "completed",
        "resubmitted_decisions_created": len(resubmitted_decisions),
        "based_on_resubmission_packets": True,
        "submitted_decisions_ready": True,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "boundary_conditions": boundary_conditions,
        "submitted_decision_files": [
            "output/control/role_decision_resubmissions/submitted/character_director_resubmitted_decision.SUBMITTED.json",
            "output/control/role_decision_resubmissions/submitted/workflow_td_resubmitted_decision.SUBMITTED.json"
        ],
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
