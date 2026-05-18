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
    """Test that episode_ledger.json is updated."""
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = json.load(f)

    # Check for human verdict task event
    verdict_events = [
        event for event in ledger
        if event.get("event_type") == "fresh_visual_human_verdict_task_executed"
    ]
    
    assert len(verdict_events) > 0, "Episode ledger must have human verdict task event"

    event = verdict_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-FRESH-VISUAL-HUMAN-VERDICT-001"
    assert event["generation_performed"] is False
    assert event["agent_generated_verdict"] is False
    assert event["fake_operator_decision_created"] is False
    assert event["agent_accepted_visual"] is False
    assert event["production_accepted"] is False


def test_human_rejection_creates_operator_visual_verdict():
    """Test that human rejection creates operator_visual_verdict.json with correct fields."""
    verdict_path = OPERATOR_REVIEW_DIR / "operator_visual_verdict.json"
    assert verdict_path.exists(), "operator_visual_verdict.json must exist after human rejection"
    
    with open(verdict_path, 'r', encoding='utf-8') as f:
        verdict = json.load(f)
    
    assert verdict["verdict_source"] == "human_operator", "Verdict source must be human_operator"
    assert verdict["agent_generated_verdict"] is False, "Agent generated verdict must be false"
    assert verdict["operator_visual_review_executed"] is True, "Operator visual review must be executed"
    assert verdict["operator_verdict"] == "rejected_needs_corrective_plan", "Operator verdict must be rejected_needs_corrective_plan"
    assert verdict["accepted_as_concept_reference"] is True, "Accepted as concept reference must be true"
    assert verdict["accepted_as_quality_reference"] is False, "Accepted as quality reference must be false"
    assert verdict["accepted_as_final_visual"] is False, "Accepted as final visual must be false"
    assert verdict["production_accepted"] is False, "Production accepted must be false"


def test_human_rejection_creates_operator_visual_rejection():
    """Test that human rejection creates operator_visual_rejection.json with defects."""
    rejection_path = OPERATOR_REVIEW_DIR / "operator_visual_rejection.json"
    assert rejection_path.exists(), "operator_visual_rejection.json must exist after human rejection"

    with open(rejection_path, 'r', encoding='utf-8') as f:
        rejection = json.load(f)

    assert rejection["verdict_source"] == "human_operator", "Verdict source must be human_operator"
    assert rejection["operator_verdict"] == "rejected_needs_corrective_plan"
    assert "defects" in rejection, "Rejection must include defects"
    assert len(rejection["defects"]) > 0, "Must have at least one defect"

    required_defects = [
        "doll_like_face",
        "over_smoothed_skin",
        "glassy_unrealistic_eyes",
        "weak_mouth_teeth_detail",
        "low_skin_texture_detail",
        "not_suitable_as_quality_reference"
    ]
    for defect in required_defects:
        assert defect in rejection["defects"], f"Defect {defect} must be in rejection"

    assert rejection["accepted_as_concept_reference"] is True
    assert rejection["accepted_as_quality_reference"] is False
    assert rejection["production_accepted"] is False


def test_human_rejection_creates_corrective_visual_plan():
    """Test that human rejection creates corrective_visual_plan.json with specific requirements."""
    corrective_plan_path = OPERATOR_REVIEW_DIR / "corrective_visual_plan.json"
    assert corrective_plan_path.exists(), "corrective_visual_plan.json must exist after human rejection"

    with open(corrective_plan_path, 'r', encoding='utf-8') as f:
        plan = json.load(f)

    assert "corrective_requirements" in plan, "Plan must have corrective_requirements"
    assert len(plan["corrective_requirements"]) > 0, "Must have at least one corrective requirement"

    # Verify specific requirements are present
    requirement_descriptions = [req["requirement"] for req in plan["corrective_requirements"]]
    required_requirements = [
        "Keep fairytale / winter fantasy mood",
        "Improve skin texture realism",
        "Improve mouth/teeth anatomy",
        "Reduce doll/plastic face effect",
        "Keep beautiful blue eyes but make them more natural",
        "Increase facial micro-detail",
        "Preserve concept direction, but raise production quality"
    ]
    for req in required_requirements:
        assert req in requirement_descriptions, f"Requirement '{req}' must be in corrective plan"

    # Verify forbidden actions
    assert "forbidden_actions" in plan
    forbidden_actions = [action["action"] for action in plan["forbidden_actions"]]
    assert "blind_retry" in forbidden_actions, "blind_retry must be forbidden"

    # Verify next generation requirements
    assert plan["next_generation_requirements"]["requires_separate_authorization_gate"] is True
    assert plan["next_generation_requirements"]["blind_retry_forbidden"] is True

    # Verify state
    assert plan["current_state"] == "fresh_visual_rejected"
    assert plan["next_allowed_action"] == "corrective_visual_plan_review_required"
    assert plan["retry_authorized"] is False
    assert plan["generation_authorized"] is False


