"""
Production Role Decision Submission Contract Module

Creates strict submission contracts for real Character Director and Workflow TD decisions
based on evidence packets, without approving or applying any decisions yet.

Submission templates are NOT decisions - they are draft submission templates for real role input.
They do NOT approve decisions, do NOT open retry gate, do NOT mark production_accepted=true.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_evidence_packets(project_root: str) -> Dict[str, Any]:
    """Load evidence packets for submission contract generation."""
    project_path = Path(project_root)
    role_review_packets_dir = project_path / "output" / "control" / "role_review_packets"
    
    char_packet_path = role_review_packets_dir / "character_director_identity_evidence_packet.json"
    workflow_packet_path = role_review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json"
    
    char_packet = {}
    workflow_packet = {}
    
    if char_packet_path.exists():
        with open(char_packet_path, 'r') as f:
            char_packet = json.load(f)
    
    if workflow_packet_path.exists():
        with open(workflow_packet_path, 'r') as f:
            workflow_packet = json.load(f)
    
    return {
        "character_director_packet": char_packet,
        "workflow_td_packet": workflow_packet
    }


def load_work_orders(project_root: str) -> Dict[str, Any]:
    """Load work orders for submission contract generation."""
    project_path = Path(project_root)
    work_orders_dir = project_path / "output" / "control" / "work_orders"
    
    char_order_path = work_orders_dir / "character_director_identity_review.json"
    workflow_order_path = work_orders_dir / "workflow_td_identity_workflow_review.json"
    
    char_order = {}
    workflow_order = {}
    
    if char_order_path.exists():
        with open(char_order_path, 'r') as f:
            char_order = json.load(f)
    
    if workflow_order_path.exists():
        with open(workflow_order_path, 'r') as f:
            workflow_order = json.load(f)
    
    return {
        "character_director_work_order": char_order,
        "workflow_td_work_order": workflow_order
    }


def load_project_metadata(project_root: str) -> Dict[str, Any]:
    """Load project metadata for submission contract generation."""
    project_path = Path(project_root)
    
    # Load artifact index to get project metadata
    artifact_index_path = project_path / "output" / "control" / "artifact_index.json"
    artifact_index = {}
    if artifact_index_path.exists():
        with open(artifact_index_path, 'r') as f:
            artifact_index = json.load(f)
    
    # Extract project ID from project root
    project_id = Path(project_root).name
    
    return {
        "project_id": project_id,
        "artifact_index": artifact_index
    }


def create_character_director_submission_template(
    project_root: str,
    evidence_packets: Dict[str, Any],
    work_orders: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Create Character Director real decision submission template."""
    project_path = Path(project_root)
    char_packet = evidence_packets["character_director_packet"]
    char_order = work_orders["character_director_work_order"]
    project_id = metadata["project_id"]
    
    # Extract evidence packet path
    evidence_packet_path = project_path / "output" / "control" / "role_review_packets" / "character_director_identity_evidence_packet.json"
    work_order_path = project_path / "output" / "control" / "work_orders" / "character_director_identity_review.json"
    
    # Extract character data from evidence packet (preserve real project data)
    character_name = char_packet.get("character_name", "Unknown")
    blocked_shot = char_packet.get("blocked_shot", "shot01")
    
    # Build submission template
    template = {
        "role": "Character Director",
        "decision_source": "real_role_decision",
        "fixture_only": False,
        "approved_by_role": "Character Director",
        "approved_for_project_id": project_id,
        "approved_for_shot": blocked_shot,
        "character_name": character_name,
        "based_on_evidence_packet": str(evidence_packet_path.relative_to(project_path)),
        "based_on_work_order": str(work_order_path.relative_to(project_path)),
        "current_decision_status": "draft_submission",
        "allowed_decisions": [
            "approve",
            "reject",
            "request_new_reference",
            "request_workflow_change"
        ],
        "selected_decision": None,
        "required_artifacts": [
            "approved_character_identity_rules",
            "approved_reference_strategy",
            "identity_acceptance_criteria"
        ],
        "production_accepted": False,
        "downstream_blocked": True,
        "next_allowed_action_if_approved": "retry_generate_frames",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_project_root": project_root
    }
    
    return template


