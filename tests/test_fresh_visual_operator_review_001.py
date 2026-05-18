"""Tests for RC-COMBINE-V2-FRESH-VISUAL-OPERATOR-REVIEW-001.

Validates operator visual review recording for corrective fresh visual candidate.
No generation, no retry, no Visual QA auto-acceptance, no assembly, no downstream.
"""

import json
import os
import pytest

CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"
FVC_DIR = os.path.join(CONTROL_DIR, "fresh_visual_candidate")

OUTCOME_PATH = os.path.join(FVC_DIR, "operator_visual_review_outcome.json")
ROUTING_PATH = os.path.join(FVC_DIR, "post_operator_visual_review_routing_decision.json")
BLOCKER_PATH = os.path.join(FVC_DIR, "operator_visual_review_blocker.json")
MANIFEST_PATH = os.path.join(FVC_DIR, "corrective_generation_manifest.json")
RESULT_REVIEW_PATH = os.path.join(FVC_DIR, "corrective_generation_result_review.json")
ARTIFACT_INDEX_PATH = os.path.join(CONTROL_DIR, "artifact_index.json")
EPISODE_LEDGER_PATH = os.path.join(CONTROL_DIR, "episode_ledger.json")
ASSET_PATH = os.path.join(FVC_DIR, "combine_v2_corrective_1779095420_00001_.png")

KNOWN_SHA256 = "37d32671facfb11323e779d2811e1c7a8d5c430597f3eb11eef3dcd0ed78c405"
KNOWN_PROMPT_ID = "62cf0c52-7f45-4b75-8fa1-3fcfc9d70fbc"


def _load(path):
    with open(path, "r") as f:
        return json.load(f)


def test_operator_review_requires_real_operator_verdict():
    """No verdict was provided — outcome must reflect missing verdict, not a fake one."""
    outcome = _load(OUTCOME_PATH)
    assert outcome["operator_verdict"] is None, "verdict must be null when no real verdict provided"
    assert outcome["fake_operator_decision_created"] is False
    assert outcome["blocker_type"] == "missing_operator_visual_verdict"
    assert outcome["blocker_active"] is True


def test_operator_review_rejects_fake_agent_decision():
    """Outcome and blocker must explicitly record that no fake decision was created."""
    outcome = _load(OUTCOME_PATH)
    blocker = _load(BLOCKER_PATH)
    routing = _load(ROUTING_PATH)
    assert outcome["fake_operator_decision_created"] is False
    assert blocker["fake_operator_decision_created"] is False
    assert routing["fake_operator_decision_created"] is False


def test_operator_review_accepts_candidate_without_production_acceptance():
    """Even if a future verdict is 'accepted_for_next_stage', production_accepted stays False.
    Currently no verdict — validate the constraint is correctly modelled in routing decision."""
    routing = _load(ROUTING_PATH)
    accepted_route = routing["accepted_for_next_stage_route"]
    assert accepted_route["would_keep_production_accepted"] is False
    assert accepted_route["would_trigger_generation"] is False
    outcome = _load(OUTCOME_PATH)
    assert outcome["production_accepted"] is False
    assert outcome["visual_candidate_operator_accepted"] is False


def test_operator_review_rejected_routes_to_corrective_plan():
    """Rejected route must lead to corrective_plan_required, not generation."""
    routing = _load(ROUTING_PATH)
    rejected = routing["rejected_route"]
    assert rejected["would_route_to"] == "corrective_plan_required"
    assert rejected["would_keep_production_accepted"] is False


def test_operator_review_needs_fix_routes_to_plan_update():
    """needs_fix route must lead to corrective_plan_update_required, no generation."""
    routing = _load(ROUTING_PATH)
    needs_fix = routing["needs_fix_route"]
    assert needs_fix["would_route_to"] == "corrective_plan_update_required"
    assert needs_fix["would_trigger_generation"] is False


def test_operator_review_blocks_assembly_downstream():
    """Assembly and downstream must remain blocked at all paths."""
    outcome = _load(OUTCOME_PATH)
    assert outcome["assembly_allowed"] is False
    assert outcome["downstream_allowed"] is False
    assert outcome["assembly_blocked"] is True
    assert outcome["downstream_blocked"] is True
    assert outcome["assembly_executed"] is False
    assert outcome["downstream_executed"] is False
    blocker = _load(BLOCKER_PATH)
    assert blocker["assembly_blocked"] is True
    assert blocker["downstream_blocked"] is True


def test_operator_review_keeps_production_accepted_false():
    """production_accepted must be False in all artifacts."""
    outcome = _load(OUTCOME_PATH)
    routing = _load(ROUTING_PATH)
    blocker = _load(BLOCKER_PATH)
    assert outcome["production_accepted"] is False
    assert routing["production_accepted"] is False
    assert blocker["production_accepted"] is False


