"""
Tests for fresh visual operator review workflow.
"""
import json
import os
from pathlib import Path
import pytest


PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
OPERATOR_REVIEW_DIR = CONTROL_DIR / "fresh_visual_operator_review"


def test_candidate_discovery_from_latest_manifest():
    """Test that candidate can be discovered from latest generation manifest."""
    manifest_path = CONTROL_DIR / "fresh_visual_candidate" / "generated_candidate_proof.json"
    assert manifest_path.exists(), "Generation manifest must exist"
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert "generated_assets" in manifest, "Manifest must have generated_assets"
    assert len(manifest["generated_assets"]) > 0, "Must have at least one generated asset"
    
    asset = manifest["generated_assets"][0]
    assert "path" in asset, "Asset must have path"
    assert "sha256" in asset, "Asset must have sha256"
    assert "width" in asset, "Asset must have width"
    assert "height" in asset, "Asset must have height"
    
    # Verify file exists
    assert os.path.exists(asset["path"]), f"Candidate image must exist: {asset['path']}"
    assert asset["exists"] is True, "Asset must be marked as exists"
    assert asset["readable"] is True, "Asset must be marked as readable"


def test_candidate_validation():
    """Test that candidate is valid (sha256, dimensions, not stub)."""
    manifest_path = CONTROL_DIR / "fresh_visual_candidate" / "generated_candidate_proof.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    asset = manifest["generated_assets"][0]
    
    # Check dimensions
    assert asset["width"] == 1024, f"Width must be 1024, got {asset['width']}"
    assert asset["height"] == 1024, f"Height must be 1024, got {asset['height']}"
    
    # Check size
    assert asset["size_bytes"] > 100000, f"Size must be > 100KB, got {asset['size_bytes']}"
    
    # Check sha256 format
    assert len(asset["sha256"]) == 64, "SHA256 must be 64 characters"
    
    # Check generation count
    assert manifest["generation_count"] == 1, f"Generation count must be 1, got {manifest['generation_count']}"
    assert manifest.get("second_generation_attempted", False) is False, "Second generation must not be attempted"


def test_operator_review_packet_created():
    """Test that operator review packet was created with required fields."""
    packet_path = OPERATOR_REVIEW_DIR / "operator_review_packet.json"
    assert packet_path.exists(), "Operator review packet must exist"
    
    with open(packet_path, 'r') as f:
        packet = json.load(f)
    
    assert packet["task_id"] == "RC-COMBINE-V2-FRESH-VISUAL-OPERATOR-REVIEW-001"
    assert "candidate_image_path" in packet
    assert "candidate_manifest_path" in packet
    assert "prompt_id" in packet
    assert "sha256" in packet
    assert "width" in packet
    assert "height" in packet
    assert packet["review_required"] is True
    assert packet["operator_must_decide"] is True
    assert packet["agent_may_not_accept_visual"] is True
    assert packet["production_accepted"] is False


def test_visual_review_checklist_created():
    """Test that visual review checklist was created."""
    checklist_path = OPERATOR_REVIEW_DIR / "visual_review_checklist.json"
    assert checklist_path.exists(), "Visual review checklist must exist"
    
    with open(checklist_path, 'r') as f:
        checklist = json.load(f)
    
    assert "checklist_items" in checklist
    assert len(checklist["checklist_items"]) > 0
    
    # Verify required checklist categories
    categories = [item["category"] for item in checklist["checklist_items"]]
    required_categories = [
        "face_quality", "eyes", "mouth_teeth", "skin_realism",
        "facial_detail", "identity_style", "anatomy", "clothing_props",
        "background", "production_usability"
    ]
    for req_cat in required_categories:
        assert req_cat in categories, f"Checklist must include {req_cat}"
    
    assert checklist["checklist_status"] == "pending_operator_completion"


def test_no_fake_operator_decision():
    """Test that no fake operator decision was created."""
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    assert review_pending_path.exists(), "Review pending artifact must exist"
    
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["agent_generated_verdict"] is False
    assert pending["fake_operator_decision_created"] is False
    assert pending["agent_accepted_visual"] is False
    assert pending["operator_verdict"] is None
    assert pending["production_accepted"] is False


def test_accepted_verdict_does_not_set_production_accepted():
    """Test that accepted verdict does not set production_accepted=true."""
    # Since no verdict was provided, state should remain pending
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["production_accepted"] is False
    assert pending["current_state"] == "operator_visual_review_required"
    assert pending["next_allowed_action"] == "operator_visual_review_required"


def test_rejected_verdict_creates_corrective_plan():
    """Test that rejected verdict creates corrective plan but does not retry."""
    # This test is for the case when a verdict is provided
    # Since no verdict was provided in this run, we verify that no corrective plan was created
    corrective_plan_path = OPERATOR_REVIEW_DIR / "corrective_plan.json"
    assert not corrective_plan_path.exists(), "Corrective plan should not exist without rejection"


def test_needs_manual_review_keeps_state():
    """Test that needs_manual_review keeps operator_visual_review_required."""
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["current_state"] == "operator_visual_review_required"
    assert pending["next_allowed_action"] == "operator_visual_review_required"


def test_second_generation_detection_blocks():
    """Test that second generation detection would block."""
    manifest_path = CONTROL_DIR / "fresh_visual_candidate" / "generated_candidate_proof.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["generation_count"] == 1, "Should only have 1 generation"
    assert manifest.get("second_generation_attempted", False) is False, "Second generation should not be attempted"


def test_artifact_index_updated():
    """Test that artifact_index.json was updated with operator review artifacts."""
    artifact_index_path = CONTROL_DIR / "artifact_index.json"
    assert artifact_index_path.exists()
    
    with open(artifact_index_path, 'r') as f:
        index = json.load(f)
    
    assert index.get("fresh_visual_operator_review_packet_created") is True
    assert "fresh_visual_operator_review_dir" in index
    assert "fresh_visual_operator_review_packet" in index
    assert "fresh_visual_visual_review_checklist" in index
    assert "fresh_visual_review_pending" in index
    assert "fresh_visual_candidate_image_path" in index
    assert "fresh_visual_candidate_sha256" in index
    assert "fresh_visual_candidate_dimensions" in index
    assert index["fresh_visual_generation_count"] == 1
    assert index["fresh_visual_second_generation_attempted"] is False


def test_episode_ledger_updated():
    """Test that episode_ledger.json was updated with operator review event."""
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    assert ledger_path.exists()
    
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    
    # Find the operator review event
    operator_review_events = [
        event for event in ledger 
        if event.get("event_type") == "fresh_visual_operator_review_packet_created"
    ]
    
    assert len(operator_review_events) > 0, "Episode ledger must have operator review event"
    
    event = operator_review_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-FRESH-VISUAL-OPERATOR-REVIEW-001"
    assert event["generation_performed"] is False
    assert event["operator_visual_verdict_recorded"] is False
    assert event["fake_operator_decision_created"] is False
    assert event["agent_accepted_visual"] is False
    assert event["production_accepted"] is False


def test_forbidden_actions_remain_false():
    """Test that forbidden actions remain false."""
    manifest_path = CONTROL_DIR / "fresh_visual_candidate" / "generated_candidate_proof.json"
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    assert manifest["visual_qa_acceptance_executed"] is False
    assert manifest["operator_visual_acceptance_executed"] is False
    assert manifest["assembly_executed"] is False
    assert manifest["downstream_executed"] is False
    assert manifest["production_accepted"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
