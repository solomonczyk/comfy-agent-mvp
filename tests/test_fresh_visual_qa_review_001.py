"""RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001 — Visual QA Review Tests.

Tests for standards-based visual QA review of accepted body-part eye closeup
quality reference candidate. No generation, retry, assembly, or downstream.
"""
import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
CANDIDATE_DIR = (
    PROJECT_ROOT
    / "data"
    / "rc2_multishot1_ep01"
    / "output"
    / "control"
    / "fresh_visual_candidate"
)
ARTIFACT_INDEX = (
    PROJECT_ROOT / "data" / "rc2_multishot1_ep01" / "output" / "control" / "artifact_index.json"
)
EPISODE_LEDGER = (
    PROJECT_ROOT / "data" / "rc2_multishot1_ep01" / "output" / "control" / "episode_ledger.json"
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_preflight_report() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_qa_preflight_report.json")


def _load_review_report() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_qa_review_report.json")


def _load_defect_assessment() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_defect_assessment.json")


def _load_qa_decision() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_qa_decision.json")


def _load_qa_packet() -> dict:
    return _load_json(CANDIDATE_DIR / "quality_reference_qa_packet.json")


def _load_scope_validation() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_candidate_scope_validation.json")


def _load_artifact_index() -> dict:
    return _load_json(ARTIFACT_INDEX)


def _load_episode_ledger() -> list:
    with open(EPISODE_LEDGER, "r", encoding="utf-8") as f:
        return json.load(f)


def _latest_ledger_event() -> dict:
    return _load_episode_ledger()[-1]


# ---------------------------------------------------------------------------
# Test 1: Visual QA review requires preflight complete
# ---------------------------------------------------------------------------

def test_visual_qa_review_requires_preflight_complete():
    """Preflight report must confirm current_state=visual_qa_preflight_complete
    and next_allowed_action=visual_qa_review_required before review executes."""
    preflight = _load_preflight_report()
    assert preflight["current_state"] == "visual_qa_preflight_complete", (
        f"Expected visual_qa_preflight_complete, got {preflight['current_state']}"
    )
    assert preflight["next_allowed_action"] == "visual_qa_review_required", (
        f"Expected visual_qa_review_required, got {preflight['next_allowed_action']}"
    )
    assert preflight["preflight_verdict"] == "pass"

    # Review report must reference this pre-state
    review = _load_review_report()
    assert review["previous_state_verified"] == "visual_qa_preflight_complete"
    assert review["next_allowed_action_verified"] == "visual_qa_review_required"
    assert review["previous_commit"] == "bbb0a1b"


# ---------------------------------------------------------------------------
# Test 2: Visual QA review preserves body-part scope
# ---------------------------------------------------------------------------

def test_visual_qa_review_preserves_body_part_scope():
    """Review must preserve accepted_as_body_part_closeup=true and
    accepted_as_quality_reference=true."""
    review = _load_review_report()
    scope = review["candidate_scope"]
    assert scope["accepted_as_body_part_closeup"] is True
    assert scope["accepted_as_quality_reference"] is True

    decision = _load_qa_decision()
    assert decision["scope_preserved"]["accepted_as_body_part_closeup"] is True
    assert decision["scope_preserved"]["accepted_as_quality_reference"] is True

    packet = _load_qa_packet()
    assert packet["scope_boundaries"]["accepted_as_body_part_closeup"] is True
    assert packet["scope_boundaries"]["accepted_as_quality_reference"] is True


# ---------------------------------------------------------------------------
# Test 3: Visual QA review blocks full-character claim
# ---------------------------------------------------------------------------

def test_visual_qa_review_blocks_full_character_claim():
    """accepted_as_full_character and accepted_as_final_scene must remain False."""
    review = _load_review_report()
    scope = review["candidate_scope"]
    assert scope["accepted_as_full_character"] is False
    assert scope["accepted_as_final_scene"] is False

    decision = _load_qa_decision()
    assert decision["scope_preserved"]["accepted_as_full_character"] is False
    assert decision["scope_preserved"]["accepted_as_final_scene"] is False

    packet = _load_qa_packet()
    assert packet["scope_boundaries"]["accepted_as_full_character"] is False
    assert packet["scope_boundaries"]["accepted_as_final_scene"] is False
    assert packet["usage_constraints"]["may_not_be_used_as_full_character"] is True


# ---------------------------------------------------------------------------
# Test 4: Mouth/teeth check recorded as not_applicable for eye closeup
# ---------------------------------------------------------------------------

def test_visual_qa_review_records_mouth_teeth_as_not_applicable_for_eye_closeup():
    """mouth_teeth_check must have result=not_applicable with a reason string."""
    review = _load_review_report()
    mouth_check = review["visual_qa_checks"]["mouth_teeth_check"]
    assert mouth_check["result"] == "not_applicable", (
        f"Expected not_applicable, got {mouth_check['result']}"
    )
    assert "reason" in mouth_check and len(mouth_check["reason"]) > 10

    defect = _load_defect_assessment()
    na_checks = defect["not_applicable_checks"]
    mouth_na = next((c for c in na_checks if c["check"] == "mouth_teeth_check"), None)
    assert mouth_na is not None, "mouth_teeth_check must appear in not_applicable_checks"
    assert mouth_na["blocker"] is False

    ledger_event = _latest_ledger_event()
    assert ledger_event["mouth_teeth_check"] == "not_applicable"
    assert "eye" in ledger_event["mouth_teeth_not_applicable_reason"].lower()


# ---------------------------------------------------------------------------
# Test 5: Visual QA review keeps production_accepted False
# ---------------------------------------------------------------------------

def test_visual_qa_review_keeps_production_accepted_false():
    """production_accepted must be False in all review artifacts."""
    review = _load_review_report()
    assert review["production_accepted"] is False

    decision = _load_qa_decision()
    assert decision["state_routing"]["production_accepted"] is False
    assert decision["forbidden_actions_confirmed_not_executed"]["production_accepted_set_true"] is False

    packet = _load_qa_packet()
    assert packet["production_accepted"] is False
    assert packet["scope_boundaries"]["production_accepted"] is False

    defect = _load_defect_assessment()
    assert defect["production_accepted"] is False

    index = _load_artifact_index()
    assert index["production_accepted"] is False

    ledger_event = _latest_ledger_event()
    assert ledger_event["production_accepted"] is False


# ---------------------------------------------------------------------------
# Test 6: Visual QA review blocks assembly and downstream
# ---------------------------------------------------------------------------

def test_visual_qa_review_blocks_assembly_downstream():
    """assembly_allowed and downstream_blocked must be enforced in all artifacts."""
    review = _load_review_report()
    assert review["assembly_allowed"] is False
    assert review["downstream_blocked"] is True

    decision = _load_qa_decision()
    assert decision["state_routing"]["assembly_allowed"] is False
    assert decision["state_routing"]["downstream_blocked"] is True
    assert decision["forbidden_actions_confirmed_not_executed"]["assembly_executed"] is False
    assert decision["forbidden_actions_confirmed_not_executed"]["downstream_executed"] is False

    packet = _load_qa_packet()
    assert packet["assembly_allowed"] is False
    assert packet["downstream_blocked"] is True
    assert packet["usage_constraints"]["may_not_be_assembly_submitted"] is True
    assert packet["usage_constraints"]["may_not_trigger_downstream"] is True

    index = _load_artifact_index()
    assert index["assembly_allowed"] is False
    assert index["downstream_blocked"] is True

    ledger_event = _latest_ledger_event()
    assert ledger_event["assembly_allowed"] is False
    assert ledger_event["downstream_blocked"] is True


# ---------------------------------------------------------------------------
# Test 7: Visual QA review routes pass/warning/fail/manual_review correctly
# ---------------------------------------------------------------------------

def test_visual_qa_review_routes_pass_warning_fail_manual_review():
    """QA decision must be one of the four allowed outcomes and route correctly."""
    decision = _load_qa_decision()
    allowed_outcomes = {
        "visual_qa_passed_for_quality_reference",
        "visual_qa_passed_with_warnings",
        "visual_qa_failed",
        "manual_review_required",
    }
    assert set(decision["allowed_outcomes_checked"]) == allowed_outcomes
    assert decision["qa_decision"] in allowed_outcomes

    # For pass: state routing must be correct
    if decision["qa_decision"] == "visual_qa_passed_for_quality_reference":
        assert decision["state_routing"]["current_state"] == "visual_qa_review_complete"
        assert decision["state_routing"]["next_allowed_action"] == "quality_reference_registration_required"

    # Review report must carry the same verdict
    review = _load_review_report()
    assert review["review_verdict"] == decision["qa_decision"]
    assert review["current_state"] == decision["state_routing"]["current_state"]
    assert review["next_allowed_action"] == decision["state_routing"]["next_allowed_action"]

    # Artifact index must be updated to new state
    index = _load_artifact_index()
    assert index["current_state"] == decision["state_routing"]["current_state"]
    assert index["next_allowed_action"] == decision["state_routing"]["next_allowed_action"]


# ---------------------------------------------------------------------------
# Test 8: Visual QA review requires committed artifacts
# ---------------------------------------------------------------------------

def test_visual_qa_review_requires_committed_artifacts():
    """All four required review artifacts must exist on disk."""
    required = [
        CANDIDATE_DIR / "visual_qa_review_report.json",
        CANDIDATE_DIR / "visual_defect_assessment.json",
        CANDIDATE_DIR / "visual_qa_decision.json",
        CANDIDATE_DIR / "quality_reference_qa_packet.json",
    ]
    for path in required:
        assert path.exists(), f"Missing required artifact: {path}"
        data = path.read_bytes()
        assert len(data) > 50, f"Artifact suspiciously small: {path}"
        # Must be valid JSON
        parsed = json.loads(data)
        assert isinstance(parsed, dict)
        assert parsed.get("task_id") == "RC-COMBINE-V2-FRESH-VISUAL-QA-REVIEW-001"

    # Artifact index must reference all four
    index = _load_artifact_index()
    assert "visual_qa_review_report" in index
    assert "visual_defect_assessment" in index
    assert "visual_qa_decision" in index
    assert "quality_reference_qa_packet" in index

    # Episode ledger last event must reference all four
    ledger_event = _latest_ledger_event()
    artifacts = ledger_event.get("artifacts_created", [])
    assert any("visual_qa_review_report" in a for a in artifacts)
    assert any("visual_defect_assessment" in a for a in artifacts)
    assert any("visual_qa_decision" in a for a in artifacts)
    assert any("quality_reference_qa_packet" in a for a in artifacts)
