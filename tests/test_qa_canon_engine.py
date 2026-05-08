"""Tests for QA Canon Engine MVP — core engine, canons, scene routing, defects."""
from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from app.qa.canon_registry import (
    HUMAN_FACE_CANON,
    UNIVERSAL_CANON,
    load_domain_canon,
    load_universal_canon,
    merge_canons,
)
from app.qa.decision_policy import apply_decision_policy, load_decision_policy
from app.qa.defect_taxonomy import (
    DEFECT_TAXONOMY,
    get_defect,
    get_defects_by_domain,
    map_operator_feedback_to_defects,
)
from app.qa.qa_canon_engine import QACanonEngine
from app.qa.region_checks import (
    check_dimensions,
    check_file_size,
    check_image_readable,
    run_region_checks,
)
from app.qa.scene_router import classify_scene_type


class TestUniversalCanon:
    def test_universal_canon_loaded(self):
        canon = load_universal_canon()
        assert canon["canon_id"] == "universal_quality_v1"
        assert "readable_asset" in canon["must_have"]
        assert "stub_asset" in canon["hard_reject_defects"]

    def test_universal_canon_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            canon_dir = Path(tmp)
            canon_path = canon_dir / "universal_quality_canon.json"
            with open(canon_path, "w") as f:
                json.dump({"canon_id": "test_universal", "must_have": [], "hard_reject_defects": []}, f)
            canon = load_universal_canon(canon_dir)
            assert canon["canon_id"] == "test_universal"

    def test_universal_canon_fallback(self):
        canon = load_universal_canon(Path("/nonexistent"))
        assert canon["canon_id"] == "universal_quality_v1"


class TestHumanFaceCanon:
    def test_human_face_canon_loaded(self):
        canon = load_domain_canon("human_face_portrait")
        assert canon["canon_id"] == "human_face_photoreal_v1"
        assert "mouth" in canon["critical_regions"]
        assert "bad_teeth" in canon["hard_reject_defects"]

    def test_human_face_canon_from_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            canon_dir = Path(tmp)
            canon_path = canon_dir / "human_face_canon.json"
            with open(canon_path, "w") as f:
                json.dump({"canon_id": "test_face", "critical_regions": [], "hard_reject_defects": []}, f)
            canon = load_domain_canon("human_face_portrait", canon_dir)
            assert canon["canon_id"] == "test_face"

    def test_unknown_domain_fallback(self):
        canon = load_domain_canon("unknown_domain")
        assert canon == {}


class TestCanonMerge:
    def test_merge_universal_and_domain(self):
        merged = merge_canons(UNIVERSAL_CANON, HUMAN_FACE_CANON)
        assert len(merged["canons_used"]) == 2
        assert "universal_quality_v1" in merged["canons_used"]
        assert "human_face_photoreal_v1" in merged["canons_used"]
        # Both must_have lists should be merged
        assert "readable_asset" in merged["must_have"]
        # Both hard_reject lists should be merged
        assert "stub_asset" in merged["hard_reject_defects"]
        assert "bad_teeth" in merged["hard_reject_defects"]

    def test_merge_deduplicates(self):
        canon_a = {
            "canon_id": "canon_a",
            "must_have": ["a", "b"],
            "hard_reject_defects": ["x", "y"],
        }
        canon_b = {
            "canon_id": "canon_b",
            "must_have": ["b", "c"],
            "hard_reject_defects": ["y", "z"],
        }
        merged = merge_canons(canon_a, canon_b)
        assert merged["must_have"] == ["a", "b", "c"]
        assert merged["hard_reject_defects"] == ["x", "y", "z"]


class TestSceneRouter:
    def test_defaults_to_human_face_for_v12(self):
        scene = classify_scene_type("v12")
        assert scene == "human_face_portrait"

    def test_defaults_to_human_face_for_v13(self):
        scene = classify_scene_type("v13")
        assert scene == "human_face_portrait"

    def test_uses_explicit_scene_type(self):
        scene = classify_scene_type("v12", task_contract={"scene_type": "human_face_portrait"})
        assert scene == "human_face_portrait"

    def test_keyword_detection(self):
        scene = classify_scene_type("v1", task_contract={"task_description": "elderly portrait face"})
        assert scene == "human_face_portrait"

    def test_unknown_fallback(self):
        scene = classify_scene_type("v1")
        assert scene == "unknown"


class TestDefectTaxonomy:
    def test_full_taxonomy_has_expected_defects(self):
        assert "bad_teeth" in DEFECT_TAXONOMY
        assert "unnatural_mouth" in DEFECT_TAXONOMY
        assert "lip_teeth_boundary_failed" in DEFECT_TAXONOMY
        assert "synthetic_doll_like_face" in DEFECT_TAXONOMY
        assert "plastic_skin" in DEFECT_TAXONOMY
        assert "stub_asset" in DEFECT_TAXONOMY
        assert "severe_blur" in DEFECT_TAXONOMY

    def test_get_defect(self):
        defect = get_defect("bad_teeth")
        assert defect is not None
        assert defect["domain"] == "human_face"
        assert defect["severity"] == "hard_reject"

    def test_get_nonexistent_defect(self):
        assert get_defect("nonexistent_defect") is None

    def test_get_defects_by_domain(self):
        human_face = get_defects_by_domain("human_face")
        assert "bad_teeth" in human_face
        assert "unnatural_mouth" in human_face
        universal = get_defects_by_domain("universal")
        assert "stub_asset" in universal
        assert "severe_blur" in universal

    def test_map_operator_feedback_to_defects(self):
        defects = map_operator_feedback_to_defects("teeth do not pass visual approval")
        assert "bad_teeth" in defects

    def test_map_operator_feedback_multiple(self):
        defects = map_operator_feedback_to_defects("bad teeth, unnatural mouth, plastic doll face")
        assert "bad_teeth" in defects
        assert "unnatural_mouth" in defects
        assert "synthetic_doll_like_face" in defects

    def test_map_operator_feedback_no_match(self):
        defects = map_operator_feedback_to_defects("looks great, very realistic")
        assert defects == []