def create_workflow_td_submission_template(
    project_root: str,
    evidence_packets: Dict[str, Any],
    work_orders: Dict[str, Any],
    metadata: Dict[str, Any]
) -> Dict[str, Any]:
    """Create Workflow TD real decision submission template."""
    project_path = Path(project_root)
    workflow_packet = evidence_packets["workflow_td_packet"]
    workflow_order = work_orders["workflow_td_work_order"]
    project_id = metadata["project_id"]
    
    # Extract evidence packet path
    evidence_packet_path = project_path / "output" / "control" / "role_review_packets" / "workflow_td_identity_workflow_evidence_packet.json"
    work_order_path = project_path / "output" / "control" / "work_orders" / "workflow_td_identity_workflow_review.json"
    
    # Extract workflow data from evidence packet (preserve real project data)
    generation_mode = workflow_packet.get("current_required_generation_mode", "gorynych_identity")
    legacy_allowed = workflow_packet.get("legacy_reference_locked_allowed_for_production", False)
    blocked_shot = workflow_packet.get("blocked_shot", "shot01")
    
    # Build submission template
    template = {
        "role": "Workflow TD / ComfyUI Technical Director",
        "decision_source": "real_role_decision",
        "fixture_only": False,
        "approved_by_role": "Workflow TD / ComfyUI Technical Director",
        "approved_for_project_id": project_id,
        "approved_for_shot": blocked_shot,
        "current_required_generation_mode": generation_mode,
        "legacy_reference_locked_allowed_for_production": legacy_allowed,
        "based_on_evidence_packet": str(evidence_packet_path.relative_to(project_path)),
        "based_on_work_order": str(work_order_path.relative_to(project_path)),
        "current_decision_status": "draft_submission",
        "allowed_decisions": [
            "approve_workflow",
            "reject_workflow",
            "request_missing_nodes",
            "request_missing_models",
            "request_reference_rebuild"
        ],
        "selected_decision": None,
        "required_artifacts": [
            "workflow_audit",
            "required_nodes",
            "required_models",
            "preflight_result",
            "output_collection_contract"
        ],
        "production_accepted": False,
        "downstream_blocked": True,
        "next_allowed_action_if_approved": "retry_generate_frames",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "project_specific_data_allowed": True,
        "source_project_root": project_root
    }
    
    return template


def create_character_director_instructions(
    project_root: str,
    evidence_packets: Dict[str, Any]
) -> str:
    """Create Markdown instructions for Character Director decision submission."""
    char_packet = evidence_packets["character_director_packet"]
    character_name = char_packet.get("character_name", "Unknown")
    blocked_shot = char_packet.get("blocked_shot", "shot01")
    evidence_packet_path = char_packet.get("packet_type", "character_director_identity_review")
    
    instructions = f"""# Character Director Decision Submission Instructions

## Role
Character Director

## Purpose
Review evidence packet and submit real decision for identity QA failure on {blocked_shot}.

## Evidence Packet to Review
- File: `output/control/role_review_packets/character_director_identity_evidence_packet.json`
- Type: {evidence_packet_path}
- Character: {character_name}
- Issue: identity_qa_failed

## Allowed Decisions
- **approve**: Approve character identity strategy for retry
- **reject**: Reject current character identity strategy
- **request_new_reference**: Request new character reference
- **request_workflow_change**: Request workflow changes

## Required Artifacts
Before submitting your decision, ensure you have reviewed:
- Approved character identity rules
- Approved reference strategy
- Identity acceptance criteria

## What Must Not Be Changed
- **DO NOT** modify `production_accepted` (must remain false)
- **DO NOT** modify `downstream_blocked` (must remain true)
- **DO NOT** open retry gate (this is handled by decision intake/apply)
- **DO NOT** approve automatically (this is a manual role decision)

## Submission Process
1. Review the evidence packet at `output/control/role_review_packets/character_director_identity_evidence_packet.json`
2. Review the work order at `output/control/work_orders/character_director_identity_review.json`
3. Make your decision based on the evidence
4. Fill in the `selected_decision` field in `output/control/role_decision_submissions/character_director_real_decision.SUBMIT.json`
5. Add any required artifacts to your decision
6. Submit for validation

## Important Notes
- This is a **real role decision submission**, not a fixture
- Your decision will be validated before being applied
- Approval opens retry gate for frame generation, but does not mark production_accepted=true
- production_accepted=true is only set after successful frame generation passes identity QA
- Downstream remains blocked until your decision is validated and applied
"""
    return instructions


