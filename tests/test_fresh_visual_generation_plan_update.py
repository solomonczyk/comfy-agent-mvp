"""
Tests for RC-COMBINE-V2-FRESH-VISUAL-GENERATION-PLAN-UPDATE-001.

Covers:
- quality reference usage as calibration only
- full character / full face / final scene rejection
- generation not authorized
- no ComfyUI submit package
- future operator generation gate required
- blind retry blocked
- production_accepted=false
- artifact index and ledger updated
- dirty carryover scope preserved
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CONTROL_DIR = PROJECT_ROOT / "data/rc2_multishot1_ep01/output/control"
PLAN_DIR = CONTROL_DIR / "fresh_visual_generation_plan"

PLAN_FILE = PLAN_DIR / "fresh_visual_generation_plan.json"
APP_MAP_FILE = PLAN_DIR / "quality_reference_application_map.json"
CONSTRAINTS_FILE = PLAN_DIR / "visual_recipe_constraints.json"
GATE_REQ_FILE = PLAN_DIR / "future_generation_gate_requirements.json"
SCOPE_GUARD_FILE = PLAN_DIR / "generation_plan_scope_guard.json"
UPDATE_REPORT_FILE = PLAN_DIR / "generation_plan_update_report.json"
ARTIFACT_INDEX_FILE = CONTROL_DIR / "artifact_index.json"
EPISODE_LEDGER_FILE = CONTROL_DIR / "episode_ledger.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def plan():
    assert PLAN_FILE.exists(), f"Missing: {PLAN_FILE}"
    return _load(PLAN_FILE)


@pytest.fixture(scope="module")
def app_map():
    assert APP_MAP_FILE.exists(), f"Missing: {APP_MAP_FILE}"
    return _load(APP_MAP_FILE)


@pytest.fixture(scope="module")
def constraints():
    assert CONSTRAINTS_FILE.exists(), f"Missing: {CONSTRAINTS_FILE}"
    return _load(CONSTRAINTS_FILE)


@pytest.fixture(scope="module")
def gate_req():
    assert GATE_REQ_FILE.exists(), f"Missing: {GATE_REQ_FILE}"
    return _load(GATE_REQ_FILE)


@pytest.fixture(scope="module")
def scope_guard():
    assert SCOPE_GUARD_FILE.exists(), f"Missing: {SCOPE_GUARD_FILE}"
    return _load(SCOPE_GUARD_FILE)


@pytest.fixture(scope="module")
def update_report():
    assert UPDATE_REPORT_FILE.exists(), f"Missing: {UPDATE_REPORT_FILE}"
    return _load(UPDATE_REPORT_FILE)


@pytest.fixture(scope="module")
def artifact_index():
    assert ARTIFACT_INDEX_FILE.exists(), f"Missing: {ARTIFACT_INDEX_FILE}"
    return _load(ARTIFACT_INDEX_FILE)


@pytest.fixture(scope="module")
def episode_ledger():
    assert EPISODE_LEDGER_FILE.exists(), f"Missing: {EPISODE_LEDGER_FILE}"
    raw = EPISODE_LEDGER_FILE.read_text(encoding="utf-8")
    return json.loads(raw)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_generation_plan_uses_quality_reference_as_calibration_only(plan, app_map):
    assert plan["quality_reference_id"] == "quality_ref_eye_closeup_001"
    assert plan["quality_reference_usage"] == "quality_calibration_only"
    assert app_map["reference_id"] == "quality_ref_eye_closeup_001"
    assert "eye_detail_quality" in app_map["may_inform"]
    assert "body_part_texture_realism" in app_map["may_inform"]
    assert "sharpness_target" in app_map["may_inform"]


def test_generation_plan_rejects_full_character_reference_usage(plan, app_map, scope_guard):
    assert plan.get("accepted_as_full_character") is not True
    assert "character_identity" in app_map["must_not_define"]
    assert "accepted_as_full_character" in scope_guard["blocked_overclaims"]
    blocked = app_map.get("forbidden_applications", {})
    assert blocked.get("character_identity", {}).get("blocked") is True


def test_generation_plan_rejects_full_face_reference_usage(plan, app_map, scope_guard):
    assert plan.get("accepted_as_full_face") is not True
    assert "full_face_identity" in app_map["must_not_define"]
    assert "accepted_as_full_face" in scope_guard["blocked_overclaims"]
    blocked = app_map.get("forbidden_applications", {})
    assert blocked.get("full_face_identity", {}).get("blocked") is True


def test_generation_plan_rejects_final_scene_usage(plan, app_map, scope_guard):
    assert plan.get("accepted_as_final_scene") is not True
    assert "final_scene_composition" in app_map["must_not_define"]
    assert "accepted_as_final_scene" in scope_guard["blocked_overclaims"]
    blocked = app_map.get("forbidden_applications", {})
    assert blocked.get("final_scene_composition", {}).get("blocked") is True


def test_generation_plan_does_not_authorize_generation(plan, scope_guard):
    assert plan["generation_authorized"] is False
    assert plan["plan_type"] == "future_generation_plan_only"
    assert "generation_authorized" in scope_guard["blocked_overclaims"]
    assert scope_guard["scope_boundary"]["generation_authorized"] is False


def test_generation_plan_does_not_create_comfyui_submit_package(plan, constraints, update_report):
    assert plan["comfyui_submit_authorized"] is False
    assert constraints["runtime_execution_authorized"] is False
    assert constraints["comfyui_submit_authorized"] is False
    assert constraints["workflow_package_created"] is False
    assert update_report["forbidden_actions_blocked"]["executable_comfyui_submit_package_created"] is False
    assert update_report["forbidden_actions_blocked"]["comfyui_submit_executed"] is False


def test_generation_plan_requires_future_operator_generation_gate(plan, gate_req):
    assert plan["requires_separate_generation_gate"] is True
    assert plan["requires_operator_authorization_before_generation"] is True
    assert gate_req["generation_gate_required"] is True
    assert gate_req["operator_authorization_required"] is True
    assert gate_req.get("next_task_required") == "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-GATE-001"


def test_generation_plan_blocks_blind_retry(plan, gate_req, scope_guard):
    assert plan["retry_authorized"] is False
    assert gate_req["blind_retry_allowed"] is False
    assert gate_req.get("gate_semantics", {}).get("gate_cannot_be_opened_by_quality_reference") is True
    assert "generation_authorized" in scope_guard["blocked_overclaims"]


def test_generation_plan_keeps_production_accepted_false(plan, constraints, gate_req, update_report):
    assert plan["production_accepted"] is False
    assert plan["assembly_allowed"] is False
    assert plan["downstream_blocked"] is True
    assert gate_req["production_acceptance_allowed_after_generation"] is False
    assert gate_req["assembly_allowed_after_generation"] is False
    assert update_report["forbidden_actions_blocked"]["production_accepted_set_true"] is False
    assert update_report["scope_boundary_enforced"]["production_accepted"] is False


def test_generation_plan_updates_artifact_index_and_ledger(artifact_index, episode_ledger):
    assert artifact_index.get("fresh_visual_generation_plan_created") is True
    assert artifact_index.get("current_state") == "fresh_visual_generation_plan_updated"
    assert artifact_index.get("next_allowed_action") == "fresh_visual_generation_gate_required"

    ledger_list = episode_ledger if isinstance(episode_ledger, list) else [episode_ledger]
    plan_events = [
        e for e in ledger_list
        if e.get("event_type") == "fresh_visual_generation_plan_updated"
        or e.get("task_id") == "RC-COMBINE-V2-FRESH-VISUAL-GENERATION-PLAN-UPDATE-001"
    ]
    assert len(plan_events) >= 1, "Episode ledger missing generation plan update entry"
    entry = plan_events[-1]
    assert entry.get("production_accepted") is False
    assert entry.get("generation_performed") is False


def test_generation_plan_preserves_dirty_carryover_scope(update_report):
    blocked = update_report["forbidden_actions_blocked"]
    assert blocked["dirty_carryover_staged_or_committed"] is False
    guard = _load(SCOPE_GUARD_FILE)
    assert guard["guard_invariants"]["dirty_carryover_not_modified_by_this_task"] is True
    assert guard["guard_invariants"]["production_accepted_remains_false"] is True
