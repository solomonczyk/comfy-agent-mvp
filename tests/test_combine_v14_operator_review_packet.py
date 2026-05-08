"""Tests for V14 operator visual review packet and artifact index.

Verifies pre-generation artifact structure, state transitions,
production guards, and episode ledger entries for V14 success case.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

V14_CONTROL_DIR = "data/rc2_multishot1_ep01/output/control"


class TestV14ArtifactIndex:
    """Verify artifact_index.json is correctly updated for V14."""

    def test_index_state(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("current_state") == "v14_operator_visual_review_required"
        assert idx.get("next_allowed_action") == "v14_operator_visual_review_required"

    def test_index_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("production_accepted") is False
        assert idx.get("assembly_executed") is False
        assert idx.get("downstream_executed") is False
        assert idx.get("visual_acceptance_executed") is False

    def test_index_v13_rejection_recorded(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v13_operator_rejection_recorded") is True
        assert idx.get("v13_decision") == "rejected"
        assert idx.get("framing_defects_registered") is True

    def test_index_v14_correction_package_created(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v14_correction_plan_created") is True
        assert idx.get("v14_prompt_patch_created") is True
        assert idx.get("v14_workflow_patch_created") is True
        assert idx.get("v14_quality_pipeline_patch_created") is True

    def test_index_v14_generation_authorized(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v14_generation_authorized") is True
        assert idx.get("candidate_version") == "v14"

    def test_index_v14_generation_succeeded(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v14_generation_attempted") is True
        assert idx.get("v14_generation_succeeded") is True
        assert idx.get("comfyui_execution") is True

    def test_index_no_second_generation(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("second_v14_generation_attempted") is False
        assert idx.get("blind_retry_attempted") is False

    def test_index_post_gen_artifacts_created(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v14_outputs_manifest_created") is True
        assert idx.get("v14_qa_canon_report_created") is True
        assert idx.get("v14_result_review_created") is True
        assert idx.get("v14_operator_visual_review_packet_created") is True

    def test_index_v14_artifact_paths(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert "combine_v2_v14_correction_plan.json" in str(idx.get("v14_correction_plan", ""))
        assert "combine_v2_v14_prompt_patch.json" in str(idx.get("v14_prompt_patch", ""))
        assert "combine_v2_v14_generation_authorization.json" in str(
            idx.get("v14_generation_authorization", "")
        )
        assert "combine_v2_v14_outputs_manifest.json" in str(
            idx.get("v14_outputs_manifest", "")
        )
        assert "combine_v2_v14_qa_canon_report.json" in str(
            idx.get("v14_qa_canon_report", "")
        )
        assert "combine_v2_v14_result_review.json" in str(
            idx.get("v14_result_review", "")
        )
        assert "combine_v2_v14_operator_visual_review_packet.json" in str(
            idx.get("v14_operator_visual_review_packet", "")
        )

    def test_index_v14_asset_present(self):
        path = Path(V14_CONTROL_DIR) / "artifact_index.json"
        with open(path) as f:
            idx = json.load(f)

        assert idx.get("v14_asset_generated") is True
        assert "v14" in str(idx.get("v14_asset_path", ""))


class TestV14EpisodeLedger:
    """Verify episode_ledger.json has correct V14 events."""

    def test_ledger_has_v14_events(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        v14_events = [e for e in ledger if e.get("version") == "v14"]
        assert len(v14_events) >= 5, f"Expected at least 5 V14 events, got {len(v14_events)}"

    def test_ledger_has_rejection_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        rejection = [e for e in ledger if e.get("event_type") == "v13_operator_rejection_recorded"]
        assert len(rejection) >= 1

    def test_ledger_has_correction_package_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        package = [e for e in ledger if e.get("event_type") == "v14_correction_package_created"]
        assert len(package) >= 1

    def test_ledger_has_authorization_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        auth = [e for e in ledger if e.get("event_type") == "v14_generation_authorized"]
        assert len(auth) >= 1

    def test_ledger_has_generation_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        gen = [e for e in ledger if e.get("event_type") == "v14_generation_executed"]
        assert len(gen) >= 1

    def test_ledger_has_qa_canon_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        qa = [e for e in ledger if e.get("event_type") == "v14_qa_canon_report_created"]
        assert len(qa) >= 1

    def test_ledger_has_review_packet_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        rp = [e for e in ledger if e.get("event_type") == "v14_operator_visual_review_packet_created"]
        assert len(rp) >= 1

    def test_ledger_has_pipeline_stopped_event(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        stopped = [e for e in ledger if e.get("event_type") == "pipeline_stopped_at_operator_review"]
        assert len(stopped) >= 1

    def test_ledger_production_guards_on_v14_events(self):
        path = Path(V14_CONTROL_DIR) / "episode_ledger.json"
        with open(path) as f:
            ledger = json.load(f)

        for event in ledger:
            if event.get("version") == "v14" and "production_accepted" in event:
                assert event["production_accepted"] is False, \
                    f"production_accepted must be False for all V14 events: {event.get('event_type')}"


class TestV14ProductionGuards:
    """Verify production guard fields across all artifacts."""

    def test_rejection_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        with open(path) as f:
            rejection = json.load(f)

        assert rejection.get("production_accepted") is False

    def test_correction_plan_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_correction_plan.json"
        with open(path) as f:
            plan = json.load(f)

        assert plan.get("production_accepted") is False
        assert plan.get("assembly_allowed") is False
        assert plan.get("downstream_allowed") is False

    def test_authorization_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            auth = json.load(f)

        assert auth.get("production_acceptance_allowed") is False
        assert auth.get("assembly_allowed") is False
        assert auth.get("downstream_allowed") is False

    def test_generation_result_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_result.json"
        with open(path) as f:
            result = json.load(f)
        assert result.get("production_accepted") is False or "production_accepted" not in result

    def test_operator_review_packet_production_guards(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)
        assert packet.get("production_accepted") is False
        assert packet.get("assembly_allowed") is False
        assert packet.get("downstream_allowed") is False


class TestV14PreGenerationArtifacts:
    """Verify pre-generation artifacts exist and have correct structure."""

    def test_v13_rejection_has_all_required_fields(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v13_operator_visual_rejection.json"
        with open(path) as f:
            r = json.load(f)

        assert r.get("candidate_version") == "v13"
        assert r.get("operator_decision") == "rejected"
        assert r.get("rejection_reason")
        assert isinstance(r.get("defects"), list)
        assert isinstance(r.get("positive_to_preserve"), list)

    def test_generation_authorization_has_correct_structure(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_generation_authorization.json"
        with open(path) as f:
            a = json.load(f)

        assert a.get("candidate_version") == "v14"
        assert a.get("generation_authorized") is True
        assert a.get("max_generations") == 1
        assert a.get("second_generation_forbidden") is True
        assert a.get("blind_retry_forbidden") is True

    def test_operator_review_packet_has_correct_structure(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        assert packet.get("candidate_version") == "v14"
        assert packet.get("asset_path") is not None
        assert packet.get("prompt_id") is not None
        assert packet.get("sha256") is not None
        assert packet.get("operator_visual_verdict_recorded") is False
        assert packet.get("operator_decision") is None

    def test_operator_review_packet_contains_framing_checklist(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        checklist = packet.get("framing_checklist", {})
        assert "full_head_visible" in checklist
        assert "top_of_head_not_cropped" in checklist
        assert "forehead_not_cropped" in checklist
        assert "margin_above_head_sufficient" in checklist
        assert "face_not_filling_entire_frame" in checklist

    def test_allowed_operator_decisions(self):
        path = Path(V14_CONTROL_DIR) / "combine_v2_v14_operator_visual_review_packet.json"
        with open(path) as f:
            packet = json.load(f)

        allowed = packet.get("allowed_operator_decisions", [])
        assert "accepted" in allowed
        assert "rejected" in allowed
        assert "needs_manual_review" in allowed
        assert len(allowed) == 3
