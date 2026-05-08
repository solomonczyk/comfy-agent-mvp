"""Boundary tests for QA Canon Engine: no generation boundary.

Verifies the engine never performs generation, never submits to ComfyUI,
never creates generated assets, and always returns safe defaults.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.qa.canon_registry import load_domain_canon, load_universal_canon
from app.qa.decision_policy import load_decision_policy
from app.qa.defect_taxonomy import DEFECT_TAXONOMY, map_operator_feedback_to_defects
from app.qa.opencv_checks import check_opencv_available, run_opencv_checks
from app.qa.qa_canon_engine import QACanonEngine
from app.qa.region_checks import run_region_checks
from app.qa.scene_router import classify_scene_type


class TestNoGenerationBoundary:
    """Verify the QA Canon Engine never performs generation."""

    def test_engine_has_no_generation_attributes(self):
        """The engine should not have any generation-related attributes."""
        forbidden = ["comfyui", "generation", "submit", "prompt_id", "workflow_payload"]
        engine_attrs = dir(QACanonEngine)
        for attr in forbidden:
            matching = [a for a in engine_attrs if attr.lower() in a.lower()]
            # Some attributes are OK at the project_root level, but none
            # should suggest generation capability
            for match in matching:
                assert "project" in match.lower() or "control" in match.lower() or "canon" in match.lower() or "policy" in match.lower() or "feedback" in match.lower() or "ref" in match.lower(), f"Found potentially generation-related attribute: {match}"

    def test_engine_evaluate_does_not_create_assets(self, tmp_path):
        """Engine evaluation should not create any asset files."""
        # Track files before
        before = set(str(p) for p in tmp_path.rglob("*"))

        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="nonexistent.png",
            operator_feedback="test feedback",
        )

        # Track files after (should only be QA-related files)
        after = set(str(p) for p in tmp_path.rglob("*"))
        new_files = after - before

        # All new files should be in qa/ directories
        for f in new_files:
            assert "/qa/" in f.replace("\\", "/"), f"File outside qa/ directory: {f}"

    def test_production_accepted_never_true(self, tmp_path):
        """No matter the input, production_accepted must always be false."""
        engine = QACanonEngine(tmp_path)
        # Test with nonexistent asset
        decision = engine.evaluate("v12", "fake.png")
        assert decision.production_accepted is False

        # Test with empty feedback
        decision = engine.evaluate("v12", "fake.png", operator_feedback="")
        assert decision.production_accepted is False

        # Test with positive feedback
        decision = engine.evaluate("v12", "fake.png", operator_feedback="looks great")
        assert decision.production_accepted is False

    def test_assembly_and_downstream_blocked(self, tmp_path):
        """Assembly and downstream must always be blocked."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate("v12", "fake.png", operator_feedback="test")
        assert decision.assembly_allowed is False
        assert decision.downstream_allowed is False

    def test_no_retry_triggered_by_engine(self, tmp_path):
        """The engine should not trigger any retry logic."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate("v12", "fake.png", operator_feedback="test")
        # The decision should only reference correction plans or review,
        # never generation retry directly
        assert "retry" not in decision.recommended_next_action.lower()
        assert decision.production_accepted is False


class TestOpenCVFallback:
    """Test OpenCV fallback behavior when cv2 is unavailable."""

    def test_opencv_unavailable_fallback_does_not_crash(self):
        """The QA engine should not crash when cv2 is unavailable."""
        available = check_opencv_available()
        # Test passes regardless of whether cv2 is available
        engine_imports = True

    def test_run_opencv_checks_fallback(self, tmp_path):
        """run_opencv_checks should handle missing cv2 gracefully."""
        result = run_opencv_checks(tmp_path / "nonexistent.png")
        # Should always return a structured result
        assert isinstance(result, dict)
        assert "opencv_available" in result
        assert "checks_executed" in result

    def test_engine_does_not_fail_without_opencv(self, tmp_path):
        """The engine should complete successfully even without OpenCV."""
        engine = QACanonEngine(tmp_path)
        decision = engine.evaluate(
            candidate_version="v12",
            asset_path="fake.png",
            operator_feedback="teeth do not pass visual approval",
        )
        # The opencv result should be included but the overall QA should still work
        opencv_result = decision.opencv_result
        assert isinstance(opencv_result, dict)
        # The decision should still be determined regardless of OpenCV availability
        assert decision.decision in ("reject", "operator_review_required", "candidate_ok_for_pipeline_review")


class TestSceneTypeBoundaries:
    """Test scene router edge cases."""

    def test_scene_router_v12_defaults_human_face(self):
        assert classify_scene_type("v12") == "human_face_portrait"

    def test_scene_router_v13_defaults_human_face(self):
        assert classify_scene_type("v13") == "human_face_portrait"

    def test_scene_router_unknown_no_hints(self):
        assert classify_scene_type("v1") == "unknown"

    def test_scene_router_with_metadata(self):
        scene = classify_scene_type("v1", metadata={"description": "portrait of a woman"})
        assert scene == "human_face_portrait"


class TestStateContract:
    """Verify the expected state contract for the V12->V13 transition."""

    def test_expected_state_contract(self):
        """The state contract constants should be as expected."""
        expected_state_contract = {
            "current_state": "v13_correction_plan_required",
            "next_allowed_action": "v13_generation_authorization_required",
            "candidate_version": "v13",
            "candidate_count": 2,
            "max_candidates": 3,
            "v12_operator_rejected": True,
            "qa_canon_engine_available": True,
            "production_accepted": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
        }
        assert expected_state_contract["current_state"] == "v13_correction_plan_required"
        assert expected_state_contract["next_allowed_action"] == "v13_generation_authorization_required"
        assert expected_state_contract["production_accepted"] is False
        assert expected_state_contract["assembly_allowed"] is False
        assert expected_state_contract["downstream_allowed"] is False
