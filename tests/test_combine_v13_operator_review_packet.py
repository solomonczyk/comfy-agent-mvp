"""Tests for V13 operator visual review packet.

Verifies packet structure, decision placeholders, mouth/teeth defect checklist,
negative reference pointers, and production guard fields.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

V13_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"


class TestV13OperatorReviewPacket:
    """Verify operator visual review packet structure and content."""

    def test_packet_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        assert path.exists()

    def test_packet_required_fields(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("candidate_version") == "v13"
        assert packet.get("asset_path") is not None
        assert packet.get("prompt_id") is not None
        assert packet.get("sha256") is not None

    def test_dimensions_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        dims = packet.get("dimensions", {})
        assert dims.get("width", 0) > 0
        assert dims.get("height", 0) > 0

    def test_qa_canon_engine_summary_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        summary = packet.get("qa_canon_engine_summary", {})
        assert summary.get("decision") is not None
        assert isinstance(summary.get("detected_defects"), list)
        assert isinstance(summary.get("critical_failures"), list)

    def test_mouth_teeth_defect_checklist_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        checklist = packet.get("mouth_teeth_defect_checklist", {})
        assert "bad_teeth" in checklist
        assert "unnatural_mouth" in checklist
        assert "lip_teeth_boundary_failed" in checklist

    def test_negative_reference_pointer_to_v12(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        neg_ref = packet.get("negative_reference", {})
        assert neg_ref is not None
        assert "v12_bad_teeth" in str(neg_ref.get("v12_bad_teeth_reference", ""))

    def test_operator_verdict_not_recorded(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("operator_visual_verdict_recorded") is False

    def test_operator_decision_is_null(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("operator_decision") is None

    def test_allowed_operator_decisions(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        allowed = packet.get("allowed_operator_decisions", [])
        assert "accepted" in allowed
        assert "rejected" in allowed
        assert "needs_manual_review" in allowed
        assert len(allowed) == 3

    def test_production_not_accepted(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("production_accepted") is False

    def test_assembly_and_downstream_blocked(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("assembly_allowed") is False
        assert packet.get("downstream_allowed") is False

    def test_current_state_correct(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("current_state") == "v13_operator_visual_review_required"
        assert packet.get("next_allowed_action") == "v13_operator_visual_review_required"

    def test_instruction_for_operator_present(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        instruction = packet.get("instruction", "")
        assert instruction and len(instruction) > 10
        assert "operator" in instruction.lower()


class TestV13ResultReview:
    """Verify V13 result review artifact."""

    def test_result_review_exists(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        assert path.exists()

    def test_result_review_required_fields(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        with open(path) as f:
            review = json.load(f)

        assert review.get("candidate_version") == "v13"
        assert review.get("v13_generation_authorized") is True
        assert review.get("generation_count") == 1
        assert review.get("max_generations") == 1
        assert review.get("workflow_submitted") is True
        assert review.get("comfyui_execution") is True

    def test_result_review_has_prompt_id(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        with open(path) as f:
            review = json.load(f)

        pid = review.get("prompt_id", "")
        assert pid and pid.strip(), "prompt_id must not be empty"
        parts = pid.split("-")
        assert len(parts) == 5, f"Not a valid UUID: {pid}"

    def test_result_review_asset_validated(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        with open(path) as f:
            review = json.load(f)

        assert review.get("asset_readable") is True
        assert review.get("sha256_present") is True
        assert review.get("stub_asset_detected") is False

    def test_result_review_operator_review_required(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        with open(path) as f:
            review = json.load(f)

        assert review.get("operator_visual_review_required") is True
        assert review.get("operator_visual_verdict_recorded") is False

    def test_result_review_production_guards(self):
        path = Path(V13_CONTROL_DIR) / "combine_v2_v13_result_review.json"
        with open(path) as f:
            review = json.load(f)

        assert review.get("production_accepted") is False
        assert review.get("assembly_executed") is False
        assert review.get("downstream_executed") is False


class TestArtifactIndex:
    """Verify artifact_index.json is correctly updated."""

    def test_index_state_correct(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("current_state") == "v13_operator_visual_review_required"
        assert idx.get("next_allowed_action") == "v13_operator_visual_review_required"

    def test_index_production_guards(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("production_accepted") is False
        assert idx.get("assembly_executed") is False
        assert idx.get("downstream_executed") is False
        assert idx.get("visual_acceptance_executed") is False
        assert idx.get("operator_visual_verdict_recorded") is False

    def test_index_v13_artifact_pointers(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v13_preflight_completed") is True
        assert idx.get("v13_generation_authorized") is True
        assert idx.get("v13_generation_executed") is True
        assert idx.get("v13_qa_canon_report_created") is True
        assert idx.get("v13_result_review_created") is True
        assert idx.get("v13_operator_visual_review_packet_created") is True

    def test_index_v13_artifact_paths(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert "combine_v2_v13_preflight_report.json" in str(idx.get("v13_preflight_report", ""))
        assert "combine_v2_v13_generation_authorization.json" in str(
            idx.get("v13_generation_authorization", "")
        )
        assert "combine_v2_v13_generation_result.json" in str(idx.get("v13_generation_result", ""))
        assert "combine_v2_v13_qa_canon_report.json" in str(
            idx.get("v13_qa_canon_report", "")
        )
        assert "combine_v2_v13_result_review.json" in str(idx.get("v13_result_review", ""))
        assert "combine_v2_v13_operator_visual_review_packet.json" in str(
            idx.get("v13_operator_visual_review_packet", "")
        )

    def test_index_v13_asset_present(self):
        path = Path(V13_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v13_asset_generated") is True
        assert "v13" in str(idx.get("v13_asset_path", ""))


class TestEpisodeLedger:
    """Verify episode_ledger.json V13 events."""

    def test_ledger_has_v13_events(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        v13_events = [e for e in ledger if e.get("version") == "v13"]
        assert len(v13_events) >= 6, f"Expected at least 6 V13 events, got {len(v13_events)}"

    def test_ledger_has_preflight_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        preflight = [e for e in ledger if e.get("event_type") == "v13_preflight_completed"]
        assert len(preflight) >= 1

    def test_ledger_has_authorization_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        auth = [e for e in ledger if e.get("event_type") == "v13_generation_authorized"]
        assert len(auth) >= 1

    def test_ledger_has_generation_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        gen = [e for e in ledger if e.get("event_type") == "v13_generation_executed"]
        assert len(gen) >= 1
        assert gen[0].get("comfyui_execution") is True
        assert gen[0].get("workflow_submitted") is True

    def test_ledger_has_qa_canon_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        qa = [e for e in ledger if e.get("event_type") == "v13_qa_canon_report_created"]
        assert len(qa) >= 1

    def test_ledger_has_review_packet_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        rp = [
            e
            for e in ledger
            if e.get("event_type") == "v13_operator_visual_review_packet_created"
        ]
        assert len(rp) >= 1

    def test_ledger_has_pipeline_stopped_event(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        stopped = [
            e for e in ledger if e.get("event_type") == "pipeline_stopped_at_operator_review"
        ]
        assert len(stopped) >= 1

    def test_ledger_production_guards_on_v13_events(self):
        path = Path(V13_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        for event in ledger:
            if event.get("version") == "v13" and "production_accepted" in event:
                assert event["production_accepted"] is False, \
                    f"production_accepted must be False for all V13 events: {event.get('event_type')}"
