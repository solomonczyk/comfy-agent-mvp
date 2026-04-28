"""
Test role decision resubmission pack creation.

Tests the create_role_decision_resubmission_pack function to ensure:
- Resubmission packets are created from submitted completions
- Packets include evidence outputs from completions
- Packets are based on original review packets and submission templates
- Packets validate correctly
- ready_for_role_resubmission=true
- apply_performed=false
- retry_gate_open=false
- production_accepted=false
- downstream_blocked=true
- No apply/generation/downstream action executes
"""

import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from app.production_cards.role_decision_resubmission import (
    create_role_decision_resubmission_pack,
    load_submitted_completions,
    load_role_review_packets,
    load_submission_templates
)


@pytest.fixture
def sample_project_root():
    """Create a temporary project root with submitted completions, review packets, and submission templates."""
    with TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        
        # Create directory structure
        submitted_dir = project_root / "output" / "control" / "change_request_completions" / "submitted"
        review_packets_dir = project_root / "output" / "control" / "role_review_packets"
        submissions_dir = project_root / "output" / "control" / "role_decision_submissions"
        
        submitted_dir.mkdir(parents=True, exist_ok=True)
        review_packets_dir.mkdir(parents=True, exist_ok=True)
        submissions_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Workflow TD submitted completion
        workflow_completion = {
            "completion_type": "workflow_change_completion",
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "completion_status": "submitted",
            "execution_performed": True,
            "selected_resolution": "workflow_strategy_updated",
            "current_required_generation_mode": "gorynych_identity",
            "legacy_reference_locked_allowed_for_production": False,
            "updated_workflow_strategy": {
                "strategy_type": "gorynych_identity",
                "identity_preservation": "enabled"
            },
            "workflow_audit": {
                "audit_status": "complete",
                "nodes_verified": True
            },
            "required_nodes": {
                "nodes": ["KSampler", "VAEDecode"],
                "all_present": True
            },
            "required_models": {
                "models": ["gorynych_identity_v1"],
                "all_present": True
            },
            "preflight_result": {
                "preflight_status": "passed"
            },
            "output_collection_contract": {
                "collection_mode": "identity_preserved"
            },
            "ready_for_resubmission": True,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submitted_dir / "workflow_td_identity_workflow_change.SUBMITTED.json", 'w') as f:
            json.dump(workflow_completion, f, indent=2)
        
        # Create Character Director submitted completion
        character_completion = {
            "completion_type": "reference_rebuild_completion",
            "role": "Character Director",
            "blocked_shot": "shot01",
            "completion_status": "submitted",
            "execution_performed": True,
            "selected_resolution": "reference_strategy_updated",
            "updated_character_identity_rules": {
                "identity_preservation_level": "strict"
            },
            "updated_reference_strategy": {
                "strategy_type": "identity_first"
            },
            "identity_acceptance_criteria": {
                "identity_similarity_threshold": 0.85
            },
            "reference_rebuild_notes": {
                "rebuild_status": "strategy_updated"
            },
            "ready_for_resubmission": True,
            "apply_performed": False,
            "retry_gate_open": False,
            "production_accepted": False,
            "downstream_blocked": True
        }
        
        with open(submitted_dir / "character_director_reference_rebuild.SUBMITTED.json", 'w') as f:
            json.dump(character_completion, f, indent=2)
        
        # Create Workflow TD review packet
        workflow_review_packet = {
            "packet_type": "workflow_td_identity_workflow_review",
            "role": "Workflow TD / ComfyUI Technical Director",
            "blocked_shot": "shot01",
            "based_on_evidence_packet": "output/control/role_review_packets/workflow_td_identity_workflow_evidence_packet.json"
        }
        
        with open(review_packets_dir / "workflow_td_identity_workflow_evidence_packet.json", 'w') as f:
            json.dump(workflow_review_packet, f, indent=2)
        
        # Create Character Director review packet
        character_review_packet = {
            "packet_type": "character_director_identity_review",
            "role": "Character Director",
            "blocked_shot": "shot01",
            "character_name": "Alya",
            "based_on_evidence_packet": "output/control/role_review_packets/character_director_identity_evidence_packet.json"
        }
        
        with open(review_packets_dir / "character_director_identity_evidence_packet.json", 'w') as f:
            json.dump(character_review_packet, f, indent=2)
        
        # Create Workflow TD submission template
        workflow_template = {
            "role": "Workflow TD / ComfyUI Technical Director",
            "allowed_decisions": ["approve_workflow", "reject_workflow"],
            "required_artifacts": ["workflow_audit", "required_nodes"]
        }
        
        with open(submissions_dir / "workflow_td_real_decision.SUBMIT.json", 'w') as f:
            json.dump(workflow_template, f, indent=2)
        
        # Create Character Director submission template
        character_template = {
            "role": "Character Director",
            "allowed_decisions": ["approve", "reject"],
            "required_artifacts": ["approved_character_identity_rules"]
        }
        
        with open(submissions_dir / "character_director_real_decision.SUBMIT.json", 'w') as f:
            json.dump(character_template, f, indent=2)
        
        yield str(project_root)