def create_workflow_td_instructions(
    project_root: str,
    evidence_packets: Dict[str, Any]
) -> str:
    """Create Markdown instructions for Workflow TD decision submission."""
    workflow_packet = evidence_packets["workflow_td_packet"]
    generation_mode = workflow_packet.get("current_required_generation_mode", "gorynych_identity")
    blocked_shot = workflow_packet.get("blocked_shot", "shot01")
    evidence_packet_path = workflow_packet.get("packet_type", "workflow_td_identity_workflow_review")
    
    instructions = f"""# Workflow TD Decision Submission Instructions

## Role
Workflow TD / ComfyUI Technical Director

## Purpose
Review evidence packet and submit real decision for identity workflow failure on {blocked_shot}.

## Evidence Packet to Review
- File: `output/control/role_review_packets/workflow_td_identity_workflow_evidence_packet.json`
- Type: {evidence_packet_path}
- Generation Mode: {generation_mode}
- Issue: identity_qa_failed

## Allowed Decisions
- **approve_workflow**: Approve workflow for retry
- **reject_workflow**: Reject current workflow
- **request_missing_nodes**: Request missing ComfyUI nodes
- **request_missing_models**: Request missing models
- **request_reference_rebuild**: Request reference rebuild

## Required Artifacts
Before submitting your decision, ensure you have reviewed:
- Workflow audit
- Required nodes (IPAdapter, ControlNet, KSampler)
- Required models (character_reference_model, identity_preservation_model)
- Preflight result
- Output collection contract (frame_manifest.json)

## What Must Not Be Changed
- **DO NOT** modify `production_accepted` (must remain false)
- **DO NOT** modify `downstream_blocked` (must remain true)
- **DO NOT** open retry gate (this is handled by decision intake/apply)
- **DO NOT** approve automatically (this is a manual role decision)
- **DO NOT** allow legacy reference_locked for production (must remain false)

## Submission Process
1. Review the evidence packet at `output/control/role_review_packets/workflow_td_identity_workflow_evidence_packet.json`
2. Review the work order at `output/control/workflows/workflow_td_identity_workflow_review.json`
3. Make your decision based on the evidence
4. Fill in the `selected_decision` field in `output/control/role_decision_submissions/workflow_td_real_decision.SUBMIT.json`
5. Add any required artifacts to your decision
6. Submit for validation

## Important Notes
- This is a **real role decision submission**, not a fixture
- Your decision will be validated before being applied
- Approval opens retry gate for frame generation, but does not mark production_accepted=true
- production_accepted=true is only set after successful frame generation passes identity QA
- Downstream remains blocked until your decision is validated and applied
- Legacy reference_locked workflow is not allowed for production
"""
    return instructions


