"""
Production Role Review Evidence Packets Module

Creates structured review evidence packets for Character Director and Workflow TD
so real role decisions can be made from complete project evidence, not from
fixture approvals or ad-hoc assumptions.

Evidence packets are NOT decisions - they are review evidence only.
They do NOT approve decisions, do NOT open retry gate, do NOT mark production_accepted=true.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_relevant_cards(project_root: str) -> Dict[str, Any]:
    """Load relevant cards for evidence packet generation."""
    cards_dir = Path(project_root) / "cards"
    cards = {}
    
    # Load shot cards
    shots_dir = cards_dir / "shots"
    if shots_dir.exists():
        for shot_file in shots_dir.glob("*.json"):
            with open(shot_file, 'r') as f:
                cards[shot_file.stem] = json.load(f)
    
    # Load character card
    character_file = cards_dir / "characters" / "character_card.json"
    if character_file.exists():
        with open(character_file, 'r') as f:
            cards["character_card"] = json.load(f)
    
    # Load workflow card
    workflow_file = cards_dir / "workflows" / "workflow_card.json"
    if workflow_file.exists():
        with open(workflow_file, 'r') as f:
            cards["workflow_card"] = json.load(f)
    
    return cards


def load_identity_failure_evidence(project_root: str) -> Dict[str, Any]:
    """Load identity QA failure evidence from project state."""
    project_path = Path(project_root)
    
    # Load artifact index to get failure summary
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    artifact_index = {}
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
    
    # Load shot cards to find blocked shot
    cards = load_relevant_cards(project_root)
    blocked_shot = None
    for shot_id, shot_card in cards.items():
        if shot_id != "character_card" and shot_id != "workflow_card":
            if shot_card.get("blocking_reason") == "identity_qa_failed":
                blocked_shot = shot_card
                break
    
    # Load work orders for pending decision paths
    work_orders_dir = project_path / "output" / "control" / "work_orders"
    char_work_order = {}
    workflow_work_order = {}
    
    char_order_path = work_orders_dir / "character_director_identity_review.json"
    if char_order_path.exists():
        with open(char_order_path, 'r') as f:
            char_work_order = json.load(f)
    
    workflow_order_path = work_orders_dir / "workflow_td_identity_workflow_review.json"
    if workflow_order_path.exists():
        with open(workflow_order_path, 'r') as f:
            workflow_work_order = json.load(f)
    
    # Load role decisions for pending decision paths
    role_decisions_dir = project_path / "output" / "control" / "role_decisions"
    char_decision = {}
    workflow_decision = {}
    
    char_decision_path = role_decisions_dir / "character_director_identity_decision.json"
    if char_decision_path.exists():
        with open(char_decision_path, 'r') as f:
            char_decision = json.load(f)
    
    workflow_decision_path = role_decisions_dir / "workflow_td_identity_workflow_decision.json"
    if workflow_decision_path.exists():
        with open(workflow_decision_path, 'r') as f:
            workflow_decision = json.load(f)
    
    return {
        "blocked_shot": blocked_shot,
        "artifact_index": artifact_index,
        "character_work_order": char_work_order,
        "workflow_work_order": workflow_work_order,
        "character_decision": char_decision,
        "workflow_decision": workflow_decision
    }


def create_character_director_review_packet(
    project_root: str,
    cards: Dict[str, Any],
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """Create Character Director evidence packet for identity review."""
    project_path = Path(project_root)
    
    # Extract character data from cards (preserve real project data)
    character_card = cards.get("character_card", {})
    character_name = character_card.get("name", "Unknown")
    character_reference = character_card.get("reference_character", "Unknown")
    
    # Extract blocked shot data
    blocked_shot = evidence["blocked_shot"]
    blocked_shot_id = blocked_shot.get("card_id", "shot01") if blocked_shot else "shot01"
    
    # Extract paths
    character_card_path = project_path / "cards" / "characters" / "character_card.json"
    shot_card_path = project_path / "cards" / "shots" / f"{blocked_shot_id}.json"
    work_order_path = project_path / "output" / "control" / "work_orders" / "character_director_identity_review.json"
    pending_decision_path = project_path / "output" / "control" / "role_decisions" / "character_director_identity_decision.json"
    
    # Build evidence packet
    packet = {
        "packet_type": "character_director_identity_review",
        "role": "Character Director",
        "blocked_shot": blocked_shot_id,
        "issue": "identity_qa_failed",
        "character_name": character_name,
        "character_reference": character_reference,
        "character_card_path": str(character_card_path.relative_to(project_path)),
        "shot_card_path": str(shot_card_path.relative_to(project_path)),
        "work_order_path": str(work_order_path.relative_to(project_path)),
        "pending_decision_path": str(pending_decision_path.relative_to(project_path)),
        "identity_qa_failure_summary": {
            "frame_qc_passed": blocked_shot.get("frame_qc_passed", True) if blocked_shot else True,
            "identity_consistency_passed": blocked_shot.get("identity_consistency_passed", False) if blocked_shot else False,
            "production_accepted": blocked_shot.get("production_accepted", False) if blocked_shot else False,
            "blocking_reason": blocked_shot.get("blocking_reason", "identity_qa_failed") if blocked_shot else "identity_qa_failed"
        },
        "required_review_questions": [
            "is the current character reference strategy sufficient?",
            "are identity rules complete?",
            "does the failed output drift from approved identity?",
            "should the role approve, reject, request_new_reference, or request_workflow_change?"
        ],
        "required_decision_output": "character_identity_approval or rejection/request",
        "downstream_blocked": True,
        "production_accepted": False,
        "evidence_only": True,
        "not_a_decision": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    
    return packet


def create_workflow_td_review_packet(
    project_root: str,
    cards: Dict[str, Any],
    evidence: Dict[str, Any]
) -> Dict[str, Any]:
    """Create Workflow TD evidence packet for identity workflow review."""
    project_path = Path(project_root)
    
    # Extract workflow data from cards (preserve real project data)
    workflow_card = cards.get("workflow_card", {})
    generation_mode = workflow_card.get("generation_mode", "gorynych_identity")
    legacy_reference_locked_allowed = workflow_card.get("legacy_reference_locked_allowed_for_production", False)
    
    # Extract blocked shot data
    blocked_shot = evidence["blocked_shot"]
    blocked_shot_id = blocked_shot.get("card_id", "shot01") if blocked_shot else "shot01"
    
    # Extract paths
    workflow_card_path = project_path / "cards" / "workflows" / "workflow_card.json"
    shot_card_path = project_path / "cards" / "shots" / f"{blocked_shot_id}.json"
    work_order_path = project_path / "output" / "control" / "work_orders" / "workflow_td_identity_workflow_review.json"
    pending_decision_path = project_path / "output" / "control" / "role_decisions" / "workflow_td_identity_workflow_decision.json"
    
    # Build evidence packet
    packet = {
        "packet_type": "workflow_td_identity_workflow_review",
        "role": "Workflow TD / ComfyUI Technical Director",
        "blocked_shot": blocked_shot_id,
        "issue": "identity_qa_failed",
        "workflow_card_path": str(workflow_card_path.relative_to(project_path)),
        "shot_card_path": str(shot_card_path.relative_to(project_path)),
        "work_order_path": str(work_order_path.relative_to(project_path)),
        "pending_decision_path": str(pending_decision_path.relative_to(project_path)),
        "current_required_generation_mode": generation_mode,
        "legacy_reference_locked_allowed_for_production": legacy_reference_locked_allowed,
        "known_workflow_requirements": {
            "required_nodes": ["IPAdapter", "ControlNet", "KSampler"],
            "required_models": ["character_reference_model", "identity_preservation_model"],
            "output_collection_contract": "frame_manifest.json"
        },
        "previous_failure_summary": {
            "generation_mode": generation_mode,
            "identity_consistency_passed": blocked_shot.get("identity_consistency_passed", False) if blocked_shot else False,
            "blocking_reason": blocked_shot.get("blocking_reason", "identity_qa_failed") if blocked_shot else "identity_qa_failed"
        },
        "required_review_questions": [
            "is gorynych_identity workflow fit for retry?",
            "are required nodes/models available?",
            "is output collection contract complete?",
            "should the role approve_workflow, reject_workflow, request_missing_nodes, request_missing_models, or request_reference_rebuild?"
        ],
        "required_decision_output": "workflow_fit_approval or rejection/request",
        "downstream_blocked": True,
        "production_accepted": False,
        "evidence_only": True,
        "not_a_decision": True,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_data_origin": "production_cards",
        "source_project_root": project_root
    }
    
    return packet


def update_artifact_index_for_review_packets(
    project_root: str,
    char_packet_path: Path,
    workflow_packet_path: Path
) -> None:
    """Update artifact_index.json with role review packet information."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add role_review_packets section
    artifact_index["role_review_packets"] = {
        "status": "created",
        "character_director_packet": str(char_packet_path.relative_to(Path(project_root))),
        "workflow_td_packet": str(workflow_packet_path.relative_to(Path(project_root))),
        "downstream_blocked": True,
        "production_accepted": False,
        "evidence_only": True
    }
    
    # Ensure downstream_blocked is true
    artifact_index["downstream_blocked"] = True
    artifact_index["production_accepted"] = False
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def update_episode_ledger_for_review_packets(project_root: str) -> None:
    """Update episode_ledger.json with role review packet creation event."""
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
    
    # Add role review packet creation event
    event = {
        "event_type": "role_review_packets_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roles": [
            "Character Director",
            "Workflow TD / ComfyUI Technical Director"
        ],
        "reason": "identity_qa_failed",
        "downstream_blocked": True,
        "production_accepted": False,
        "comfyui_generation": False,
        "pipeline_action_rerun": False,
        "evidence_only": True
    }
    
    ledger["events"].append(event)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)