def test_pre_state_validated_corrective_generation_result_review_required():
    """Pre-state must be corrective_generation_result_review_required."""
    result_review = _load(RESULT_REVIEW_PATH)
    assert result_review["current_state"] == "corrective_generation_result_review_required"
    assert result_review["next_allowed_action"] == "operator_visual_review_required"
    assert result_review["production_accepted"] is False
    assert result_review["operator_review_required"] is True


def test_generation_count_exactly_one_no_second():
    """generation_count must be 1, max_generations 1, no second generation."""
    manifest = _load(MANIFEST_PATH)
    assert manifest["generation_count"] == 1
    assert manifest["max_generations"] == 1
    assert manifest["stop_after_generation"] is True
    outcome = _load(OUTCOME_PATH)
    assert outcome["generation_count"] == 1
    assert outcome["second_generation_attempted"] is False


def test_asset_exists_with_known_sha256_and_dimensions():
    """Generated asset must exist and match known sha256/size/dimensions."""
    assert os.path.isfile(ASSET_PATH), f"Asset not found: {ASSET_PATH}"
    result_review = _load(RESULT_REVIEW_PATH)
    asset = result_review["generated_assets"][0]
    assert asset["sha256"] == KNOWN_SHA256
    assert asset["width"] == 1024
    assert asset["height"] == 1024
    assert asset["size_bytes"] > 0
    assert asset["exists"] is True


def test_prompt_id_is_real_not_dry_run():
    """prompt_id must be a real UUID, not dry-run placeholder."""
    manifest = _load(MANIFEST_PATH)
    prompt_id = manifest["prompt_id"]
    assert prompt_id == KNOWN_PROMPT_ID
    assert "dry-run" not in str(prompt_id).lower()
    assert prompt_id is not None


def test_outcome_sha256_matches_manifest():
    """outcome sha256 must match the corrective_generation_result_review sha256."""
    outcome = _load(OUTCOME_PATH)
    result_review = _load(RESULT_REVIEW_PATH)
    assert outcome["reviewed_asset_sha256"] == result_review["generated_assets"][0]["sha256"]
    assert outcome["reviewed_asset_sha256"] == KNOWN_SHA256


def test_blocker_artifact_exists_when_no_verdict():
    """operator_visual_review_blocker.json must exist when no verdict provided."""
    assert os.path.isfile(BLOCKER_PATH)
    blocker = _load(BLOCKER_PATH)
    assert blocker["blocker_active"] is True
    assert blocker["blocker_type"] == "missing_operator_visual_verdict"


def test_current_state_remains_operator_visual_review_required():
    """State must remain at operator_visual_review_required."""
    outcome = _load(OUTCOME_PATH)
    routing = _load(ROUTING_PATH)
    blocker = _load(BLOCKER_PATH)
    assert outcome["current_state"] == "operator_visual_review_required"
    assert outcome["next_allowed_action"] == "operator_visual_review_required"
    assert routing["current_state"] == "operator_visual_review_required"
    assert blocker["current_state"] == "operator_visual_review_required"


def test_no_generation_performed_in_this_task():
    """This task must not have performed any generation."""
    outcome = _load(OUTCOME_PATH)
    assert outcome["generation_performed"] is False
    assert outcome["comfyui_submit_executed"] is False
    assert outcome["retry_attempted"] is False


def test_no_visual_qa_executed():
    """Visual QA must not have been executed (blocked)."""
    outcome = _load(OUTCOME_PATH)
    assert outcome["visual_qa_executed"] is False
    assert outcome["visual_qa_blocked"] is True


def test_artifact_index_updated():
    """artifact_index.json must reference all three new artifacts."""
    index = _load(ARTIFACT_INDEX_PATH)
    assert "operator_visual_review_outcome" in index
    assert "post_operator_visual_review_routing_decision" in index
    assert "operator_visual_review_blocker" in index
    assert index["operator_visual_review_blocker_active"] is True
    assert index["fake_operator_decision_created"] is False


def test_episode_ledger_updated():
    """episode_ledger.json must contain the blocker event for this task."""
    ledger = _load(EPISODE_LEDGER_PATH)
    task_events = [e for e in ledger if e.get("task_id") == "RC-COMBINE-V2-FRESH-VISUAL-OPERATOR-REVIEW-001"]
    assert len(task_events) >= 1
    blocker_events = [e for e in task_events if e.get("event_type") == "operator_visual_review_blocker_created"]
    assert len(blocker_events) == 1
    ev = blocker_events[0]
    assert ev["blocker_type"] == "missing_operator_visual_verdict"
    assert ev["production_accepted"] is False
    assert ev["fake_operator_decision_created"] is False