def update_artifact_index_for_submission_contract(
    project_root: str,
    char_template_path: Path,
    workflow_template_path: Path
) -> None:
    """Update artifact_index.json with decision submission contract information."""
    artifact_index_path = Path(project_root) / "output" / "control" / "artifact_index.json"
    
    if not artifact_index_path.exists():
        return
    
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    # Add role_decision_submission_contract section
    artifact_index["role_decision_submission_contract"] = {
        "status": "created",
        "character_director_submission_template": str(char_template_path.relative_to(Path(project_root))),
        "workflow_td_submission_template": str(workflow_template_path.relative_to(Path(project_root))),
        "downstream_blocked": True,
        "production_accepted": False,
        "retry_gate_open": False
    }
    
    # Ensure downstream_blocked is true
    artifact_index["downstream_blocked"] = True
    artifact_index["production_accepted"] = False
    artifact_index["retry_gate_open"] = False
    
    with open(artifact_index_path, 'w') as f:
        json.dump(artifact_index, f, indent=2)


def update_episode_ledger_for_submission_contract(project_root: str) -> None:
    """Update episode_ledger.json with decision submission contract creation event."""
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
    
    # Add decision submission contract creation event
    event = {
        "event_type": "role_decision_submission_contract_created",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "roles": [
            "Character Director",
            "Workflow TD / ComfyUI Technical Director"
        ],
        "reason": "identity_qa_failed",
        "downstream_blocked": True,
        "production_accepted": False,
        "retry_gate_open": False,
        "comfyui_generation": False,
        "pipeline_action_rerun": False
    }
    
    ledger["events"].append(event)
    
    with open(ledger_path, 'w') as f:
        json.dump(ledger, f, indent=2)


