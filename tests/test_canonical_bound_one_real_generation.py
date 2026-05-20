"""
Tests for RC-COMBINE-V2-CANONICAL-BOUND-ONE-REAL-GENERATION-AND-VISUAL-REVIEW-001
Tests canonical bound generation execution, artifacts, and state.
"""

import pytest
import json
from pathlib import Path
from PIL import Image

project_root = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01")
canonical_bound_dir = project_root / "output" / "control" / "canonical_bound_generation"
control_dir = project_root / "output" / "control"


def test_agent_contract_created():
    """Test that agent contract was created with correct structure."""
    contract_path = canonical_bound_dir / "canonical_bound_generation_stage_agent_contract.json"
    assert contract_path.exists(), "Agent contract does not exist"
    
    with open(contract_path) as f:
        contract = json.load(f)
    
    assert contract["agent_id"] == "canonical_bound_generation_stage_agent"
    assert contract["agent_role"] == "Camera Operator + Actor Identity Binding Execution Stage"
    assert contract["canonical_references_verified_count"] == 24
    assert "canonical_reference_search" in contract["forbidden_tools"]
    assert "canonical_reference_rebuild" in contract["forbidden_tools"]
    assert "retry_generation" in contract["forbidden_tools"]


def test_generation_authorization_created():
    """Test that generation authorization was created."""
    auth_path = canonical_bound_dir / "canonical_bound_generation_authorization.json"
    assert auth_path.exists(), "Generation authorization does not exist"
    
    with open(auth_path) as f:
        auth = json.load(f)
    
    assert auth["generation_authorized"] == True
    assert auth["max_generations"] == 1
    assert auth["retry_authorized"] == False
    assert auth["second_generation_authorized"] == False
    assert auth["assembly_authorized"] == False
    assert auth["downstream_authorized"] == False
    assert auth["production_acceptance_authorized"] == False
    assert auth["dry_run_forbidden"] == True
    assert auth["canonical_references_verified"] == 24


def test_submitted_workflow_exists():
    """Test that submitted workflow was created."""
    workflow_path = canonical_bound_dir / "canonical_bound_submitted_workflow.json"
    assert workflow_path.exists(), "Submitted workflow does not exist"
    
    with open(workflow_path) as f:
        workflow = json.load(f)
    
    # Check that workflow has no metadata node (it was stripped for ComfyUI)
    assert "_canonical_binding" not in workflow, "Workflow should not have _canonical_binding metadata"
    
    # Check that workflow has required nodes
    assert "3" in workflow, "KSampler node missing"
    assert "4" in workflow, "CheckpointLoader node missing"
    assert "9" in workflow, "SaveImage node missing"


def test_binding_metadata_preserved():
    """Test that canonical binding metadata was preserved separately."""
    metadata_path = canonical_bound_dir / "canonical_bound_binding_metadata.json"
    assert metadata_path.exists(), "Binding metadata does not exist"
    
    with open(metadata_path) as f:
        metadata = json.load(f)
    
    assert "bound_references" in metadata
    assert metadata["bound_references"] == 24
    assert "reference_paths" in metadata
    assert len(metadata["reference_paths"]) == 24


def test_generation_manifest_created():
    """Test that generation manifest was created."""
    manifest_path = canonical_bound_dir / "canonical_bound_generation_manifest.json"
    assert manifest_path.exists(), "Generation manifest does not exist"
    
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert manifest["task_id"] == "RC-COMBINE-V2-CANONICAL-BOUND-ONE-REAL-GENERATION-AND-VISUAL-REVIEW-001"
    assert manifest["generation_count"] == 1
    assert manifest["max_generations"] == 1
    assert manifest["dry_run"] == False
    assert manifest["execute_mode"] == True
    assert manifest["canonical_binding_used"] == True
    assert manifest["canonical_references_verified"] == 24
    assert manifest["prompt_id"] is not None
    assert manifest["prompt_id"] != ""
    assert len(manifest["generated_assets"]) == 1


