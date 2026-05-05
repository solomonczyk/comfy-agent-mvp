"""
RC-COMBINE-V2-1041-1100 — Tests for Corrective Retry V2 Result Review

Tests for reviewing corrective retry v2 generation result and gating next step:
- Branch A (success): asset collected -> stop before Visual QA
- Branch B (failed_collection): zero assets -> stop at result review
"""

import json
import pytest
from pathlib import Path
from app.cli import combine_review_corrective_retry_v2_result
import argparse


@pytest.fixture
def temp_project_root_with_generation(tmp_path: Path):
    """Create a temporary project root with generation result."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with assets
    generation_result = {
        "stage": "corrective_retry_generate_assets_v2",
        "corrective_retry_package_v2_used": True,
        "requested_shot_id": "shot02",
        "workflow_shot_id_matches_requested_shot": True,
        "prompt_patch_v2_applied": True,
        "generation_attempts": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "generation_performed": True,
        "comfyui_execution": False,
        "second_generation_attempted": False,
        "blind_retry_allowed": False,
        "legacy_512_workflow_blocked": True,
        "minimum_short_side_1024_enforced": True,
        "generated_assets": ["output/shot02/asset1.png", "output/shot02/asset2.png"],
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_corrective_retry_v2_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    return tmp_path


@pytest.fixture
def temp_project_root_no_assets(tmp_path: Path):
    """Create a temporary project root with generation result but no assets."""
    control_dir = tmp_path / "output" / "control"
    control_dir.mkdir(parents=True, exist_ok=True)
    
    # Create generation result with no assets
    generation_result = {
        "stage": "corrective_retry_generate_assets_v2",
        "corrective_retry_package_v2_used": True,
        "requested_shot_id": "shot02",
        "workflow_shot_id_matches_requested_shot": True,
        "prompt_patch_v2_applied": True,
        "generation_attempts": 1,
        "max_generations": 1,
        "workflow_submitted": True,
        "generation_performed": True,
        "comfyui_execution": False,
        "second_generation_attempted": False,
        "blind_retry_allowed": False,
        "legacy_512_workflow_blocked": True,
        "minimum_short_side_1024_enforced": True,
        "generated_assets": [],  # No assets
        "visual_qa_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": "2024-01-01T00:00:00"
    }
    with open(control_dir / "combine_v2_corrective_retry_v2_generation_result.json", 'w') as f:
        json.dump(generation_result, f)
    
    return tmp_path


def test_result_review_success_branch(temp_project_root_with_generation: Path):
    """Test result review with assets (success branch)."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["branch_selected"] == "success"
    assert review["generated_assets_count"] == 2
    assert review["result_review_executed"] is True
    assert review["visual_qa_executed"] is False
    assert review["real_visual_qa_started"] is False
    assert review["assembly_executed"] is False
    assert review["downstream_executed"] is False
    assert review["production_accepted"] is False


def test_result_review_failed_collection_branch(temp_project_root_no_assets: Path):
    """Test result review with no assets (failed_collection branch)."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_no_assets),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_no_assets / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["branch_selected"] == "failed_collection"
    assert review["generated_assets_count"] == 0
    assert review["failure_code"] == "FAILED_OUTPUT_COLLECTION_ZERO_ASSETS"
    assert review["result_review_executed"] is True
    assert review["visual_qa_executed"] is False
    assert review["assembly_executed"] is False
    assert review["downstream_executed"] is False
    assert review["production_accepted"] is False


def test_visual_qa_not_executed_on_review(temp_project_root_with_generation: Path):
    """Test that visual QA is not executed during result review."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["visual_qa_executed"] is False
    assert review["real_visual_qa_started"] is False
    assert review["operator_visual_decision_executed"] is False


def test_assembly_not_executed_on_review(temp_project_root_with_generation: Path):
    """Test that assembly is not executed during result review."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["assembly_executed"] is False


def test_downstream_not_executed_on_review(temp_project_root_with_generation: Path):
    """Test that downstream is not executed during result review."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["downstream_executed"] is False


def test_production_accepted_false_on_review(temp_project_root_with_generation: Path):
    """Test that production_accepted is false during result review."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    review_path = control_dir / "combine_v2_corrective_retry_v2_result_review.json"
    with open(review_path, 'r') as f:
        review = json.load(f)
    
    assert review["production_accepted"] is False


def test_visual_qa_entry_decision_success_branch(temp_project_root_with_generation: Path):
    """Test visual QA entry decision for success branch."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    visual_qa_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_entry_decision.json"
    with open(visual_qa_path, 'r') as f:
        visual_qa_decision = json.load(f)
    
    assert visual_qa_decision["visual_qa_required"] is True
    assert visual_qa_decision["visual_qa_executed"] is False
    assert visual_qa_decision["real_visual_qa_started"] is False
    assert visual_qa_decision["operator_visual_decision_required"] is True


def test_visual_qa_entry_decision_failed_branch(temp_project_root_no_assets: Path):
    """Test visual QA entry decision for failed_collection branch."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_no_assets),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_no_assets / "output" / "control"
    visual_qa_path = control_dir / "combine_v2_corrective_retry_v2_visual_qa_entry_decision.json"
    with open(visual_qa_path, 'r') as f:
        visual_qa_decision = json.load(f)
    
    assert visual_qa_decision["visual_qa_required"] is False
    assert visual_qa_decision["visual_qa_executed"] is False
    assert visual_qa_decision["real_visual_qa_started"] is False
    assert visual_qa_decision["operator_visual_decision_required"] is False


def test_artifact_index_updated_success(temp_project_root_with_generation: Path):
    """Test that artifact index is updated on success branch."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["current_state"] == "corrective_retry_v2_visual_qa_preflight_required"
    assert artifact_index["next_allowed_action"] == "corrective_retry_v2_visual_qa_preflight_required"
    assert artifact_index["branch_selected"] == "success"
    assert artifact_index["generated_assets_count"] == 2
    assert artifact_index["result_review_executed"] is True
    assert artifact_index["visual_qa_executed"] is False


def test_artifact_index_updated_failed(temp_project_root_no_assets: Path):
    """Test that artifact index is updated on failed_collection branch."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_no_assets),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_no_assets / "output" / "control"
    artifact_index_path = control_dir / "artifact_index.json"
    with open(artifact_index_path, 'r') as f:
        artifact_index = json.load(f)
    
    assert artifact_index["current_state"] == "corrective_retry_v2_result_review_required"
    assert artifact_index["next_allowed_action"] == "corrective_retry_v2_result_review_required"
    assert artifact_index["branch_selected"] == "failed_collection"
    assert artifact_index["generated_assets_count"] == 0
    assert artifact_index["result_review_executed"] is True


def test_episode_ledger_updated(temp_project_root_with_generation: Path):
    """Test that episode ledger is updated."""
    args = argparse.Namespace(
        project_root=str(temp_project_root_with_generation),
        shot_id="shot02",
        json=True
    )
    
    result = combine_review_corrective_retry_v2_result(args)
    assert result == 0
    
    control_dir = temp_project_root_with_generation / "output" / "control"
    ledger_path = control_dir / "episode_ledger.json"
    with open(ledger_path, 'r') as f:
        ledger = json.load(f)
    
    # Check that the last event is the result review completion
    last_event = ledger[-1]
    assert last_event["event_type"] == "corrective_retry_v2_result_review_completed"
    assert last_event["shot_id"] == "shot02"
    assert last_event["branch_selected"] == "success"
    assert last_event["result_review_executed"] is True
    assert last_event["visual_qa_executed"] is False
    assert last_event["assembly_executed"] is False
    assert last_event["downstream_executed"] is False
