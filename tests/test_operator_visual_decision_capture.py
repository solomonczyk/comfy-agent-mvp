"""
Tests for Operator Visual Decision Capture — RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001.

Verifies:
- Decision artifact structure is correct
- Verdict validation works
- operator_reason is recorded
- Missing verdict creates pending artifact
- Invalid verdict is rejected
- production_accepted is always False
"""

import json
import pytest
from pathlib import Path


@pytest.fixture
def project_dir(tmp_path: Path) -> Path:
    """Create a temporary project directory structure."""
    (tmp_path / "output" / "control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "assets").mkdir(parents=True, exist_ok=True)
    return tmp_path


class TestVerdictValidation:
    """Tests for verdict validation logic."""

    def test_valid_verdict_accepted(self):
        """accepted must be a valid verdict."""
        from app.qa.operator_visual_decision import validate_verdict

        result = validate_verdict("accepted")
        assert result["valid"] is True
        assert result["error"] is None

    def test_valid_verdict_rejected(self):
        """rejected must be a valid verdict."""
        from app.qa.operator_visual_decision import validate_verdict

        result = validate_verdict("rejected")
        assert result["valid"] is True
        assert result["error"] is None

    def test_valid_verdict_needs_fix(self):
        """needs_fix must be a valid verdict."""
        from app.qa.operator_visual_decision import validate_verdict

        result = validate_verdict("needs_fix")
        assert result["valid"] is True
        assert result["error"] is None

    def test_empty_verdict_not_valid(self):
        """Empty string must not be valid."""
        from app.qa.operator_visual_decision import validate_verdict

        result = validate_verdict("")
        assert result["valid"] is False

    def test_non_string_verdict_not_valid(self):
        """A numeric verdict must not be valid."""
        from app.qa.operator_visual_decision import validate_verdict

        result = validate_verdict(None)
        assert result["valid"] is False
        assert result["verdict_missing"] is True


class TestDecisionArtifact:
    """Tests for the decision artifact structure."""

    def test_decision_artifact_structure(self, project_dir):
        """Decision artifact must have the correct structure."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
            reason="Good quality",
        )

        assert result["decision_artifact_created"] is True
        assert result["production_accepted"] is False

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "operator_visual_decision.json") as f:
            artifact = json.load(f)

        assert artifact["task_id"] == "RC-COMBINE-V2-OPERATOR-VISUAL-DECISION-001"
        assert artifact["operator_visual_review_executed"] is True
        assert artifact["operator_verdict"] == "accepted"
        assert artifact["operator_reason"] == "Good quality"
        assert artifact["technical_pass_not_treated_as_visual_pass"] is True
        assert artifact["production_accepted"] is False

    def test_reason_recorded(self, project_dir):
        """Operator reason must be recorded in the artifact."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="rejected",
            reason="Skin texture is synthetic",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "operator_visual_decision.json") as f:
            artifact = json.load(f)

        assert artifact["operator_reason"] == "Skin texture is synthetic"

    def test_reason_empty_when_not_provided(self, project_dir):
        """Reason must be empty string when not provided."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="accepted",
        )

        control_dir = project_dir / "output" / "control"
        with open(control_dir / "operator_visual_decision.json") as f:
            artifact = json.load(f)

        assert artifact["operator_reason"] == ""

    def test_missing_verdict_creates_pending(self, project_dir):
        """Missing verdict must create a pending artifact."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        assert result["missing_verdict_branch_supported"] is True
        assert result["state_updated"] is False
        assert result["current_state"] == "operator_visual_review_required"

        control_dir = project_dir / "output" / "control"
        pending_path = control_dir / "operator_visual_decision_pending.json"
        assert pending_path.exists(), "Pending artifact must exist when verdict is missing"

        with open(pending_path) as f:
            pending = json.load(f)

        assert pending["operator_verdict_provided"] is False
        assert pending["production_accepted"] is False

    def test_invalid_verdict_is_rejected(self, project_dir):
        """Invalid verdict must not advance state."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict="not_a_valid_verdict",
            reason="testing",
        )

        assert result["state_updated"] is False
        assert result["current_state"] == "operator_visual_review_required"
        assert result["production_accepted"] is False

    def test_production_accepted_never_true(self, project_dir):
        """production_accepted must always be False."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        for v in ["accepted", "rejected", "needs_fix"]:
            r = record_operator_visual_decision(
                project_root=str(project_dir),
                verdict=v,
                reason="test",
            )
            assert r["production_accepted"] is False, f"production_accepted must be False for verdict={v}"


class TestVerdictCaptureSources:
    """Tests that verdict comes from explicit operator input, not agent."""

    def test_agent_did_not_invent_verdict(self, project_dir):
        """Agent must not invent an operator verdict."""
        from app.qa.operator_visual_decision import record_operator_visual_decision

        result = record_operator_visual_decision(
            project_root=str(project_dir),
            verdict=None,
        )

        assert result["agent_invented_verdict"] is False
        assert result["operator_verdict_source_required"] is True
