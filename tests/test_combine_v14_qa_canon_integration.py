"""Tests for V14 QA Canon Engine integration.

Verifies defect taxonomy includes framing defects,
canon files are updated, and QA engine handles framing defects.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.defect_taxonomy import (
    DEFECT_TAXONOMY,
    get_defect,
    map_operator_feedback_to_defects,
)
from app.qa.canon_registry import load_domain_canon, load_universal_canon
from app.qa.decision_policy import DEFAULT_DECISION_POLICY, apply_decision_policy

PROJECT_ROOT = Path("data/rc2_multishot1_ep01")
CONTROL_DIR = PROJECT_ROOT / "output" / "control"
CANON_DIR = CONTROL_DIR / "qa" / "canons"
POLICY_DIR = CONTROL_DIR / "qa" / "policies"

FRAMING_DEFECTS = [
    "head_not_fully_in_frame",
    "top_of_head_cropped",
    "over_tight_face_crop",
    "portrait_framing_failed",
]


class TestV14FramingDefectTaxonomy:
    """Verify framing defects are in the taxonomy."""

    def test_framing_defects_exist(self):
        for defect_id in FRAMING_DEFECTS:
            defect = get_defect(defect_id)
            assert defect is not None, f"Defect {defect_id} not found in taxonomy"
            assert defect.get("id") == defect_id
            assert defect.get("domain") == "human_face"

    def test_framing_defect_severity(self):
        hard_reject = ["head_not_fully_in_frame", "top_of_head_cropped", "over_tight_face_crop"]
        medium = ["portrait_framing_failed"]
        for defect_id in hard_reject:
            d = get_defect(defect_id)
            assert d.get("severity") == "hard_reject", f"{defect_id} should be hard_reject"
        for defect_id in medium:
            d = get_defect(defect_id)
            assert d.get("severity") == "medium", f"{defect_id} should be medium"

    def test_framing_defect_descriptions(self):
        for defect_id in FRAMING_DEFECTS:
            d = get_defect(defect_id)
            assert d.get("description") and len(d["description"]) > 5


class TestV14KeywordMapping:
    """Verify operator feedback keyword mapping covers framing."""

    def test_head_keyword_maps_to_head_not_fully_in_frame(self):
        defects = map_operator_feedback_to_defects("head is not fully visible in frame")
        assert "head_not_fully_in_frame" in defects

    def test_cropped_keyword_maps_to_top_of_head_cropped(self):
        defects = map_operator_feedback_to_defects("top of head is cropped")
        assert "top_of_head_cropped" in defects

    def test_forehead_keyword_maps_to_top_of_head_cropped(self):
        defects = map_operator_feedback_to_defects("forehead is cut off")
        assert "top_of_head_cropped" in defects

    def test_closeup_keyword_maps_to_over_tight_face_crop(self):
        defects = map_operator_feedback_to_defects("extreme close-up face")
        assert "over_tight_face_crop" in defects

    def test_tight_keyword_maps_to_over_tight_face_crop(self):
        defects = map_operator_feedback_to_defects("face is too tight in frame")
        assert "over_tight_face_crop" in defects

    def test_portrait_keyword_maps_to_portrait_framing_failed(self):
        defects = map_operator_feedback_to_defects("portrait framing is wrong")
        assert "portrait_framing_failed" in defects


class TestV14CanonFiles:
    """Verify canon files include framing defects."""

    def test_universal_canon_includes_framing(self):
        canon = load_universal_canon(CANON_DIR)
        must_have = canon.get("must_have", [])
        assert "full_head_in_frame" in must_have
        assert "no_cropped_forehead" in must_have

    def test_human_face_canon_includes_framing_defects(self):
        canon = load_domain_canon("human_face_portrait", CANON_DIR)
        hard_reject = canon.get("hard_reject_defects", [])
        assert "head_not_fully_in_frame" in hard_reject
        assert "top_of_head_cropped" in hard_reject
        assert "over_tight_face_crop" in hard_reject

    def test_human_face_canon_includes_framing_regions(self):
        canon = load_domain_canon("human_face_portrait", CANON_DIR)
        regions = canon.get("critical_regions", [])
        assert "hair" in regions
        assert "forehead" in regions
        assert "top_of_head" in regions


class TestV14DecisionPolicy:
    """Verify decision policy handles framing defects."""

    def test_default_policy_includes_framing_defects(self):
        auto_reject = DEFAULT_DECISION_POLICY.get("auto_reject_if", [])
        assert "head_not_fully_in_frame" in auto_reject
        assert "top_of_head_cropped" in auto_reject
        assert "over_tight_face_crop" in auto_reject

    def test_framing_defects_trigger_auto_reject(self):
        from app.qa.decision_policy import apply_decision_policy
        policy = {
            "auto_reject_if": [
                "head_not_fully_in_frame",
                "top_of_head_cropped",
                "over_tight_face_crop",
            ],
            "operator_review_if": ["portrait_framing_failed"],
            "production_accepted_allowed": False,
        }
        result = apply_decision_policy(
            policy=policy,
            critical_failures=["head_not_fully_in_frame"],
            all_detected_defects=["head_not_fully_in_frame"],
        )
        assert result["decision"] == "reject"
        assert "head_not_fully_in_frame" in result.get("auto_rejected_by", [])
        assert result["production_accepted"] is False

    def test_portrait_framing_failed_triggers_operator_review(self):
        policy = {
            "auto_reject_if": [],
            "operator_review_if": ["portrait_framing_failed"],
            "production_accepted_allowed": False,
        }
        result = apply_decision_policy(
            policy=policy,
            critical_failures=[],
            all_detected_defects=["portrait_framing_failed"],
        )
        assert result["decision"] == "operator_review_required"
        assert "portrait_framing_failed" in result.get("operator_review_by", [])

    def test_decision_policy_never_accepts_production(self):
        policy = DEFAULT_DECISION_POLICY
        result = apply_decision_policy(
            policy=policy,
            critical_failures=[],
            all_detected_defects=[],
        )
        assert result["production_accepted"] is False
        assert result["assembly_allowed"] is False
        assert result["downstream_allowed"] is False


class TestV14QACanonEngine:
    """Verify QA Canon Engine can handle framing defects without crashing."""

    def test_engine_initializes_with_project_root(self):
        from app.qa.qa_canon_engine import QACanonEngine
        engine = QACanonEngine(str(PROJECT_ROOT))
        assert engine is not None
        assert engine.project_root == PROJECT_ROOT

    def test_engine_evaluate_with_framing_feedback(self, tmp_path):
        from app.qa.qa_canon_engine import QACanonEngine
        # Use a known V13 asset as test input (it exists on disk)
        v13_asset = str(PROJECT_ROOT / "output/assets/combine_v2_v13_candidate_1778239698_00001_.png")
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v14",
            asset_path=v13_asset,
            task_contract={"candidate_version": "v14"},
            operator_feedback="head is cropped, not fully in frame, forehead cut off",
        )
        assert decision is not None
        assert decision.candidate_version == "v14"
        # Operator feedback should map to framing defects
        detected = decision.detected_defects
        assert "head_not_fully_in_frame" in detected
        assert "top_of_head_cropped" in detected

    def test_engine_preserves_production_guards(self, tmp_path):
        from app.qa.qa_canon_engine import QACanonEngine
        v13_asset = str(PROJECT_ROOT / "output/assets/combine_v2_v13_candidate_1778239698_00001_.png")
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v14",
            asset_path=v13_asset,
        )
        assert decision.production_accepted is False
        assert decision.assembly_allowed is False
        assert decision.downstream_allowed is False


class TestV14OperatorFeedbackMemory:
    """Verify operator feedback memory contains V13 framing feedback."""

    def test_feedback_memory_has_framing_entry(self):
        from app.qa.reference_memory import load_operator_feedback_memory
        memory = load_operator_feedback_memory(CONTROL_DIR / "qa" / "feedback")
        entries = memory.get("feedback_entries", [])
        v13_framing = [e for e in entries if e.get("candidate_version") == "v13"
                       and "head_not_fully_in_frame" in e.get("defects", [])]
        assert len(v13_framing) >= 1, "No V13 framing entry in feedback memory"