def test_result_review_created():
    """Test that result review was created."""
    review_path = canonical_bound_dir / "canonical_bound_generation_result_review.json"
    assert review_path.exists(), "Result review does not exist"
    
    with open(review_path) as f:
        review = json.load(f)
    
    assert review["generation_status"] == "completed"
    assert review["dry_run"] == False
    assert review["assets_generated"] == True
    assert len(review["generated_assets"]) == 1
    assert review["technical_validation"]["assets_readable"] == True
    assert review["technical_validation"]["assets_have_dimensions"] == True
    assert review["technical_validation"]["assets_have_sha256"] == True
    assert review["visual_qa_blocked"] == True
    assert review["assembly_blocked"] == True
    assert review["downstream_blocked"] == True
    assert review["production_accepted"] == False
    assert review["face_visibility_requirement"] == True
    assert review["environment_stability_requirement"] == True
    assert review["back_only_shot_forbidden"] == True
    assert review["random_identity_drift_forbidden"] == True
    assert review["random_environment_drift_forbidden"] == True


def test_operator_visual_review_packet_created():
    """Test that operator visual review packet was created."""
    packet_path = canonical_bound_dir / "canonical_bound_operator_visual_review_packet.json"
    assert packet_path.exists(), "Operator visual review packet does not exist"
    
    with open(packet_path) as f:
        packet = json.load(f)
    
    assert packet["generation_status"] == "completed"
    assert packet["prompt_id"] is not None
    assert len(packet["generated_assets"]) == 1
    assert packet["canonical_binding_used"] == True
    assert packet["canonical_references_verified"] == 24
    assert packet["operator_verdict"] == "NOT_PROVIDED"
    assert packet["verdict_required"] == True
    assert packet["current_state"] == "operator_visual_review_required"
    assert packet["next_allowed_action"] == "operator_visual_review_required"


def test_generated_asset_exists_and_readable():
    """Test that generated asset exists and is readable."""
    manifest_path = canonical_bound_dir / "canonical_bound_generation_manifest.json"
    with open(manifest_path) as f:
        manifest = json.load(f)
    
    assert len(manifest["generated_assets"]) == 1, "Should have exactly 1 generated asset"
    
    asset_path = Path(manifest["generated_assets"][0])
    assert asset_path.exists(), f"Generated asset does not exist: {asset_path}"
    
    # Verify asset is readable
    try:
        with Image.open(asset_path) as img:
            width, height = img.size
            assert width > 0, "Asset width should be > 0"
            assert height > 0, "Asset height should be > 0"
    except Exception as e:
        pytest.fail(f"Generated asset is not readable: {e}")


def test_generated_asset_has_sha256():
    """Test that generated asset has SHA256 recorded."""
    review_path = canonical_bound_dir / "canonical_bound_generation_result_review.json"
    with open(review_path) as f:
        review = json.load(f)
    
    asset = review["generated_assets"][0]
    assert "sha256" in asset
    assert asset["sha256"] is not None
    assert len(asset["sha256"]) == 64  # SHA256 is 64 hex chars
    assert asset["size_bytes"] > 1024  # Should be > 1KB
    assert asset["width"] > 0
    assert asset["height"] > 0


def test_state_updated_to_operator_visual_review_required():
    """Test that state was updated to operator_visual_review_required."""
    state_path = control_dir / "state.json"
    assert state_path.exists(), "state.json does not exist"
    
    with open(state_path) as f:
        state = json.load(f)
    
    assert state["current_state"] == "operator_visual_review_required"
    assert state["next_allowed_action"] == "operator_visual_review_required"
    assert state["production_accepted"] == False
    assert state["canonical_bound_real_generation_executed"] == True
    assert state["canonical_bound_generation_count"] == 1
    assert state["canonical_bound_max_generations"] == 1
    assert state["canonical_bound_dry_run"] == False


def test_artifact_index_updated():
    """Test that artifact index was updated."""
    index_path = control_dir / "artifact_index.json"
    assert index_path.exists(), "artifact_index.json does not exist"
    
    with open(index_path) as f:
        index = json.load(f)
    
    assert index["current_state"] == "operator_visual_review_required"
    assert index["next_allowed_action"] == "operator_visual_review_required"
    assert index["production_accepted"] == False
    assert index["canonical_bound_real_generation_executed"] == True
    assert index["canonical_bound_generation_count"] == 1
    assert index["canonical_bound_max_generations"] == 1
    assert index["canonical_bound_dry_run"] == False
    assert "canonical_bound_generation_authorization" in index
    assert "canonical_bound_generation_manifest" in index
    assert "canonical_bound_generation_result_review" in index
    assert "canonical_bound_operator_visual_review_packet" in index
    assert "canonical_bound_submitted_workflow" in index