def create_decision_submission_contract(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Create decision submission contract for Character Director and Workflow TD.
    
    These templates are draft submission templates for real role input, NOT decisions.
    They do NOT approve decisions, do NOT open retry gate, do NOT mark production_accepted=true.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with submission contract creation results
    """
    project_path = Path(project_root)
    role_decision_submissions_dir = project_path / "output" / "control" / "role_decision_submissions"
    role_decision_submissions_dir.mkdir(parents=True, exist_ok=True)
    
    # Load project data
    evidence_packets = load_evidence_packets(project_root)
    work_orders = load_work_orders(project_root)
    metadata = load_project_metadata(project_root)
    
    # Create submission templates
    character_director_template = create_character_director_submission_template(
        project_root, evidence_packets, work_orders, metadata
    )
    workflow_td_template = create_workflow_td_submission_template(
        project_root, evidence_packets, work_orders, metadata
    )
    
    # Save submission templates
    char_template_path = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
    workflow_template_path = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
    
    with open(char_template_path, 'w') as f:
        json.dump(character_director_template, f, indent=2)
    
    with open(workflow_template_path, 'w') as f:
        json.dump(workflow_td_template, f, indent=2)
    
    # Create Markdown instructions
    char_instructions = create_character_director_instructions(project_root, evidence_packets)
    workflow_instructions = create_workflow_td_instructions(project_root, evidence_packets)
    
    char_instructions_path = role_decision_submissions_dir / "CHARACTER_DIRECTOR_DECISION_INSTRUCTIONS.md"
    workflow_instructions_path = role_decision_submissions_dir / "WORKFLOW_TD_DECISION_INSTRUCTIONS.md"
    
    with open(char_instructions_path, 'w') as f:
        f.write(char_instructions)
    
    with open(workflow_instructions_path, 'w') as f:
        f.write(workflow_instructions)
    
    # Update artifact index and episode ledger
    update_artifact_index_for_submission_contract(project_root, char_template_path, workflow_template_path)
    update_episode_ledger_for_submission_contract(project_root)
    
    result = {
        "status": "completed",
        "project_root": project_root,
        "downstream_blocked": True,
        "production_accepted": False,
        "retry_gate_open": False,
        "submission_templates_created": 2,
        "ready_for_real_role_input": True,
        "decision_ready": False,
        "templates": [
            {
                "role": character_director_template["role"],
                "template_path": str(char_template_path),
                "decision_source": character_director_template["decision_source"],
                "fixture_only": character_director_template["fixture_only"],
                "approved_for_shot": character_director_template["approved_for_shot"]
            },
            {
                "role": workflow_td_template["role"],
                "template_path": str(workflow_template_path),
                "decision_source": workflow_td_template["decision_source"],
                "fixture_only": workflow_td_template["fixture_only"],
                "approved_for_shot": workflow_td_template["approved_for_shot"]
            }
        ],
        "instructions": [
            {
                "role": "Character Director",
                "instructions_path": str(char_instructions_path)
            },
            {
                "role": "Workflow TD / ComfyUI Technical Director",
                "instructions_path": str(workflow_instructions_path)
            }
        ]
    }
    
    return result


def validate_decision_submission_contract(project_root: str, json_output: bool = False) -> Dict[str, Any]:
    """
    Validate decision submission contract and determine if ready for real role input.
    
    Templates are draft submissions, not submitted decisions, so decision_ready is always false.
    ready_for_real_role_input is true if templates exist and are properly configured.
    
    Args:
        project_root: Path to the project root
        json_output: Whether to return JSON-compatible output
    
    Returns:
        Dictionary with validation results
    """
    project_path = Path(project_root)
    role_decision_submissions_dir = project_path / "output" / "control" / "role_decision_submissions"
    
    # Check if submission templates exist
    char_template_path = role_decision_submissions_dir / "character_director_real_decision.SUBMIT.json"
    workflow_template_path = role_decision_submissions_dir / "workflow_td_real_decision.SUBMIT.json"
    
    submission_templates_found = 0
    validation_errors = []
    
    # Check Character Director template
    if char_template_path.exists():
        with open(char_template_path, 'r') as f:
            char_template = json.load(f)
        
        # Verify it's a real decision submission, not a fixture
        if char_template.get("fixture_only"):
            validation_errors.append("Character Director template is marked as fixture_only")
        if char_template.get("decision_source") != "real_role_decision":
            validation_errors.append("Character Director template does not have decision_source=real_role_decision")
        if char_template.get("selected_decision") is not None:
            validation_errors.append("Character Director template has selected_decision filled (should be null)")
        if char_template.get("production_accepted"):
            validation_errors.append("Character Director template incorrectly has production_accepted=true")
        
        submission_templates_found += 1
    else:
        validation_errors.append("character_director_real_decision.SUBMIT.json")
    
    # Check Workflow TD template
    if workflow_template_path.exists():
        with open(workflow_template_path, 'r') as f:
            workflow_template = json.load(f)
        
        # Verify it's a real decision submission, not a fixture
        if workflow_template.get("fixture_only"):
            validation_errors.append("Workflow TD template is marked as fixture_only")
        if workflow_template.get("decision_source") != "real_role_decision":
            validation_errors.append("Workflow TD template does not have decision_source=real_role_decision")
        if workflow_template.get("selected_decision") is not None:
            validation_errors.append("Workflow TD template has selected_decision filled (should be null)")
        if workflow_template.get("production_accepted"):
            validation_errors.append("Workflow TD template incorrectly has production_accepted=true")
        
        submission_templates_found += 1
    else:
        validation_errors.append("workflow_td_real_decision.SUBMIT.json")
    
    # Templates are draft submissions, not submitted decisions, so decision_ready is always false
    decision_ready = False
    ready_for_real_role_input = submission_templates_found == 2 and not validation_errors
    downstream_blocked = True
    production_accepted = False
    retry_gate_open = False
    
    # Determine overall status
    status = "valid" if submission_templates_found == 2 and not validation_errors else "invalid"
    
    result = {
        "status": status,
        "submission_templates_found": submission_templates_found,
        "ready_for_real_role_input": ready_for_real_role_input,
        "decision_ready": decision_ready,
        "retry_gate_open": retry_gate_open,
        "downstream_blocked": downstream_blocked,
        "production_accepted": production_accepted,
        "validation_errors": validation_errors
    }
    
    return result
