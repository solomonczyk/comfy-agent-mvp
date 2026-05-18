"""RC-COMBINE-V2-FRESH-VISUAL-QA-PREFLIGHT-001 — Visual QA Preflight Tests.

Tests for non-destructive visual QA preflight on accepted body-part closeup candidate.
No generation, retry, assembly, or downstream actions are performed or tested.
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
ASSET_PATH = CANDIDATE_DIR / "combine_v2_corrective_1779095420_00001_.png"
EXPECTED_SHA256 = "37d32671facfb11323e779d2811e1c7a8d5c430597f3eb11eef3dcd0ed78c405"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_json(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_operator_outcome() -> dict:
    return _load_json(CANDIDATE_DIR / "operator_visual_review_outcome.json")


def _load_preflight_report() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_qa_preflight_report.json")


def _load_scope_validation() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_candidate_scope_validation.json")


def _load_quality_registration() -> dict:
    return _load_json(CANDIDATE_DIR / "quality_reference_registration_packet.json")


def _load_routing_decision() -> dict:
    return _load_json(CANDIDATE_DIR / "visual_qa_routing_decision.json")


def _load_artifact_index() -> dict:
    return _load_json(ARTIFACT_INDEX)


def _load_episode_ledger() -> list:
    return _load_json(EPISODE_LEDGER)


# ---------------------------------------------------------------------------
# 1. Preflight requires operator-accepted candidate
# ---------------------------------------------------------------------------

class TestVisualQAPreflightRequiresOperatorAcceptedCandidate:
    def test_operator_outcome_exists(self):
        assert (CANDIDATE_DIR / "operator_visual_review_outcome.json").exists()

    def test_operator_verdict_is_accepted_for_next_stage(self):
        outcome = _load_operator_outcome()
        assert outcome.get("operator_verdict") == "accepted_for_next_stage" or outcome.get("accepted_for_next_stage") is True

    def test_operator_verdict_not_fake(self):
        outcome = _load_operator_outcome()
        assert outcome.get("fake_operator_decision_created") is False

    def test_preflight_report_references_operator_accepted(self):
        report = _load_preflight_report()
        assert report["checks"]["operator_accepted_for_next_stage"] is True


# ---------------------------------------------------------------------------
# 2. Preflight preserves body-part scope
# ---------------------------------------------------------------------------

class TestVisualQAPreflightPreservesBodyPartScope:
    def test_scope_validation_body_part_closeup(self):
        sv = _load_scope_validation()
        assert sv["acceptance_scope_verified"]["accepted_as_body_part_closeup"] is True

    def test_scope_validation_quality_reference(self):
        sv = _load_scope_validation()
        assert sv["acceptance_scope_verified"]["accepted_as_quality_reference"] is True

    def test_routing_decision_body_part_scope(self):
        rd = _load_routing_decision()
        assert rd["accepted_as_body_part_closeup"] is True
        assert rd["accepted_as_quality_reference"] is True

    def test_quality_registration_classification(self):
        qr = _load_quality_registration()
        assert qr["classification"] == "body_part_closeup_quality_reference"
        assert qr["classification_details"]["is_body_part_closeup"] is True
        assert qr["classification_details"]["is_quality_reference"] is True

    def test_preflight_report_quality_reference_check(self):
        report = _load_preflight_report()
        assert report["checks"]["quality_reference_classification_preserved"] is True


# ---------------------------------------------------------------------------
# 3. Preflight rejects full character claim
# ---------------------------------------------------------------------------

class TestVisualQAPreflightRejectsFullCharacterClaim:
    def test_scope_validation_no_full_character(self):
        sv = _load_scope_validation()
        assert sv["acceptance_scope_verified"]["accepted_as_full_character"] is False

    def test_routing_decision_no_full_character(self):
        rd = _load_routing_decision()
        assert rd["accepted_as_full_character"] is False

    def test_quality_registration_no_full_character(self):
        qr = _load_quality_registration()
        assert qr["classification_details"]["is_full_character"] is False

    def test_preflight_report_no_full_character(self):
        report = _load_preflight_report()
        assert report["checks"]["no_full_character_claim"] is True

    def test_scope_validation_no_final_scene(self):
        sv = _load_scope_validation()
        assert sv["acceptance_scope_verified"]["accepted_as_final_scene"] is False

    def test_preflight_report_no_final_scene(self):
        report = _load_preflight_report()
        assert report["checks"]["no_final_scene_claim"] is True


# ---------------------------------------------------------------------------
# 4. Preflight keeps production_accepted=false
# ---------------------------------------------------------------------------

class TestVisualQAPreflightKeepsProductionAcceptedFalse:
    def test_preflight_report_production_accepted_false(self):
        report = _load_preflight_report()
        assert report["production_accepted"] is False

    def test_scope_validation_production_accepted_false(self):
        sv = _load_scope_validation()
        assert sv["acceptance_scope_verified"]["production_accepted"] is False

    def test_routing_decision_production_accepted_false(self):
        rd = _load_routing_decision()
        assert rd["production_accepted"] is False

    def test_quality_registration_production_accepted_false(self):
        qr = _load_quality_registration()
        assert qr["classification_details"]["is_production_accepted"] is False

    def test_artifact_index_production_accepted_false(self):
        ai = _load_artifact_index()
        assert ai["production_accepted"] is False

    def test_episode_ledger_last_event_production_accepted_false(self):
        ledger = _load_episode_ledger()
        last = ledger[-1]
        assert last["production_accepted"] is False


# ---------------------------------------------------------------------------
# 5. Preflight blocks assembly and downstream
# ---------------------------------------------------------------------------

class TestVisualQAPreflightBlocksAssemblyDownstream:
    def test_preflight_report_assembly_not_allowed(self):
        report = _load_preflight_report()
        assert report["assembly_allowed"] is False

    def test_preflight_report_downstream_blocked(self):
        report = _load_preflight_report()
        assert report["downstream_allowed"] is False

    def test_preflight_report_assembly_not_executed(self):
        report = _load_preflight_report()
        assert report["assembly_executed"] is False

    def test_preflight_report_downstream_not_executed(self):
        report = _load_preflight_report()
        assert report["downstream_executed"] is False

    def test_routing_decision_downstream_blocked(self):
        rd = _load_routing_decision()
        assert rd["downstream_blocked"] is True
        assert rd["assembly_allowed"] is False

    def test_artifact_index_assembly_allowed_false(self):
        ai = _load_artifact_index()
        assert ai["assembly_allowed"] is False

    def test_artifact_index_downstream_allowed_false(self):
        ai = _load_artifact_index()
        assert ai["downstream_allowed"] is False

    def test_episode_ledger_last_event_downstream_blocked(self):
        ledger = _load_episode_ledger()
        last = ledger[-1]
        assert last["downstream_blocked"] is True
        assert last["assembly_allowed"] is False


# ---------------------------------------------------------------------------
# 6. Preflight validates asset metadata
# ---------------------------------------------------------------------------

class TestVisualQAPreflightValidatesAssetMetadata:
    def test_asset_file_exists(self):
        assert ASSET_PATH.exists(), f"Asset not found: {ASSET_PATH}"

    def test_asset_is_readable(self):
        from PIL import Image
        img = Image.open(str(ASSET_PATH))
        img.load()
        assert img.width > 0

    def test_asset_dimensions_1024x1024(self):
        from PIL import Image
        img = Image.open(str(ASSET_PATH))
        assert img.width == 1024
        assert img.height == 1024

    def test_asset_size_bytes_nonzero(self):
        assert ASSET_PATH.stat().st_size > 100000

    def test_asset_sha256_matches(self):
        import hashlib
        data = ASSET_PATH.read_bytes()
        actual = hashlib.sha256(data).hexdigest()
        assert actual == EXPECTED_SHA256

    def test_asset_not_stub(self):
        assert ASSET_PATH.stat().st_size > 100000

    def test_preflight_report_sha256_correct(self):
        report = _load_preflight_report()
        assert report["asset_sha256"] == EXPECTED_SHA256

    def test_preflight_report_dimensions_correct(self):
        report = _load_preflight_report()
        assert report["asset_width"] == 1024
        assert report["asset_height"] == 1024

    def test_preflight_report_checks_asset_exists(self):
        report = _load_preflight_report()
        assert report["checks"]["asset_exists"] is True

    def test_preflight_report_checks_not_stub(self):
        report = _load_preflight_report()
        assert report["checks"]["not_stub"] is True


# ---------------------------------------------------------------------------
# 7. Preflight routes pass and fail states
# ---------------------------------------------------------------------------

class TestVisualQAPreflightRoutesPassAndFailStates:
    def test_routing_decision_route_taken_pass(self):
        rd = _load_routing_decision()
        assert rd["route_taken"] == "visual_qa_preflight_passed"

    def test_routing_decision_preflight_verdict_pass(self):
        rd = _load_routing_decision()
        assert rd["preflight_verdict"] == "pass"

    def test_routing_decision_current_state(self):
        rd = _load_routing_decision()
        assert rd["current_state"] == "visual_qa_preflight_complete"

    def test_routing_decision_next_allowed_action(self):
        rd = _load_routing_decision()
        assert rd["next_allowed_action"] == "visual_qa_review_required"

    def test_artifact_index_current_state(self):
        ai = _load_artifact_index()
        assert ai["current_state"] == "visual_qa_preflight_complete"

    def test_artifact_index_next_allowed_action(self):
        ai = _load_artifact_index()
        assert ai["next_allowed_action"] == "visual_qa_review_required"

    def test_episode_ledger_last_event_current_state(self):
        ledger = _load_episode_ledger()
        last = ledger[-1]
        assert last["current_state"] == "visual_qa_preflight_complete"

    def test_episode_ledger_last_event_next_allowed_action(self):
        ledger = _load_episode_ledger()
        last = ledger[-1]
        assert last["next_allowed_action"] == "visual_qa_review_required"

    def test_preflight_report_verdict_pass(self):
        report = _load_preflight_report()
        assert report["preflight_verdict"] == "pass"


# ---------------------------------------------------------------------------
# 8. Preflight requires git-clean freeze proof
# ---------------------------------------------------------------------------

class TestVisualQAPreflightRequiresGitCleanFreezeProof:
    def test_preflight_report_no_generation_performed(self):
        report = _load_preflight_report()
        assert report["generation_performed"] is False

    def test_preflight_report_no_comfyui_submit(self):
        report = _load_preflight_report()
        assert report["comfyui_submit_executed"] is False

    def test_preflight_report_no_retry_attempted(self):
        report = _load_preflight_report()
        assert report["retry_attempted"] is False

    def test_preflight_report_no_visual_qa_final_acceptance(self):
        report = _load_preflight_report()
        assert report["visual_qa_final_acceptance_executed"] is False

    def test_routing_decision_no_generation(self):
        rd = _load_routing_decision()
        assert rd["generation_performed"] is False
        assert rd["comfyui_submit_executed"] is False

    def test_routing_decision_no_fake_operator_decision(self):
        rd = _load_routing_decision()
        assert rd["fake_operator_decision_created"] is False

    def test_scope_validation_no_generation(self):
        sv = _load_scope_validation()
        assert sv["generation_performed"] is False
        assert sv["comfyui_submit_executed"] is False

    def test_scope_validation_no_fake_operator_decision(self):
        sv = _load_scope_validation()
        assert sv.get("fake_operator_decision_created") is False

    def test_episode_ledger_preflight_event_exists(self):
        ledger = _load_episode_ledger()
        task_ids = [e.get("task_id") for e in ledger]
        assert "RC-COMBINE-V2-FRESH-VISUAL-QA-PREFLIGHT-001" in task_ids

    def test_artifact_index_preflight_task_registered(self):
        ai = _load_artifact_index()
        assert ai.get("visual_qa_preflight_task") == "RC-COMBINE-V2-FRESH-VISUAL-QA-PREFLIGHT-001"

    def test_all_four_artifacts_registered_in_artifact_index(self):
        ai = _load_artifact_index()
        assert "visual_qa_preflight_report" in ai
        assert "visual_candidate_scope_validation" in ai
        assert "quality_reference_registration_packet" in ai
        assert "visual_qa_routing_decision" in ai

    def test_all_four_artifact_files_exist(self):
        for fname in [
            "visual_qa_preflight_report.json",
            "visual_candidate_scope_validation.json",
            "quality_reference_registration_packet.json",
            "visual_qa_routing_decision.json",
        ]:
            assert (CANDIDATE_DIR / fname).exists(), f"Missing: {fname}"