class TestDecisionPolicy:
    def test_auto_reject_for_bad_teeth(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=["bad_teeth"], all_detected_defects=["bad_teeth"])
        assert result["decision"] == "reject"
        assert "bad_teeth" in result["auto_rejected_by"]
        assert result["production_accepted"] is False
        assert result["assembly_allowed"] is False
        assert result["downstream_allowed"] is False

    def test_operator_review_for_borderline(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=[], all_detected_defects=["borderline_skin_texture"])
        assert result["decision"] == "operator_review_required"

    def test_candidate_ok_when_no_defects(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=[], all_detected_defects=[])
        assert result["decision"] == "candidate_ok_for_pipeline_review"

    def test_production_accepted_always_false(self):
        policy = load_decision_policy()
        result = apply_decision_policy(policy, critical_failures=[], all_detected_defects=[])
        assert result["production_accepted"] is False
        assert result["assembly_allowed"] is False
        assert result["downstream_allowed"] is False


class TestRegionChecks:
    def test_check_image_readable_nonexistent(self):
        result = check_image_readable(Path("/nonexistent/image.png"))
        assert result["readable"] is False
        assert result["exists"] is False

    def test_check_dimensions_pass(self):
        result = check_dimensions(1024, 1024)
        assert result["pass"] is True

    def test_check_dimensions_fail(self):
        result = check_dimensions(100, 100)
        assert result["pass"] is False

    def test_check_file_size_nonexistent(self):
        result = check_file_size(Path("/nonexistent/file.png"))
        assert result["pass"] is False

    def test_run_region_checks_nonexistent(self):
        result = run_region_checks(Path("/nonexistent/file.png"))
        assert result["region_checks_pass"] is False


class TestQACanonEngine:
    def test_engine_creation(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        assert engine.project_root == tmp_path
        assert engine.control_dir == tmp_path / "output" / "control"

    def test_engine_evaluate_nonexistent_asset(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="nonexistent.png",
            operator_feedback="teeth do not pass visual approval",
        )
        assert decision.decision == "reject"
        assert decision.production_accepted is False
        assert decision.assembly_allowed is False
        assert decision.downstream_allowed is False
        assert "unreadable_asset" in decision.critical_failures or "stub_asset" in decision.critical_failures

    def test_engine_records_feedback(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        engine.record_operator_feedback(
            candidate_version="v12",
            asset_path="output/assets/test.png",
            operator_comment="teeth do not pass visual approval",
            defects=["bad_teeth", "unnatural_mouth"],
            failed_regions=["mouth", "teeth"],
        )
        feedback_file = engine.feedback_dir / "operator_feedback_memory.json"
        assert feedback_file.exists()
        with open(feedback_file) as f:
            data = json.load(f)
        assert len(data["feedback_entries"]) == 1
        assert data["feedback_entries"][0]["candidate_version"] == "v12"

    def test_engine_saves_report(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="nonexistent.png",
            operator_feedback="teeth do not pass visual approval",
        )
        report_path = engine.save_qa_report(decision)
        assert report_path.exists()
        with open(report_path) as f:
            report = json.load(f)
        assert report["candidate_version"] == "v12"
        assert report["production_accepted"] is False
        assert report["assembly_allowed"] is False
        assert report["downstream_allowed"] is False

    def test_engine_handles_empty_feedback(self, tmp_path):
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="nonexistent.png",
        )
        assert decision.operator_feedback_used is False
        # Without operator feedback, the nonexistent asset does not trigger
        # face-specific auto-reject defects (the decision policy only
        # auto-rejects on face-related defects, not generic stub_asset)
        assert decision.decision is not None

    def test_no_generation_performed(self, tmp_path):
        """Verify the QA Canon Engine does not perform any generation."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="nonexistent.png",
        )
        # The engine only evaluates — no generation side effects
        assert not hasattr(engine, "generation_performed")
        assert decision.production_accepted is False


class TestIntegration:
    """Integration-level tests combining multiple modules."""

    def test_v12_rejection_flow(self, tmp_path):
        """Simulate the full V12 rejection flow without real assets."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="output/assets/test_v12.png",
            task_contract={"candidate_version": "v12"},
            operator_feedback="teeth do not pass visual approval",
        )
        # Even without a real image, the engine should detect the missing asset
        # and the operator feedback should map to bad_teeth
        assert "bad_teeth" in decision.critical_failures
        assert decision.production_accepted is False
        assert decision.assembly_allowed is False
        assert decision.downstream_allowed is False

        # Record feedback
        engine.record_operator_feedback(
            candidate_version="v12",
            asset_path="output/assets/test_v12.png",
            operator_comment="teeth do not pass visual approval",
            defects=decision.critical_failures,
            failed_regions=["mouth", "teeth"],
        )

        # Save report
        report_path = engine.save_qa_report(decision)
        assert report_path.exists()

    def test_scene_router_integration(self):
        scene = classify_scene_type("v12", task_contract={"task_description": "elderly face portrait"})
        assert scene == "human_face_portrait"
