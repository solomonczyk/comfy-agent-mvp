"""
RC2-PRODCARDS2X — Completion-Based Role Decision Resubmission Pack, No Apply

This module creates role decision resubmission packets based on validated submitted
change request completions, without applying decisions, opening retry gate, or running
generation.

The resubmission packets incorporate evidence outputs from the change request completions
to provide updated context for role decisions, while maintaining all boundary conditions:
- No apply performed
- No retry gate opened
- No generation executed
- No downstream actions executed
- role_decisions remain pending
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


def load_submitted_completions(project_root: str) -> Dict[str, Any]:
    """Load submitted change request completions."""
    submitted_dir = Path(project_root) / "output" / "control" / "change_request_completions" / "submitted"
    
    completions = {}
    
    # Load Workflow TD submitted completion
    workflow_td_file = submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json"
    if workflow_td_file.exists():
        with open(workflow_td_file, 'r') as f:
            completions["workflow_td"] = json.load(f)
    
    # Load Character Director submitted completion
    character_director_file = submitted_dir / "character_director_reference_rebuild.SUBMITTED.json"
    if character_director_file.exists():
        with open(character_director_file, 'r') as f:
            completions["character_director"] = json.load(f)
    
    return completions


def load_role_review_packets(project_root: str) -> Dict[str, Any]:
    """Load original role review packets."""
    packets_dir = Path(project_root) / "output" / "control" / "role_review_packets"
    
    packets = {}
    
    # Load Character Director review packet
    character_packet_file = packets_dir / "character_director_identity_evidence_packet.json"
    if character_packet_file.exists():
        with open(character_packet_file, 'r') as f:
            packets["character_director"] = json.load(f)
    
    # Load Workflow TD review packet
    workflow_packet_file = packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
    if workflow_packet_file.exists():
        with open(workflow_packet_file, 'r') as f:
            packets["workflow_td"] = json.load(f)
    
    return packets


def load_submission_templates(project_root: str) -> Dict[str, Any]:
    """Load original role decision submission templates."""
    submissions_dir = Path(project_root) / "output" / "control" / "role_decision_submissions"
    
    templates = {}
    
    # Load Character Director submission template
    character_template_file = submissions_dir / "character_director_real_decision.SUBMIT.json"
    if character_template_file.exists():
        with open(character_template_file, 'r') as f:
            templates["character_director"] = json.load(f)
    
    # Load Workflow TD submission template
    workflow_template_file = submissions_dir / "workflow_td_real_decision.SUBMIT.json"
    if workflow_template_file.exists():
        with open(workflow_template_file, 'r') as f:
            templates["workflow_td"] = json.load(f)
    
    return templates


def create_character_director_resubmission_packet(
    submitted_completion: Dict[str, Any],
    review_packet: Dict[str, Any],
    submission_template: Dict[str, Any],
    project_root: str
) -> Dict[str, Any]:
    """Create Character Director resubmission packet based on submitted completion."""
    
    # Extract evidence outputs from submitted completion
    evidence_outputs = submitted_completion.get("outputs_provided", {})
    
    # Build resubmission packet
    packet = {
        "packet_type": "character_director_resubmission",
        "role": "Character Director",
        "decision_source": "completion_based_resubmission",
        "blocked_shot": submitted_completion.get("blocked_shot"),
        "character_name": review_packet.get("character_name"),
        "character_reference": review_packet.get("character_reference"),
        "based_on_submitted_completion": "output/control/change_request_completions/submitted/character_director_reference_rebuild.SUBMITTED.json",
        "based_on_review_packet": review_packet.get("based_on_evidence_packet"),
        "based_on_submission_template": "output/control/role_decision_submissions/character_director_real_decision.SUBMIT.json",
        "current_decision_status": "pending_resubmission",
        "allowed_decisions": submission_template.get("allowed_decisions"),
        "selected_decision": None,
        "completion_evidence": {
            "updated_character_identity_rules": submitted_completion.get("updated_character_identity_rules"),
            "updated_reference_strategy": submitted_completion.get("updated_reference_strategy"),
            "identity_acceptance_criteria": submitted_completion.get("identity_acceptance_criteria"),
            "reference_rebuild_notes": submitted_completion.get("reference_rebuild_notes")
        },
        "required_artifacts": submission_template.get("required_artifacts"),
        "production_accepted": False,
        "downstream_blocked": True,
        "apply_performed": False,
        "retry_gate_open": False,
        "ready_for_resubmission": True,
        "next_allowed_action_if_approved": "retry_generate_frames",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_project_root": project_root,
        "source_data_origin": "production_cards_completion_based_resubmission"
    }
    
    return packet


def create_workflow_td_resubmission_packet(
    submitted_completion: Dict[str, Any],
    review_packet: Dict[str, Any],
    submission_template: Dict[str, Any],
    project_root: str
) -> Dict[str, Any]:
    """Create Workflow TD resubmission packet based on submitted completion."""
    
    # Build resubmission packet
    packet = {
        "packet_type": "workflow_td_resubmission",
        "role": "Workflow TD / ComfyUI Technical Director",
        "decision_source": "completion_based_resubmission",
        "blocked_shot": submitted_completion.get("blocked_shot"),
        "current_required_generation_mode": submitted_completion.get("current_required_generation_mode"),
        "legacy_reference_locked_allowed_for_production": submitted_completion.get("legacy_reference_locked_allowed_for_production"),
        "based_on_submitted_completion": "output/control/change_request_completions/submitted/workflow_td_identity_workflow_change.SUBMITTED.json",
        "based_on_review_packet": review_packet.get("based_on_evidence_packet"),
        "based_on_submission_template": "output/control/role_decision_submissions/workflow_td_real_decision.SUBMIT.json",
        "current_decision_status": "pending_resubmission",
        "allowed_decisions": submission_template.get("allowed_decisions"),
        "selected_decision": None,
        "completion_evidence": {
            "updated_workflow_strategy": submitted_completion.get("updated_workflow_strategy"),
            "workflow_audit": submitted_completion.get("workflow_audit"),
            "required_nodes": submitted_completion.get("required_nodes"),
            "required_models": submitted_completion.get("required_models"),
            "preflight_result": submitted_completion.get("preflight_result"),
            "output_collection_contract": submitted_completion.get("output_collection_contract")
        },
        "required_artifacts": submission_template.get("required_artifacts"),
        "production_accepted": False,
        "downstream_blocked": True,
        "apply_performed": False,
        "retry_gate_open": False,
        "ready_for_resubmission": True,
        "next_allowed_action_if_approved": "retry_generate_frames",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_project_root": project_root,
        "source_data_origin": "production_cards_completion_based_resubmission"
    }
    
    return packet


def create_role_decision_resubmission_summary(
    submitted_completions: Dict[str, Any],
    resubmission_packets: Dict[str, Any],
    project_root: str
) -> Dict[str, Any]:
    """Create resubmission summary."""
    
    summary = {
        "resubmission_type": "completion_based_role_decision_resubmission",
        "project_root": project_root,
        "based_on_valid_completions": True,
        "completions_used": list(submitted_completions.keys()),
        "resubmission_packets_created": len(resubmission_packets),
        "resubmission_packet_files": [
            f"output/control/role_decision_resubmissions/{key}_resubmission_packet.json"
            for key in resubmission_packets.keys()
        ],
        "ready_for_role_resubmission": True,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "boundary_conditions": {
            "no_comfyui_execution": True,
            "no_frame_generation": True,
            "no_tts_execution": True,
            "no_ffmpeg_execution": True,
            "no_scene_assembly": True,
            "no_qa_review_execution": True,
            "no_apply_decisions": True,
            "no_role_decisions_modified": True,
            "no_retry_gate_opened": True,
            "no_production_accepted": True,
            "no_downstream_actions_executed": True
        },
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    
    return summary


def create_role_decision_resubmission_pack(project_root: str) -> Dict[str, Any]:
    """Create role decision resubmission pack from validated submitted completions.
    
    This function creates resubmission packets for Character Director and Workflow TD
    based on validated submitted change request completions, incorporating evidence outputs
    to provide updated context for role decisions.
    
    Args:
        project_root: Path to the project root directory.
        
    Returns:
        Dictionary containing the resubmission pack creation result.
    """
    # Load submitted completions
    submitted_completions = load_submitted_completions(project_root)
    
    if len(submitted_completions) == 0:
        return {
            "status": "failed",
            "error": "No submitted completions found",
            "resubmission_packets_created": 0,
            "based_on_valid_completions": False
        }
    
    # Load role review packets
    review_packets = load_role_review_packets(project_root)
    
    # Load submission templates
    submission_templates = load_submission_templates(project_root)
    
    # Create resubmission directory
    resubmission_dir = Path(project_root) / "output" / "control" / "role_decision_resubmissions"
    resubmission_dir.mkdir(parents=True, exist_ok=True)
    
    # Create resubmission packets
    resubmission_packets = {}
    
    # Character Director resubmission packet
    if "character_director" in submitted_completions and "character_director" in review_packets and "character_director" in submission_templates:
        character_packet = create_character_director_resubmission_packet(
            submitted_completions["character_director"],
            review_packets["character_director"],
            submission_templates["character_director"],
            project_root
        )
        
        character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
        with open(character_packet_file, 'w') as f:
            json.dump(character_packet, f, indent=2)
        
        resubmission_packets["character_director"] = character_packet
    
    # Workflow TD resubmission packet
    if "workflow_td" in submitted_completions and "workflow_td" in review_packets and "workflow_td" in submission_templates:
        workflow_packet = create_workflow_td_resubmission_packet(
            submitted_completions["workflow_td"],
            review_packets["workflow_td"],
            submission_templates["workflow_td"],
            project_root
        )
        
        workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
        with open(workflow_packet_file, 'w') as f:
            json.dump(workflow_packet, f, indent=2)
        
        resubmission_packets["workflow_td"] = workflow_packet
    
    # Create resubmission summary
    summary = create_role_decision_resubmission_summary(
        submitted_completions,
        resubmission_packets,
        project_root
    )
    
    # Write summary markdown
    summary_file = resubmission_dir / "ROLE_DECISION_RESUBMISSION_SUMMARY.md"
    with open(summary_file, 'w') as f:
        f.write("# Role Decision Resubmission Summary\n\n")
        f.write(f"**Resubmission Type**: Completion-based role decision resubmission\n\n")
        f.write(f"**Project Root**: {project_root}\n\n")
        f.write(f"**Created At**: {summary['created_at']}\n\n")
        f.write(f"**Completions Used**: {', '.join(summary['completions_used'])}\n\n")
        f.write(f"**Resubmission Packets Created**: {summary['resubmission_packets_created']}\n\n")
        f.write("## Resubmission Packet Files\n\n")
        for packet_file in summary['resubmission_packet_files']:
            f.write(f"- {packet_file}\n")
        f.write("\n")
        f.write("## Boundary Conditions\n\n")
        f.write("- No ComfyUI execution\n")
        f.write("- No frame generation\n")
        f.write("- No TTS execution\n")
        f.write("- No ffmpeg execution\n")
        f.write("- No scene assembly\n")
        f.write("- No QA review execution\n")
        f.write("- No apply decisions\n")
        f.write("- No role_decisions modified\n")
        f.write("- No retry gate opened\n")
        f.write("- No production_accepted\n")
        f.write("- No downstream actions executed\n\n")
        f.write("## Status\n\n")
        f.write(f"- **Ready for Role Resubmission**: {summary['ready_for_role_resubmission']}\n")
        f.write(f"- **Apply Performed**: {summary['apply_performed']}\n")
        f.write(f"- **Retry Gate Open**: {summary['retry_gate_open']}\n")
        f.write(f"- **Production Accepted**: {summary['production_accepted']}\n")
        f.write(f"- **Downstream Blocked**: {summary['downstream_blocked']}\n")
    
    # Write summary JSON
    summary_json_file = resubmission_dir / "RESUBMISSION_SUMMARY.json"
    with open(summary_json_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return {
        "status": "completed",
        "resubmission_packets_created": len(resubmission_packets),
        "based_on_valid_completions": True,
        "ready_for_role_resubmission": True,
        "apply_performed": False,
        "retry_gate_open": False,
        "production_accepted": False,
        "downstream_blocked": True,
        "resubmission_path": str(resubmission_dir)
    }