def test_load_submitted_completions(sample_project_root):
    """Test loading submitted completions."""
    completions = load_submitted_completions(sample_project_root)
    
    assert "workflow_td" in completions
    assert "character_director" in completions
    assert completions["workflow_td"]["completion_status"] == "submitted"
    assert completions["character_director"]["completion_status"] == "submitted"


def test_load_role_review_packets(sample_project_root):
    """Test loading role review packets."""
    packets = load_role_review_packets(sample_project_root)
    
    assert "workflow_td" in packets
    assert "character_director" in packets
    assert packets["workflow_td"]["role"] == "Workflow TD / ComfyUI Technical Director"
    assert packets["character_director"]["role"] == "Character Director"


def test_load_submission_templates(sample_project_root):
    """Test loading submission templates."""
    templates = load_submission_templates(sample_project_root)
    
    assert "workflow_td" in templates
    assert "character_director" in templates
    assert "allowed_decisions" in templates["workflow_td"]
    assert "allowed_decisions" in templates["character_director"]


def test_create_role_decision_resubmission_pack(sample_project_root):
    """Test creating resubmission pack from completions."""
    result = create_role_decision_resubmission_pack(sample_project_root)
    
    # Check result structure
    assert result["status"] == "completed"
    assert result["resubmission_packets_created"] == 2
    assert result["based_on_valid_completions"] == True
    assert result["ready_for_role_resubmission"] == True
    assert result["apply_performed"] == False
    assert result["retry_gate_open"] == False
    assert result["production_accepted"] == False
    assert result["downstream_blocked"] == True
    assert "resubmission_path" in result


def test_resubmission_packets_created(sample_project_root):
    """Test that resubmission packet files are created."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet = resubmission_dir / "character_director_resubmission_packet.json"
    workflow_packet = resubmission_dir / "workflow_td_resubmission_packet.json"
    summary_md = resubmission_dir / "ROLE_DECISION_RESUBMISSION_SUMMARY.md"
    summary_json = resubmission_dir / "RESUBMISSION_SUMMARY.json"
    
    assert character_packet.exists()
    assert workflow_packet.exists()
    assert summary_md.exists()
    assert summary_json.exists()


def test_character_director_resubmission_packet_structure(sample_project_root):
    """Test Character Director resubmission packet structure."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    
    with open(character_packet_file, 'r') as f:
        packet = json.load(f)
    
    # Check required fields
    assert packet["packet_type"] == "character_director_resubmission"
    assert packet["role"] == "Character Director"
    assert packet["decision_source"] == "completion_based_resubmission"
    assert packet["current_decision_status"] == "pending_resubmission"
    assert packet["selected_decision"] is None
    assert packet["ready_for_resubmission"] == True
    assert packet["apply_performed"] == False
    assert packet["retry_gate_open"] == False
    assert packet["production_accepted"] == False
    assert packet["downstream_blocked"] == True
    
    # Check completion evidence is present
    assert "completion_evidence" in packet
    assert "updated_character_identity_rules" in packet["completion_evidence"]
    assert "updated_reference_strategy" in packet["completion_evidence"]
    assert "identity_acceptance_criteria" in packet["completion_evidence"]
    assert "reference_rebuild_notes" in packet["completion_evidence"]
    
    # Check based on references
    assert "based_on_submitted_completion" in packet
    assert "based_on_review_packet" in packet
    assert "based_on_submission_template" in packet


