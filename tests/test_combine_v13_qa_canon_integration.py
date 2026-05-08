"""Tests for V13 QA Canon Engine integration.

Verifies QA Canon report structure, decision policy, defect detection,
operator feedback memory integration, and negative reference usage.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.qa_canon_engine import QACanonEngine
from app.qa.canon_registry import load_domain_canon, load_universal_canon
from app.qa.decision_policy import apply_decision_policy, load_decision_policy
from app.qa.reference_memory import load_operator_feedback_memory
from app.qa.scene_router import classify_scene_type

PROJECT_ROOT = Path("data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
V13_ASSET_PATH = "output/assets/combine_v2_v13_candidate_1778239698_00001_.png"
V13_QA_REPORT = CONTROL_DIR / "qa" / "reports" / "combine_v2_v13_qa_canon_report.json"


class TestV13QACanonReport:
    """Verify the V13 QA Canon report structure and content."""

    def test_qa_report_exists(self):
        assert V13_QA_REPORT.exists(), "V13 QA Canon report must exist"

    def test_qa_report_required_fields(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)

        assert report.get("candidate_version") == "v13"
        assert report.get("qa_canon_engine_used") is True
        assert report.get("universal_canon_used") is True
        assert report.get("human_face_canon_used") is True
        assert report.get("operator_feedback_memory_used") is True
        assert report.get("negative_reference_used") is True
        assert report.get("decision") == "operator_review_required"
        assert report.get("production_accepted") is False

    def test_checked_defects_include_mouth_teeth(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)

        checked = report.get("checked_defects", [])
        assert "bad_teeth" in checked
        assert "unnatural_mouth" in checked
        assert "lip_teeth_boundary_failed" in checked

    def test_canons_used(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)

        canons = report.get("canons_used", [])
        assert "universal_quality_v1" in canons
        assert "human_face_photoreal_v1" in canons

    def test_assembly_and_downstream_blocked(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        assert report.get("assembly_allowed") is False
        assert report.get("downstream_allowed") is False

    def test_scene_type_is_human_face(self):
        scene = classify_scene_type("v13", task_contract={"candidate_version": "v13"})
        assert scene == "human_face_portrait"

    def test_opencv_checks_executed(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        opencv = report.get("opencv_result", {})
        assert opencv.get("checks_executed") is True

    def test_region_checks_pass(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        region = report.get("region_check_result", {})
        assert region.get("readable") is True
        assert region.get("stub_asset") is False

    def test_asset_dimensions_pass(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        dims = report.get("region_check_result", {}).get("dimensions", {})
        assert dims.get("pass") is True
        assert dims.get("width") == 1024
        assert dims.get("height") == 1024

    def test_file_size_above_minimum(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        fs = report.get("region_check_result", {}).get("file_size", {})
        assert fs.get("pass") is True
        assert fs.get("stub_detected") is False
        assert fs.get("size_bytes", 0) > 1024


class TestV13QACanonEdgeCases:
    """Verify edge cases in QA Canon integration."""

    def test_operator_feedback_memory_carries_v12_feedback(self):
        memory = load_operator_feedback_memory(CONTROL_DIR / "qa" / "feedback")
        assert memory is not None
        entries = memory.get("feedback_entries", [])
        v12_entries = [e for e in entries if e.get("candidate_version") == "v12"]
        assert len(v12_entries) >= 1
        assert any("teeth" in e.get("operator_comment", "") for e in v12_entries)

    def test_universal_canon_loaded(self):
        canon = load_universal_canon(CONTROL_DIR / "qa" / "canons")
        assert canon["canon_id"] == "universal_quality_v1"
        assert len(canon["must_have"]) >= 5

    def test_human_face_canon_loaded(self):
        canon = load_domain_canon("human_face_portrait", CONTROL_DIR / "qa" / "canons")
        assert canon["canon_id"] == "human_face_photoreal_v1"
        assert "bad_teeth" in canon.get("hard_reject_defects", [])

    def test_decision_policy_not_accepting(self):
        policy = load_decision_policy(CONTROL_DIR / "qa" / "policies")
        result = apply_decision_policy(
            policy,
            critical_failures=["bad_teeth"],
            all_detected_defects=["bad_teeth"],
        )
        # Even with defects, decision should allow operator review
        assert result["production_accepted"] is False
        assert result["assembly_allowed"] is False
        assert result["downstream_allowed"] is False

    def test_qa_engine_can_evaluate_v13(self, tmp_path):
        """Verify QACanonEngine can evaluate a V13 asset without crashing."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v13",
            asset_path=V13_ASSET_PATH,
            task_contract={"candidate_version": "v13"},
            operator_feedback="teeth do not pass visual approval",
        )
        assert decision is not None
        assert decision.candidate_version == "v13"

    def test_decision_operator_review_required(self):
        with open(V13_QA_REPORT) as f:
            report = json.load(f)
        assert report.get("decision") == "operator_review_required", \
            f"Expected operator_review_required, got: {report.get('decision')}"