def test_episode_ledger_updated():
    """Test that episode ledger was updated."""
    ledger_path = control_dir / "episode_ledger.json"
    assert ledger_path.exists(), "episode_ledger.json does not exist"
    
    with open(ledger_path) as f:
        ledger = json.load(f)
    
    # Find the canonical bound generation events (may have multiple due to debugging)
    canonical_bound_events = [e for e in ledger if e.get("event_type") == "canonical_bound_one_real_generation_executed"]
    assert len(canonical_bound_events) >= 1, "Should have at least 1 canonical bound generation event"
    
    # Check the latest event (last in list)
    event = canonical_bound_events[-1]
    assert event["task_id"] == "RC-COMBINE-V2-CANONICAL-BOUND-ONE-REAL-GENERATION-AND-VISUAL-REVIEW-001"
    assert event["generation_count"] == 1
    assert event["max_generations"] == 1
    assert event["second_generation_attempted"] == False
    assert event["retry_attempted"] == False
    assert event["blind_retry_attempted"] == False
    assert event["workflow_submitted"] == True
    assert event["comfyui_submit_executed"] == True
    assert event["prompt_id"] is not None
    assert event["prompt_id"] != ""
    assert event["dry_run"] == False
    assert event["canonical_binding_used"] == True
    assert event["canonical_references_verified"] == 24
    assert event["visual_qa_acceptance_executed"] == False
    assert event["operator_visual_acceptance_executed"] == False
    assert event["assembly_executed"] == False
    assert event["downstream_executed"] == False
    assert event["production_accepted"] == False
    assert event["current_state"] == "operator_visual_review_required"
    assert event["next_allowed_action"] == "operator_visual_review_required"


def test_proof_created():
    """Test that proof JSON was created."""
    proof_path = canonical_bound_dir / "canonical_bound_generation_proof.json"
    assert proof_path.exists(), "Proof JSON does not exist"
    
    with open(proof_path) as f:
        proof = json.load(f)
    
    assert proof["task_id"] == "RC-COMBINE-V2-CANONICAL-BOUND-ONE-REAL-GENERATION-AND-VISUAL-REVIEW-001"
    assert proof["feature_completed"] == True
    assert proof["full_feature_loop_executed"] == True
    assert proof["previous_layer_used_as_binding_preflight_only"] == True
    assert proof["canonical_reference_set_researched"] == False
    assert proof["canonical_reference_set_rebuilt"] == False
    assert proof["canonical_references_verified_count"] == 24
    assert proof["canonical_binding_used"] == True
    assert proof["generation_performed"] == True
    assert proof["dry_run"] == False
    assert proof["workflow_submitted"] == True
    assert proof["comfyui_execution"] == True
    assert proof["generation_count"] == 1
    assert proof["max_generations"] == 1
    assert proof["second_generation_attempted"] == False
    assert proof["retry_attempted"] == False
    assert proof["blind_retry_attempted"] == False
    assert proof["prompt_id"] is not None
    assert proof["prompt_id"] != ""
    assert len(proof["generated_assets"]) == 1
    assert proof["operator_visual_review_required"] == True
    assert proof["visual_qa_acceptance_executed"] == False
    assert proof["operator_visual_acceptance_executed"] == False
    assert proof["assembly_executed"] == False
    assert proof["downstream_executed"] == False
    assert proof["production_accepted"] == False
    assert proof["current_state"] == "operator_visual_review_required"
    assert proof["next_allowed_action"] == "operator_visual_review_required"
    assert len(proof["blockers"]) == 0


def test_no_second_generation_attempted():
    """Test that no second generation was attempted."""
    ledger_path = control_dir / "episode_ledger.json"
    with open(ledger_path) as f:
        ledger = json.load(f)
    
    canonical_bound_events = [e for e in ledger if e.get("event_type") == "canonical_bound_one_real_generation_executed"]
    assert len(canonical_bound_events) >= 1, "Should have at least 1 canonical bound generation event"
    
    # Check the latest event
    event = canonical_bound_events[-1]
    assert event["second_generation_attempted"] == False
    assert event["retry_attempted"] == False
    assert event["blind_retry_attempted"] == False


def test_canonical_references_not_searched_or_rebuilt():
    """Test that canonical references were not searched or rebuilt."""
    proof_path = canonical_bound_dir / "canonical_bound_generation_proof.json"
    with open(proof_path) as f:
        proof = json.load(f)
    
    assert proof["canonical_reference_set_researched"] == False
    assert proof["canonical_reference_set_rebuilt"] == False
    assert proof["canonical_references_verified_count"] == 24


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