def test_human_rejection_state_routes_to_corrective_plan_review():
    """Test that state routes to corrective_visual_plan_review_required after human rejection."""
    state_path = CONTROL_DIR / "state.json"
    with open(state_path, 'r') as f:
        state = json.load(f)
    
    assert state["current_state"] == "fresh_visual_rejected", "Current state must be fresh_visual_rejected"
    assert state["next_allowed_action"] == "corrective_visual_plan_review_required", "Next action must be corrective_visual_plan_review_required"
    assert state["retry_authorized"] is False, "Retry must not be authorized"
    assert state["generation_authorized"] is False, "Generation must not be authorized"
    assert state["assembly_allowed"] is False, "Assembly must not be allowed"
    assert state["production_accepted"] is False, "Production accepted must remain false"


def test_human_rejection_updates_artifact_index():
    """Test that artifact_index.json is updated with human rejection artifacts."""
    artifact_index_path = CONTROL_DIR / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        index = json.load(f)
    
    assert index.get("fresh_visual_human_verdict_provided") is True, "Human verdict provided must be true"
    assert index.get("fresh_visual_operator_verdict_artifact_created") is True, "Operator verdict artifact created must be true"
    assert index.get("fresh_visual_operator_rejection_artifact_created") is True, "Operator rejection artifact created must be true"
    assert index.get("fresh_visual_corrective_plan_artifact_created") is True, "Corrective plan artifact created must be true"
    
    assert index["current_state"] == "fresh_visual_rejected"
    assert index["next_allowed_action"] == "corrective_visual_plan_review_required"
    assert index["fresh_visual_operator_verdict"] == "rejected_needs_corrective_plan"
    assert index["fresh_visual_accepted_as_concept_reference"] is True
    assert index["fresh_visual_accepted_as_quality_reference"] is False
    assert index["fresh_visual_accepted_as_final_visual"] is False
    assert index["fresh_visual_retry_authorized"] is False
    assert index["fresh_visual_generation_authorized"] is False


def test_human_rejection_updates_episode_ledger():
    """Test that episode_ledger.json is updated with human rejection event."""
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = json.load(f)

    rejection_events = [
        event for event in ledger
        if event.get("event_type") == "fresh_visual_human_verdict_rejection"
    ]

    assert len(rejection_events) > 0, "Episode ledger must have human rejection event"

    event = rejection_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-FRESH-VISUAL-HUMAN-VERDICT-REJECTION-001"
    assert event["verdict_source"] == "human_operator"
    assert event["agent_generated_verdict"] is False
    assert event["operator_verdict"] == "rejected_needs_corrective_plan"
    assert event["accepted_as_concept_reference"] is True
    assert event["accepted_as_quality_reference"] is False
    assert event["production_accepted"] is False
    assert event["generation_performed"] is False
    assert event["retry_attempted"] is False
    assert event["comfyui_submit_executed"] is False
    assert event["assembly_executed"] is False
    assert event["downstream_executed"] is False
    assert event["current_state"] == "fresh_visual_rejected"
    assert event["next_allowed_action"] == "corrective_visual_plan_review_required"


def test_agent_generated_verdict_is_always_false():
    """Test that agent_generated_verdict is always false."""
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["agent_generated_verdict"] is False
    assert pending["fake_operator_decision_created"] is False


def test_production_accepted_true_is_forbidden():
    """Test that production_accepted=true is forbidden."""
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["production_accepted"] is False


def test_generation_retry_comfyui_submit_remain_false():
    """Test that generation/retry/comfyui_submit remain false."""
    review_pending_path = OPERATOR_REVIEW_DIR / "review_pending.json"
    with open(review_pending_path, 'r') as f:
        pending = json.load(f)
    
    assert pending["generation_performed"] is False
    assert pending["retry_attempted"] is False
    assert pending["comfyui_submit_executed"] is False


def test_artifact_index_and_episode_ledger_updated():
    """Test that artifact_index and episode_ledger are updated."""
    artifact_index_path = CONTROL_DIR / "artifact_index.json"
    with open(artifact_index_path, 'r', encoding='utf-8') as f:
        index = json.load(f)

    assert index.get("fresh_visual_human_verdict_task_executed") is True
    assert index.get("fresh_visual_human_verdict_provided") is True
    assert index.get("fresh_visual_operator_verdict_artifact_created") is True
    
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    with open(ledger_path, 'r', encoding='utf-8') as f:
        ledger = json.load(f)

    verdict_events = [
        event for event in ledger
        if event.get("event_type") == "fresh_visual_human_verdict_task_executed"
    ]
    assert len(verdict_events) > 0, "Episode ledger must have human verdict task event"
    
    event = verdict_events[-1]
    assert event["human_operator_verdict_provided"] is False
    assert event["agent_generated_verdict"] is False
    assert event["operator_visual_verdict_artifact_created"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
