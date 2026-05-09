"""Regression tests: agent must not choose operator verdict.

These tests enforce the agent_may_not_choose_verdict invariant.
An agent/CLI/test may NOT set operator_verdict, may NOT claim
visual_review_performed_by_operator=true, and may NOT advance the
pipeline past preview_operator_review_required without a real human
operator decision.

Task: RC-COMBINE-V2-POST-PREVIEW-OPERATOR-REVIEW-REPAIR-001
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.post_preview.post_preview_stage import (
    validate_operator_decision,
    VALID_VERDICTS,
    OPERATOR_DECISION_SCHEMA,
)
from app.qa.operator_visual_decision import (
    validate_verdict,
    record_operator_visual_decision,
    ALLOWED_VERDICTS,
)


# ---------------------------------------------------------------------------
# 1. post_preview_stage.validate_operator_decision — gate for preview stage
# ---------------------------------------------------------------------------


class TestValidateOperatorDecision:
    """Tests for validate_operator_decision() in post_preview_stage.py."""

    def test_accepts_valid_human_verdict_accepted(self):
        """A valid human decision with accepted_for_voice_stage must pass."""
        decision = {
            "operator_verdict": "accepted_for_voice_stage",
            "operator_notes": "Looking good, proceed to voice prep.",
            "visual_review_performed_by_operator": True,
            "preview_lowres_reviewed": True,
            "preview_gif_reviewed": True,
            "contact_sheet_reviewed": True,
            "production_accepted": False,
        }
        valid, msg = validate_operator_decision(decision)
        assert valid, f"Expected valid decision, got: {msg}"
        assert msg == "Decision valid"

    def test_accepts_valid_human_verdict_rejected(self):
        """A valid human decision with rejected must pass."""
        decision = {
            "operator_verdict": "rejected",
            "operator_notes": "Preview quality not acceptable.",
            "visual_review_performed_by_operator": True,
            "preview_lowres_reviewed": True,
            "preview_gif_reviewed": True,
            "contact_sheet_reviewed": True,
            "production_accepted": False,
        }
        valid, msg = validate_operator_decision(decision)
        assert valid, f"Expected valid decision, got: {msg}"

    def test_accepts_valid_human_verdict_needs_fix(self):
        """A valid human decision with needs_fix must pass."""
        decision = {
            "operator_verdict": "needs_fix",
            "operator_notes": "Subtitle timing is off.",
            "visual_review_performed_by_operator": True,
            "preview_lowres_reviewed": True,
            "preview_gif_reviewed": True,
            "contact_sheet_reviewed": True,
            "production_accepted": False,
        }
        valid, msg = validate_operator_decision(decision)
        assert valid, f"Expected valid decision, got: {msg}"

    def test_rejects_agent_set_visual_review_performed_by_operator_false(self):
        """Agent must not set visual_review_performed_by_operator.

        If visual_review_performed_by_operator is False, the validator
        must reject the decision, since only a human operator can perform
        visual review.
        """
        decision = {
            "operator_verdict": "accepted_for_voice_stage",
            "operator_notes": "Looks good.",
            "visual_review_performed_by_operator": False,
            "preview_lowres_reviewed": False,
            "preview_gif_reviewed": False,
            "contact_sheet_reviewed": False,
            "production_accepted": False,
        }
        valid, msg = validate_operator_decision(decision)
        assert not valid, "Agent-set visual_review_performed_by_operator=False must be rejected"
        assert "visual_review_performed_by_operator must be true" in msg

    def test_rejects_production_accepted_true(self):
        """production_accepted must always be false at this stage."""
        decision = {
            "operator_verdict": "accepted_for_voice_stage",
            "operator_notes": "",
            "visual_review_performed_by_operator": True,
            "preview_lowres_reviewed": True,
            "preview_gif_reviewed": True,
            "contact_sheet_reviewed": True,
            "production_accepted": True,
        }
        valid, msg = validate_operator_decision(decision)
        assert not valid, "production_accepted=True must be rejected"
        assert "production_accepted must be false" in msg

    def test_rejects_invalid_verdict(self):
        """An unknown verdict must be rejected."""
        decision = {
            "operator_verdict": "invalid_verdict_value",
            "operator_notes": "",
            "visual_review_performed_by_operator": True,
            "preview_lowres_reviewed": True,
            "preview_gif_reviewed": True,
            "contact_sheet_reviewed": True,
            "production_accepted": False,
        }
        valid, msg = validate_operator_decision(decision)
        assert not valid, "Invalid verdict must be rejected"
        assert "Unknown operator_verdict" in msg

    def test_rejects_missing_required_fields(self):
        """Missing required fields must be caught."""
        decision = {
            "operator_verdict": "accepted_for_voice_stage",
            # missing operator_notes, visual_review_performed_by_operator, etc.
        }
        valid, msg = validate_operator_decision(decision)
        assert not valid, "Missing required fields must be rejected"
        assert "Missing required fields" in msg

    def test_rejects_empty_dict(self):
        """An empty decision dict must fail validation."""
        valid, msg = validate_operator_decision({})
        assert not valid
        assert "Missing required fields" in msg

    def test_rejects_none(self):
        """None must fail validation."""
        valid, msg = validate_operator_decision(None)  # type: ignore[arg-type]
        assert not valid
        assert "valid JSON object" in msg


# ---------------------------------------------------------------------------
# 2. operator_visual_decision.validate_verdict — gate for visual decision
# ---------------------------------------------------------------------------


class TestValidateVerdict:
    """Tests for validate_verdict() in operator_visual_decision.py."""

    def test_accepts_accepted(self):
        result = validate_verdict("accepted")
        assert result["valid"] is True

    def test_accepts_rejected(self):
        result = validate_verdict("rejected")
        assert result["valid"] is True

    def test_accepts_needs_fix(self):
        result = validate_verdict("needs_fix")
        assert result["valid"] is True

    def test_rejects_none(self):
        result = validate_verdict(None)
        assert result["valid"] is False
        assert result.get("verdict_missing") is True

    def test_rejects_unknown_verdict(self):
        result = validate_verdict("accepted_for_voice_stage")
        # Note: accepted_for_voice_stage is NOT in ALLOWED_VERDICTS for
        # the operator_visual_decision gate (different from post_preview).
        # This is the old-style gate; the new gate has its own enum.
        assert result["valid"] is False

    def test_rejects_empty_string(self):
        result = validate_verdict("")
        assert result["valid"] is False


# ---------------------------------------------------------------------------
# 3. record_operator_visual_decision — agent must not invent verdict
# ---------------------------------------------------------------------------


class TestRecordOperatorVisualDecision:
    """Tests for record_operator_visual_decision() — agent_invented_verdict guard."""

    def test_agent_invented_verdict_is_false(self):
        """The result must always report agent_invented_verdict=False."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            control_dir = tmp_path / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)

            # Create minimal artifact_index.json
            with open(control_dir / "artifact_index.json", "w") as f:
                json.dump({"stage_results": []}, f)

            # Create minimal episode_ledger.json
            with open(control_dir / "episode_ledger.json", "w") as f:
                json.dump([], f)

            result = record_operator_visual_decision(
                project_root=tmp_path,
                verdict="accepted",
                reason="Test acceptance",
            )

            assert result.get("agent_invented_verdict") is False, (
                "agent_invented_verdict must be false — agent may not invent a verdict"
            )
            assert result.get("operator_verdict_source_required") is True, (
                "operator_verdict_source_required must be true"
            )

    def test_missing_verdict_creates_blocker(self):
        """When verdict is None, blockers must be populated."""
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            control_dir = tmp_path / "output" / "control"
            control_dir.mkdir(parents=True, exist_ok=True)

            with open(control_dir / "artifact_index.json", "w") as f:
                json.dump({"stage_results": []}, f)
            with open(control_dir / "episode_ledger.json", "w") as f:
                json.dump([], f)

            result = record_operator_visual_decision(
                project_root=tmp_path,
                verdict=None,
            )

            assert len(result.get("blockers", [])) > 0, (
                "Missing verdict must produce blockers"
            )
            assert result["current_state"] == "operator_visual_review_required"
            assert result["next_allowed_action"] == "operator_visual_review_required"


