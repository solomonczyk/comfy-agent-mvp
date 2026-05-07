"""RC-COMBINE-V2-3601-3900 — State machine and operator gate tests for v6 candidate."""
from __future__ import annotations

import json
from pathlib import Path

CONTROL_DIR = Path(
    "F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control"
)


def _load(name: str) -> dict:
    p = CONTROL_DIR / name
    assert p.exists(), f"Missing: {name}"
    with open(p, "r", encoding="utf-8") as fh:
        return json.load(fh)


def test_current_state_is_operator_visual_review_required():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("current_state") == "operator_visual_review_required"
    assert data.get("next_allowed_action") == "operator_visual_review_required"


def test_second_generation_attempted_is_false():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("second_generation_attempted") is False


def test_new_generation_performed_is_true():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("new_generation_performed") is True


def test_workflow_submitted_and_executed():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("workflow_submitted") is True
    assert data.get("comfyui_execution") is True


def test_episode_ledger_has_v6_event():
    ledger_path = CONTROL_DIR / "episode_ledger.json"
    assert ledger_path.exists(), "episode_ledger.json must exist"
    with open(ledger_path, "r", encoding="utf-8") as fh:
        ledger = json.load(fh)
    events = ledger if isinstance(ledger, list) else ledger.get("events", [])
    v6_events = [
        e for e in events
        if e.get("event_type") == "clean_sdxl_v6_candidate_generation_completed"
    ]
    assert len(v6_events) >= 1, "episode_ledger must contain v6 generation event"
    ev = v6_events[-1]
    assert ev.get("generation_count") == 1
    assert ev.get("production_accepted") is False
    assert ev.get("operator_visual_review_required") is True


def test_review_packet_forbidden_actions():
    data = _load("combine_v2_visual_quality_recovery_operator_review_packet.json")
    forbidden = data.get("forbidden_automatic_actions", [])
    for action in ("production_acceptance", "assembly", "downstream",
                   "second_generation_attempt", "blind_retry"):
        assert action in forbidden, f"'{action}' must be forbidden"


def test_review_packet_allowed_actions_present():
    data = _load("combine_v2_visual_quality_recovery_operator_review_packet.json")
    allowed = data.get("allowed_operator_actions", [])
    assert len(allowed) >= 1, "At least one allowed operator action must be listed"
    assert "approve_v6_direction" in allowed


def test_baseline_rejection_confirmed_in_artifact_index():
    data = _load("artifact_index.json")
    assert data.get("baseline_rejected_as_production") is True


def test_task_id_in_result():
    data = _load("combine_v2_clean_sdxl_v6_candidate_result.json")
    assert data.get("task_id") == "RC-COMBINE-V2-3601-3900"