def create_role_review_packets(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Create role review evidence packets for Character Director and Workflow TD.
    
    These packets are evidence for review, NOT decisions. They do NOT approve
    decisions, do NOT open retry gate, do NOT mark production_accepted=true.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with evidence packet creation results
    """
    project_path = Path(project_root)
    role_review_packets_dir = project_path / "output" / "control" / "role_review_packets"
    role_review_packets_dir.mkdir(parents=True, exist_ok=True)
    
    # Load project data
    cards = load_relevant_cards(project_root)
    evidence = load_identity_failure_evidence(project_root)
    
    # Create evidence packets
    character_director_packet = create_character_director_review_packet(
        project_root, cards, evidence
    )
    workflow_td_packet = create_workflow_td_review_packet(
        project_root, cards, evidence
    )
    
    # Save evidence packets
    char_packet_path = role_review_packets_dir / "character_director_identity_evidence_packet.json"
    workflow_packet_path = role_review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
    
    with open(char_packet_path, 'w') as f:
        json.dump(character_director_packet, f, indent=2)
    
    with open(workflow_packet_path, 'w') as f:
        json.dump(workflow_td_packet, f, indent=2)
    
    # Update artifact index and episode ledger
    update_artifact_index_for_review_packets(project_root, char_packet_path, workflow_packet_path)
    update_episode_ledger_for_review_packets(project_root)
    
    result = {
        "status": "completed",
        "project_root": project_root,
        "downstream_blocked": True,
        "production_accepted": False,
        "evidence_packets_created": 2,
        "evidence_only": True,
        "not_decisions": True,
        "packets": [
            {
                "role": character_director_packet["role"],
                "packet_path": str(char_packet_path),
                "packet_type": character_director_packet["packet_type"],
                "blocked_shot": character_director_packet["blocked_shot"]
            },
            {
                "role": workflow_td_packet["role"],
                "packet_path": str(workflow_packet_path),
                "packet_type": workflow_td_packet["packet_type"],
                "blocked_shot": workflow_td_packet["blocked_shot"]
            }
        ]
    }
    
    return result


def validate_role_review_packets(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Validate role review evidence packets and determine if decisions are ready.
    
    Evidence packets are NOT decisions, so decision_ready is always false
    until actual role decisions are made and applied.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with validation results
    """
    project_path = Path(project_root)
    role_review_packets_dir = project_path / "output" / "control" / "role_review_packets"
    
    # Check if evidence packets exist
    char_packet_path = role_review_packets_dir / "character_director_identity_evidence_packet.json"
    workflow_packet_path = role_review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
    
    packets_found = 0
    missing_required_evidence = []
    
    # Check Character Director packet
    if char_packet_path.exists():
        with open(char_packet_path, 'r') as f:
            char_packet = json.load(f)
        
        # Verify it's evidence only, not a decision
        if not char_packet.get("evidence_only"):
            missing_required_evidence.append("Character Director packet is not marked as evidence_only")
        if char_packet.get("production_accepted"):
            missing_required_evidence.append("Character Director packet incorrectly has production_accepted=true")
        
        packets_found += 1
    else:
        missing_required_evidence.append("character_director_identity_evidence_packet.json")
    
    # Check Workflow TD packet
    if workflow_packet_path.exists():
        with open(workflow_packet_path, 'r') as f:
            workflow_packet = json.load(f)
        
        # Verify it's evidence only, not a decision
        if not workflow_packet.get("evidence_only"):
            missing_required_evidence.append("Workflow TD packet is not marked as evidence_only")
        if workflow_packet.get("production_accepted"):
            missing_required_evidence.append("Workflow TD packet incorrectly has production_accepted=true")
        
        packets_found += 1
    else:
        missing_required_evidence.append("workflow_td_identity_workflow_evidence_packet.json")
    
    # Evidence packets are NOT decisions, so decision_ready is always false
    # until actual role decisions are made and applied
    decision_ready = False
    downstream_blocked = True
    production_accepted = False
    
    # Determine overall status
    status = "valid" if packets_found == 2 and not missing_required_evidence else "invalid"
    
    result = {
        "status": status,
        "packets_found": packets_found,
        "decision_ready": decision_ready,
        "downstream_blocked": downstream_blocked,
        "production_accepted": production_accepted,
        "missing_required_evidence": missing_required_evidence,
        "evidence_only": True,
        "not_decisions": True
    }
    
    return result