# ---------------------------------------------------------------------------
# 4. post_preview_stage — staging
# ---------------------------------------------------------------------------


class TestPostPreviewStageInvariants:
    """Verify post_preview_stage invariants that prevent agent-generated decisions."""

    def test_operator_decision_schema_requires_human_review(self):
        """OPERATOR_DECISION_SCHEMA must enforce visual_review_performed_by_operator."""
        required = OPERATOR_DECISION_SCHEMA.get("required", [])
        assert "visual_review_performed_by_operator" in required, (
            "Schema must require visual_review_performed_by_operator"
        )
        assert "operator_verdict" in required
        assert "production_accepted" in required

    def test_production_accepted_schema_const_false(self):
        """production_accepted must have const: False in the schema."""
        props = OPERATOR_DECISION_SCHEMA.get("properties", {})
        prod = props.get("production_accepted", {})
        assert prod.get("const") is False, (
            "production_accepted must be const False in the schema"
        )

    def test_valid_verdicts_not_empty(self):
        """VALID_VERDICTS must contain expected values."""
        assert "accepted_for_voice_stage" in VALID_VERDICTS
        assert "rejected" in VALID_VERDICTS
        assert "needs_fix" in VALID_VERDICTS
        assert len(VALID_VERDICTS) == 3

    def test_allowed_verdicts_not_empty(self):
        """ALLOWED_VERDICTS must contain expected values."""
        assert "accepted" in ALLOWED_VERDICTS
        assert "rejected" in ALLOWED_VERDICTS
        assert "needs_fix" in ALLOWED_VERDICTS
        assert len(ALLOWED_VERDICTS) == 3

    def test_agent_may_not_set_production_accepted(self):
        """Any decision with production_accepted=true must be rejected."""
        for verdict in ["accepted_for_voice_stage", "accepted", "rejected", "needs_fix"]:
            decision = {
                "operator_verdict": verdict,
                "operator_notes": "test",
                "visual_review_performed_by_operator": True,
                "preview_lowres_reviewed": True,
                "preview_gif_reviewed": True,
                "contact_sheet_reviewed": True,
                "production_accepted": True,
            }
            valid, msg = validate_operator_decision(decision)
            assert not valid, (
                f"production_accepted=True with verdict '{verdict}' must be rejected"
            )
            assert "production_accepted must be false" in msg


