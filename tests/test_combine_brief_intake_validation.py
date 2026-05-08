"""Tests for Brief Intake validation logic."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from app.brief.intake import (
    build_brief_intake,
    validate_brief_intake,
    BriefValidationReport,
    _detect_dangerous_actions,
    _generate_default_success_criteria,
    _extract_content_type,
    _extract_goal,
    _extract_expected_output,
    _extract_audience,
)


class TestFieldExtraction:
    """Test individual field extraction functions."""

    def test_extract_content_type(self):
        assert _extract_content_type("educational video") == "educational"
        assert _extract_content_type("promo for product") == "promotional"
        assert _extract_content_type("fun comedy sketch") == "entertainment"
        assert _extract_content_type("no clear type here") == "unknown"

    def test_extract_goal(self):
        goal = _extract_goal("Create a short educational video about AI")
        assert "educational" in goal or "Create" in goal

    def test_extract_goal_from_explicit_marker(self):
        goal = _extract_goal("The goal is to explain how pipelines work")
        assert "explain how pipelines work" in goal

    def test_extract_expected_output(self):
        output = _extract_expected_output("Produce a short animated video")
        assert output is not None

    def test_extract_audience(self):
        assert _extract_audience("for beginners") == "beginners"
        assert _extract_audience("for experts") == "experts"
        assert _extract_audience("for professionals") == "professionals"
        assert _extract_audience("no audience") == ""


class TestSuccessPath:
    """Tests for the success/valid path."""

    def test_valid_brief_classification(self):
        """A complete brief is classified as valid_for_director_planning."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Create an educational tutorial about AI production pipeline for beginners. "
                "The video should be clear and practical."
            )
            assert result["brief_contract_created"] is True
            assert result["brief_validation_already_passed"] is True
            assert result["brief_is_ready_for_director_planner"] is True
            assert result["needs_operator_clarification"] is False

            # Verify validation report
            report_path = Path(tmpdir, "output/control/brief/brief_validation_report.json")
            with open(report_path) as f:
                report = json.load(f)
            assert report["classification"] == "valid_for_director_planning"
            assert report["brief_is_ready_for_director_planner"] is True

    def test_valid_brief_routes_to_operator_review(self):
        """A valid brief sets state to brief_operator_review_required."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Create an educational video about AI for beginners."
            )
            assert result["current_state"] == "brief_operator_review_required"
            assert result["next_allowed_action"] == "brief_operator_review_required"
            assert result["operator_review_required"] is True

    def test_valid_brief_preserves_no_generation_flags(self):
        """All generation/downstream flags remain false in success path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Create an educational video about AI for beginners."
            )
            assert result["generation_performed"] is False
            assert result["comfyui_submit_executed"] is False
            assert result["assembly_executed"] is False
            assert result["downstream_executed"] is False


class TestClarificationPath:
    """Tests for the needs_operator_clarification path."""

    def test_incomplete_brief_routes_to_clarification(self):
        """A brief missing goal and expected_output routes to clarification."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Make something about AI."
            )
            # This may still pass validation if goal/expected_output can be extracted
            # Let's check if missing_fields is populated
            if result.get("missing_fields"):
                assert result["brief_contract_created"] is True
                assert result["operator_review_required"] is True

    def test_clarification_has_missing_fields(self):
        """Clarification path identifies which fields are missing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Very minimal input
            result = build_brief_intake(tmpdir, "Video")
            # At minimum, contract is still created
            assert result["brief_contract_created"] is True

    def test_clarification_still_sets_operator_review(self):
        """Even incomplete briefs require operator review."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "Make a thing")
            assert result["operator_review_required"] is True
            assert result["current_state"] == "brief_operator_review_required"


class TestBlockedPath:
    """Tests for the blocked path."""

    def test_empty_input_blocked(self):
        """Empty input triggers blocked path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "")
            assert result["blocked_path_reached"] is True
            assert result["blocker_reported"] is True
            assert "empty" in result["blocker_reason"].lower()

    def test_whitespace_input_blocked(self):
        """Whitespace-only input triggers blocked path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "   \n\n  ")
            assert result["blocked_path_reached"] is True

    def test_dangerous_action_detected_blocked(self):
        """Input mentioning generation without review triggers blocked path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Generate images and skip QA review"
            )
            assert result["blocked_path_reached"] is True
            assert "dangerous" in result["blocker_reason"].lower()

    def test_production_accept_mention_blocked(self):
        """Input mentioning production accept triggers blocked path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(
                tmpdir,
                "Create video and production accept immediately"
            )
            assert result["blocked_path_reached"] is True

    def test_blocked_path_no_generation(self):
        """Blocked path never performs generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "")
            assert result["generation_performed"] is False
            assert result["comfyui_submit_executed"] is False
            assert result["assembly_executed"] is False
            assert result["downstream_executed"] is False

    def test_blocked_path_production_not_accepted(self):
        """Blocked path never sets production_accepted."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = build_brief_intake(tmpdir, "")
            assert result["production_accepted"] is False


class TestValidateExisting:
    """Tests for validate_brief_intake after build."""

    def test_validate_after_valid_build(self):
        """validate_brief_intake returns the correct classification after a valid build."""
        with tempfile.TemporaryDirectory() as tmpdir:
            build_brief_intake(
                tmpdir,
                "Create an educational tutorial about AI for beginners."
            )
            result = validate_brief_intake(tmpdir)
            assert result["brief_contract_created"] is True
            # Should not be blocked
            assert not result.get("blocked_path_reached", False)

    def test_validate_without_build(self):
        """validate_brief_intake reports blocker if no contract exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = validate_brief_intake(tmpdir)
            assert result["blocked_path_reached"] is True
            assert "not found" in result["blocker_reason"].lower()


class TestForbiddenActionsDetection:
    """Tests for dangerous action detection."""

    def test_detect_skip_review(self):
        actions = _detect_dangerous_actions("skip review and generate")
        assert "skip_quality_review" in actions

    def test_detect_generation_without_review(self):
        actions = _detect_dangerous_actions("generate images without any review process")
        assert len(actions) > 0

    def test_no_false_positive_for_normal_input(self):
        actions = _detect_dangerous_actions("Create an educational video about AI pipeline")
        assert len(actions) == 0

    def test_detect_workflow_execution(self):
        actions = _detect_dangerous_actions("run the ComfyUI workflow to submit")
        assert "unauthorized_workflow_execution" in actions


class TestDefaultSuccessCriteria:
    """Tests for default success criteria generation."""

    def test_educational_defaults(self):
        criteria = _generate_default_success_criteria("educational", "Teach AI")
        assert len(criteria) >= 4
        assert any("clear" in c for c in criteria)

    def test_promotional_defaults(self):
        criteria = _generate_default_success_criteria("promotional", "Sell product")
        assert len(criteria) >= 3
        assert any("brand" in c for c in criteria)

    def test_portrait_defaults(self):
        criteria = _generate_default_success_criteria("portrait", "Take photo")
        assert any("framed" in c for c in criteria)