def test_workflow_td_resubmission_packet_structure(sample_project_root):
    """Test Workflow TD resubmission packet structure."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    
    with open(workflow_packet_file, 'r') as f:
        packet = json.load(f)
    
    # Check required fields
    assert packet["packet_type"] == "workflow_td_resubmission"
    assert packet["role"] == "Workflow TD / ComfyUI Technical Director"
    assert packet["decision_source"] == "completion_based_resubmission"
    assert packet["current_decision_status"] == "pending_resubmission"
    assert packet["selected_decision"] is None
    assert packet["ready_for_resubmission"] == True
    assert packet["apply_performed"] == False
    assert packet["retry_gate_open"] == False
    assert packet["production_accepted"] == False
    assert packet["downstream_blocked"] == True
    
    # Check completion evidence is present
    assert "completion_evidence" in packet
    assert "updated_workflow_strategy" in packet["completion_evidence"]
    assert "workflow_audit" in packet["completion_evidence"]
    assert "required_nodes" in packet["completion_evidence"]
    assert "required_models" in packet["completion_evidence"]
    assert "preflight_result" in packet["completion_evidence"]
    assert "output_collection_contract" in packet["completion_evidence"]
    
    # Check based on references
    assert "based_on_submitted_completion" in packet
    assert "based_on_review_packet" in packet
    assert "based_on_submission_template" in packet


def test_resubmission_summary_created(sample_project_root):
    """Test resubmission summary is created with correct structure."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    summary_file = resubmission_dir / "RESUBMISSION_SUMMARY.json"
    
    with open(summary_file, 'r') as f:
        summary = json.load(f)
    
    # Check required fields
    assert summary["resubmission_type"] == "completion_based_role_decision_resubmission"
    assert summary["based_on_valid_completions"] == True
    assert summary["resubmission_packets_created"] == 2
    assert summary["ready_for_role_resubmission"] == True
    assert summary["apply_performed"] == False
    assert summary["retry_gate_open"] == False
    assert summary["production_accepted"] == False
    assert summary["downstream_blocked"] == True
    
    # Check boundary conditions
    assert "boundary_conditions" in summary
    assert summary["boundary_conditions"]["no_comfyui_execution"] == True
    assert summary["boundary_conditions"]["no_apply_decisions"] == True
    assert summary["boundary_conditions"]["no_role_decisions_modified"] == True
    assert summary["boundary_conditions"]["no_retry_gate_opened"] == True


def test_no_real_project_mutations(sample_project_root):
    """Test that creating resubmission pack does not mutate real project artifacts."""
    # Create a marker file to detect mutations
    role_decisions_dir = Path(sample_project_root) / "role_decisions"
    role_decisions_dir.mkdir(parents=True, exist_ok=True)
    
    marker_file = role_decisions_dir / "do_not_touch.txt"
    marker_file.write_text("unchanged")
    
    # Create resubmission pack
    create_role_decision_resubmission_pack(sample_project_root)
    
    # Verify marker file is unchanged
    assert marker_file.exists()
    assert marker_file.read_text() == "unchanged"


def test_ready_for_role_resubmission_only_in_resubmission_folder(sample_project_root):
    """Test that ready_for_role_resubmission=true only in resubmission folder, not in original templates."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    # Check resubmission packets have ready_for_role_resubmission=true
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    with open(character_packet_file, 'r') as f:
        character_packet = json.load(f)
    assert character_packet["ready_for_resubmission"] == True
    
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    with open(workflow_packet_file, 'r') as f:
        workflow_packet = json.load(f)
    assert workflow_packet["ready_for_resubmission"] == True


def test_retry_gate_remains_closed(sample_project_root):
    """Test that retry gate remains closed after creating resubmission pack."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    with open(character_packet_file, 'r') as f:
        character_packet = json.load(f)
    assert character_packet["retry_gate_open"] == False
    
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    with open(workflow_packet_file, 'r') as f:
        workflow_packet = json.load(f)
    assert workflow_packet["retry_gate_open"] == False


def test_production_accepted_remains_false(sample_project_root):
    """Test that production_accepted remains false after creating resubmission pack."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    with open(character_packet_file, 'r') as f:
        character_packet = json.load(f)
    assert character_packet["production_accepted"] == False
    
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    with open(workflow_packet_file, 'r') as f:
        workflow_packet = json.load(f)
    assert workflow_packet["production_accepted"] == False


def test_downstream_remains_blocked(sample_project_root):
    """Test that downstream remains blocked after creating resubmission pack."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    with open(character_packet_file, 'r') as f:
        character_packet = json.load(f)
    assert character_packet["downstream_blocked"] == True
    
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    with open(workflow_packet_file, 'r') as f:
        workflow_packet = json.load(f)
    assert workflow_packet["downstream_blocked"] == True


def test_apply_performed_remains_false(sample_project_root):
    """Test that apply_performed remains false in resubmission packets."""
    create_role_decision_resubmission_pack(sample_project_root)
    
    resubmission_dir = Path(sample_project_root) / "output" / "control" / "role_decision_resubmissions"
    
    character_packet_file = resubmission_dir / "character_director_resubmission_packet.json"
    with open(character_packet_file, 'r') as f:
        character_packet = json.load(f)
    assert character_packet["apply_performed"] == False
    
    workflow_packet_file = resubmission_dir / "workflow_td_resubmission_packet.json"
    with open(workflow_packet_file, 'r') as f:
        workflow_packet = json.load(f)
    assert workflow_packet["apply_performed"] == False