# ---------------------------------------------------------------------------
# 5. Artifact-level invariant validation
# ---------------------------------------------------------------------------


class TestRepairArtifactInvariants:
    """Verify that the repair proof artifact and repaired artifacts are consistent."""

    REPAIR_PROOF_PATH = (
        "data/rc2_multishot1_ep01/output/control/"
        "post_preview_operator_review_repair_proof.json"
    )

    def test_repair_proof_artifact_exists(self):
        """The repair proof artifact must exist."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        assert path.exists(), f"Repair proof artifact not found at {path}"

    def test_repair_proof_has_correct_state(self):
        """Repair proof must set canonical state to preview_operator_review_required."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        with open(path) as f:
            proof = json.load(f)

        state = proof.get("restored_canonical_state", {})
        assert state.get("current_state") == "preview_operator_review_required"
        assert state.get("next_allowed_action") == "preview_operator_review_required"
        assert state.get("production_accepted") is False
        assert state.get("voice_generation_ready") is False
        assert state.get("voice_generation_executed") is False
        assert state.get("assembly_executed") is False
        assert state.get("downstream_executed") is False

    def test_repair_proof_lists_regression_tests(self):
        """Repair proof must reference the regression test file."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        with open(path) as f:
            proof = json.load(f)

        tests = proof.get("regression_tests_created", [])
        assert any(
            "test_agent_may_not_choose_verdict" in t for t in tests
        ), "Repair proof must reference regression tests"

    def test_repair_proof_enforces_invariants(self):
        """Repair proof must list agent_may_not_choose_verdict as enforced invariant."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        with open(path) as f:
            proof = json.load(f)

        invariants = proof.get("invariants_enforced", [])
        assert "agent_may_not_choose_verdict" in invariants
        assert "agent_may_not_accept_preview" in invariants
        assert "agent_may_not_override_operator" in invariants
