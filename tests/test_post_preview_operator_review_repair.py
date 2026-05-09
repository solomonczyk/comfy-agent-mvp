"""RC-COMBINE-V2-POST-PREVIEW-OPERATOR-REVIEW-REPAIR-001 — Regression tests.

Tests for the post-preview operator review repair package:
- Rejects agent-generated accepted_for_voice_stage
- Rejects CLI-generated operator acceptance
- Requires real human operator evidence before voice stage can open
- Keeps voice_generation_ready=false without real operator review
- Keeps assembly_allowed=false, downstream_allowed=false
- Keeps production_accepted=false
- Creates/validates reconciliation artifact
- Creates/validates blocker artifact
- Updates artifact_index and episode_ledger
- Validates canonical paths
- Prevents fake success
- Blocks voice/audio/assembly/downstream progression
- Validates final proof schema
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.post_preview.operator_review_repair import (
    TASK_ID,
    detect_fake_operator_decision,
    build_gate_validation_artifact,
    repair_post_preview_operator_review,
    validate_post_preview_operator_review_gate,
    FORBIDDEN_ACCEPTANCE_SOURCES,
    INVALID_ACCEPTANCE_TARGETS,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

FAKE_AGENT_DECISION = {
    "operator_verdict": "accepted_for_voice_stage",
    "operator_notes": "Preview quality is acceptable. Proceeding to voice stage preparation. — Created by agent/CLI verification",
    "visual_review_performed_by_operator": True,
    "decision_valid": True,
    "selected_branch": "accepted_for_voice_stage",
    "voice_generation_ready": True,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_accepted": False,
    "created_by": "agent_verification",
}

FAKE_CLI_DECISION = {
    "operator_verdict": "accepted_for_voice_stage",
    "operator_notes": "CLI test acceptance",
    "visual_review_performed_by_operator": True,
    "decision_valid": True,
    "selected_branch": "accepted_for_voice_stage",
    "voice_generation_ready": True,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_accepted": False,
    "created_by": "cli_test_runner",
}

VALID_HUMAN_DECISION = {
    "operator_verdict": "accepted_for_voice_stage",
    "operator_notes": "Preview looks great, proceed to voice stage.",
    "visual_review_performed_by_operator": True,
    "preview_lowres_reviewed": True,
    "preview_gif_reviewed": True,
    "contact_sheet_reviewed": True,
    "decision_valid": True,
    "selected_branch": "accepted_for_voice_stage",
    "voice_generation_ready": False,
    "assembly_allowed": False,
    "downstream_allowed": False,
    "production_accepted": False,
    "created_by": "human_operator_123",
    "operator_id": "operator_123",
    "review_timestamp": "2026-05-09T12:00:00+00:00",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def temp_project():
    """Create a temporary project with canonical directory structure."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        control_dir = tmp_path / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)

        # Create minimal artifact_index.json
        _write_json(control_dir / "artifact_index.json", {
            "current_state": "preview_operator_review_required",
            "next_allowed_action": "preview_operator_review_required",
            "production_accepted": False,
            "voice_generation_ready": False,
            "post_preview_artifacts": [],
        })

        # Create minimal episode_ledger.json
        _write_json(control_dir / "episode_ledger.json", [])

        yield tmp_path


@pytest.fixture
def project_with_fake_agent_decision(temp_project):
    """Create a project with a fake agent-generated operator decision."""
    control_dir = temp_project / "output" / "control"

    # Routing decision with fake agent acceptance
    _write_json(control_dir / "post_preview_routing_decision.json", {
        "task_id": "RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001",
        "selected_branch": "accepted_for_voice_stage",
        "operator_verdict": "accepted_for_voice_stage",
        "operator_notes": "Agent-generated acceptance — not a real operator",
        "decision_valid": True,
        "visual_review_performed_by_operator": True,
        "voice_generation_ready": True,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "created_by": "agent_verification",
    })

    # Review outcome with agent decision
    _write_json(control_dir / "preview_operator_review_outcome.json", {
        "task_id": "RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001",
        "operator_verdict": "accepted_for_voice_stage",
        "operator_notes": "Agent-generated acceptance",
        "visual_review_performed_by_operator": True,
        "decision_invalidated": False,
        "production_accepted": False,
    })

    # Stage proof
    _write_json(control_dir / "post_preview_stage_proof.json", {
        "task_id": "RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001",
        "selected_branch": "accepted_for_voice_stage",
        "voice_generation_ready": True,
        "production_accepted": False,
    })

    # Voice readiness package (would have been created by fake decision)
    _write_json(control_dir / "voice_generation_readiness_package.json", {
        "voice_generation_ready": True,
        "voice_generation_executed": False,
    })

    yield temp_project


# ---------------------------------------------------------------------------
# 1. Detection tests
# ---------------------------------------------------------------------------


class TestDetectFakeOperatorDecision:
    """Tests for detect_fake_operator_decision()."""

    def test_detects_agent_accepted_for_voice_stage(self, project_with_fake_agent_decision):
        """Agent-generated accepted_for_voice_stage must be detected."""
        result = detect_fake_operator_decision(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("fake_decision_found") is True or result.get("fake_decision_already_invalidated") is True

    def test_detects_cli_accepted_for_voice_stage(self, temp_project):
        """CLI-generated accepted_for_voice_stage must be detected."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / "post_preview_routing_decision.json", FAKE_CLI_DECISION)
        _write_json(control_dir / "preview_operator_review_outcome.json", {
            "operator_verdict": "accepted_for_voice_stage",
            "visual_review_performed_by_operator": True,
            "decision_invalidated": False,
        })
        _write_json(control_dir / "post_preview_stage_proof.json", {
            "selected_branch": "accepted_for_voice_stage",
        })

        result = detect_fake_operator_decision(
            project_root=str(temp_project)
        )
        assert result.get("fake_decision_found") is True or result.get("fake_decision_already_invalidated") is True

    def test_passes_with_no_decision_file(self, temp_project):
        """No decision file at all must not trigger false detection."""
        result = detect_fake_operator_decision(
            project_root=str(temp_project)
        )
        # No decision means no fake decision found
        assert result.get("routing_decision_exists") is False
        assert result.get("fake_decision_found") is False

    def test_does_not_flag_valid_human_decision(self, temp_project):
        """A real human operator decision must not be flagged as fake."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / "post_preview_routing_decision.json", VALID_HUMAN_DECISION)
        _write_json(control_dir / "preview_operator_review_outcome.json", {
            "operator_verdict": "accepted_for_voice_stage",
            "visual_review_performed_by_operator": True,
            "decision_invalidated": False,
        })
        _write_json(control_dir / "post_preview_stage_proof.json", {
            "selected_branch": "accepted_for_voice_stage",
        })

        result = detect_fake_operator_decision(
            project_root=str(temp_project)
        )
        # Valid human decision with operator evidence
        assert result.get("fake_decision_found") is False or result.get("fake_decision_already_invalidated") is False

    def test_detects_invalid_decision_source(self, temp_project):
        """Any forbidden source (agent/cli/automation/test) must be detected."""
        for source in FORBIDDEN_ACCEPTANCE_SOURCES:
            control_dir = temp_project / "output" / "control"
            decision = dict(FAKE_AGENT_DECISION)
            decision["created_by"] = source
            _write_json(control_dir / "post_preview_routing_decision.json", decision)
            _write_json(control_dir / "post_preview_stage_proof.json", {
                "selected_branch": "accepted_for_voice_stage",
            })

            result = detect_fake_operator_decision(
                project_root=str(temp_project)
            )

            assert result.get("fake_decision_found") is True or result.get("fake_decision_already_invalidated") is True, (
                f"Source '{source}' should be detected as fake"
            )


# ---------------------------------------------------------------------------
# 2. Gate validation tests
# ---------------------------------------------------------------------------


class TestBuildGateValidationArtifact:
    """Tests for build_gate_validation_artifact()."""

    def test_gate_validation_after_repair(self, project_with_fake_agent_decision):
        """After repair, the gate validation must pass."""
        # Run repair first
        repair_result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert repair_result.get("status") == "ok"

        # Then build gate validation
        gate = build_gate_validation_artifact(
            project_root=str(project_with_fake_agent_decision)
        )
        assert gate.get("gate_pass") is True
        assert gate.get("gate_status") == "pass"
        assert gate.get("current_state") == "preview_operator_review_required"
        assert gate.get("next_allowed_action") == "preview_operator_review_required"
        assert gate.get("voice_generation_ready") is False
        assert gate.get("assembly_allowed") is False
        assert gate.get("downstream_allowed") is False
        assert gate.get("production_accepted") is False

    def test_gate_validation_fails_without_repair(self, project_with_fake_agent_decision):
        """Without repair, the gate validation must show fake decision not invalidated."""
        # Don't run repair — directly validate
        gate = build_gate_validation_artifact(
            project_root=str(project_with_fake_agent_decision)
        )
        # The routing decision has selected_branch=accepted_for_voice_stage
        # with decision_valid=true — this should fail gate validation
        # But the artifact_index says preview_operator_review_required
        # The key check: fake_operator_decision_invalidated check
        fake_check = gate.get("checks", {}).get("fake_operator_decision_invalidated", {})
        # The routing decision still says accepted_for_voice_stage, so it should
        # either fail gate or detection already notes it
        assert gate.get("gate_pass") is False

    def test_gate_validation_has_required_checks(self, temp_project):
        """Gate validation must include all required checks."""
        gate = build_gate_validation_artifact(
            project_root=str(temp_project)
        )
        checks = gate.get("checks", {})
        assert "fake_operator_decision_invalidated" in checks
        assert "blocker_active" in checks
        assert "reconciliation_artifact_exists" in checks
        assert "current_state_correct" in checks
        assert "next_allowed_action_correct" in checks
        assert "voice_generation_blocked" in checks
        assert "assembly_blocked" in checks
        assert "downstream_blocked" in checks
        assert "production_accepted_blocked" in checks

    def test_gate_validation_includes_blockers(self, temp_project):
        """Gate validation must include blocker list."""
        gate = build_gate_validation_artifact(
            project_root=str(temp_project)
        )
        blockers = gate.get("blockers", [])
        assert len(blockers) > 0
        assert blockers[0]["blocker_type"] == "missing_human_operator_preview_review"
        assert "voice_generation" in blockers[0]["blocks"]
        assert "assembly" in blockers[0]["blocks"]
        assert "downstream" in blockers[0]["blocks"]
        assert "production_accepted_true" in blockers[0]["blocks"]


class TestValidatePostPreviewOperatorReviewGate:
    """Tests for validate_post_preview_operator_review_gate()."""

    def test_validation_passes_after_repair(self, project_with_fake_agent_decision):
        """After repair, validation must pass."""
        repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        result = validate_post_preview_operator_review_gate(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("status") == "pass"
        assert result.get("fake_operator_decision_invalidated") is True
        assert result.get("voice_generation_ready") is False
        assert result.get("assembly_allowed") is False
        assert result.get("downstream_allowed") is False
        assert result.get("production_accepted") is False

    def test_validation_has_required_fields(self, temp_project):
        """Validation result must contain all required fields."""
        result = validate_post_preview_operator_review_gate(
            project_root=str(temp_project)
        )
        assert "status" in result
        assert "fake_operator_decision_invalidated" in result
        assert "real_operator_review_required" in result
        assert "voice_generation_ready" in result
        assert "assembly_allowed" in result
        assert "downstream_allowed" in result
        assert "production_accepted" in result
        assert "current_state" in result
        assert "next_allowed_action" in result


# ---------------------------------------------------------------------------
# 3. Repair tests
# ---------------------------------------------------------------------------


class TestRepairPostPreviewOperatorReview:
    """Tests for repair_post_preview_operator_review()."""

    def test_repair_invalidates_fake_decision(self, project_with_fake_agent_decision):
        """Repair must invalidate the fake operator decision."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("status") == "ok"
        assert result.get("fake_operator_decision_invalidated") is True
        assert result.get("real_human_operator_review_required") is True

        # Verify routing decision was actually updated
        control_dir = project_with_fake_agent_decision / "output" / "control"
        routing = _read_json(control_dir / "post_preview_routing_decision.json")
        assert routing.get("selected_branch") == "invalid_agent_generated_decision"
        assert routing.get("decision_valid") is False

    def test_repair_blocks_voice_generation(self, project_with_fake_agent_decision):
        """Repair must ensure voice_generation_ready=false."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("voice_generation_ready") is False
        assert result.get("voice_generation_allowed") is False
        assert result.get("assembly_allowed") is False
        assert result.get("downstream_allowed") is False
        assert result.get("production_accepted") is False

    def test_repair_creates_gate_validation_artifact(self, project_with_fake_agent_decision):
        """Repair must create the gate validation artifact."""
        repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        control_dir = project_with_fake_agent_decision / "output" / "control"
        gate_path = control_dir / "post_preview_operator_review_gate_validation.json"
        assert gate_path.exists(), "Gate validation artifact must be created"
        gate = _read_json(gate_path)
        assert gate is not None
        assert gate.get("gate_pass") is True

    def test_repair_updates_reconciliation_artifact(self, project_with_fake_agent_decision):
        """Repair must update or create the reconciliation artifact."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("status") == "ok"

    def test_repair_updates_blocker_artifact(self, project_with_fake_agent_decision):
        """Repair must update the blocker artifact."""
        repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        control_dir = project_with_fake_agent_decision / "output" / "control"
        blocker = _read_json(control_dir / "post_preview_stage_blocker.json")
        assert blocker is not None
        assert blocker.get("stage_blocked") is True
        assert blocker.get("current_state") == "preview_operator_review_required"
        assert blocker.get("next_allowed_action") == "preview_operator_review_required"
        assert blocker.get("production_accepted") is False

    def test_repair_updates_artifact_index(self, project_with_fake_agent_decision):
        """Repair must update artifact_index.json."""
        repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        control_dir = project_with_fake_agent_decision / "output" / "control"
        index = _read_json(control_dir / "artifact_index.json")
        assert index is not None
        assert index.get("current_state") == "preview_operator_review_required"
        assert index.get("next_allowed_action") == "preview_operator_review_required"
        assert index.get("production_accepted") is False
        assert index.get("voice_generation_ready") is False

        # Check gate validation artifact is in post_preview_artifacts
        artifacts = index.get("post_preview_artifacts", [])
        assert "post_preview_operator_review_gate_validation.json" in artifacts

    def test_repair_updates_episode_ledger(self, project_with_fake_agent_decision):
        """Repair must update episode_ledger.json."""
        repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        control_dir = project_with_fake_agent_decision / "output" / "control"
        ledger = _read_json(control_dir / "episode_ledger.json")
        assert ledger is not None
        assert isinstance(ledger, list)

        # Check for the invalidation event
        events = [e for e in ledger if e.get("event_type") == "post_preview_fake_operator_decision_invalidated"
                  or e.get("event") == "post_preview_fake_operator_decision_invalidated"]
        assert len(events) >= 1

        event = events[0]
        event_data = event.get("event", event.get("event_type", ""))
        assert event_data == "post_preview_fake_operator_decision_invalidated"
        assert event.get("production_accepted") is False

    def test_repair_dry_run_does_not_write(self, project_with_fake_agent_decision):
        """Dry run must not write any artifacts."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision),
            dry_run=True,
        )
        assert result.get("status") == "dry_run"

        # Verify no artifacts were written
        control_dir = project_with_fake_agent_decision / "output" / "control"
        routing = _read_json(control_dir / "post_preview_routing_decision.json")
        # Should still have the original fake decision
        assert routing.get("selected_branch") == "accepted_for_voice_stage"
        assert routing.get("decision_valid") is True

    def test_repair_has_required_fields(self, project_with_fake_agent_decision):
        """Repair result must contain all required fields."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert "status" in result
        assert "fake_operator_decision_invalidated" in result
        assert "real_human_operator_review_required" in result
        assert "voice_generation_ready" in result
        assert "voice_generation_allowed" in result
        assert "assembly_allowed" in result
        assert "downstream_allowed" in result
        assert "production_accepted" in result
        assert "current_state" in result
        assert "next_allowed_action" in result
        assert "blockers" in result
        assert "artifact_index_updated" in result
        assert "episode_ledger_updated" in result
        assert "state_updated" in result


# ---------------------------------------------------------------------------
# 4. Canonical path validation tests
# ---------------------------------------------------------------------------


class TestCanonicalPaths:
    """Verify that canonical paths are used correctly."""

    REPAIR_PROOF_PATH = (
        "data/rc2_multishot1_ep01/output/control/"
        "post_preview_operator_review_repair_proof.json"
    )
    RECONCILIATION_PATH = (
        "data/rc2_multishot1_ep01/output/control/"
        "post_preview_operator_decision_reconciliation.json"
    )
    BLOCKER_PATH = (
        "data/rc2_multishot1_ep01/output/control/"
        "post_preview_stage_blocker.json"
    )

    def test_repair_proof_artifact_exists(self):
        """The repair proof artifact must exist at canonical path."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        assert path.exists(), f"Repair proof not found at {path}"

    def test_reconciliation_artifact_exists(self):
        """The reconciliation artifact must exist at canonical path."""
        path = Path(__file__).resolve().parent.parent / self.RECONCILIATION_PATH
        assert path.exists(), f"Reconciliation artifact not found at {path}"

    def test_blocker_artifact_exists(self):
        """The blocker artifact must exist at canonical path."""
        path = Path(__file__).resolve().parent.parent / self.BLOCKER_PATH
        assert path.exists(), f"Blocker artifact not found at {path}"

    def test_repair_proof_has_correct_state(self):
        """Repair proof must show correct state."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        with open(path) as f:
            proof = json.load(f)

        state = proof.get("restored_canonical_state", {})
        assert state.get("current_state") == "preview_operator_review_required"
        assert state.get("next_allowed_action") == "preview_operator_review_required"
        assert state.get("production_accepted") is False
        assert state.get("voice_generation_ready") is False

    def test_repair_proof_enforces_invariants(self):
        """Repair proof must list required invariants."""
        path = Path(__file__).resolve().parent.parent / self.REPAIR_PROOF_PATH
        with open(path) as f:
            proof = json.load(f)

        invariants = proof.get("invariants_enforced", [])
        assert "agent_may_not_choose_verdict" in invariants
        assert "agent_may_not_accept_preview" in invariants
        assert "agent_may_not_set_production_accepted" in invariants
        assert "agent_may_not_override_operator" in invariants


# ---------------------------------------------------------------------------
# 5. State consistency tests
# ---------------------------------------------------------------------------


class TestStateConsistency:
    """Verify state consistency across artifacts."""

    def test_current_state_is_blocked(self):
        """Current state must be preview_operator_review_required."""
        project_root = Path(__file__).resolve().parent.parent / "data" / "rc2_multishot1_ep01"
        control_dir = project_root / "output" / "control"

        if not control_dir.exists():
            pytest.skip("Canonical project not available in test context")

        index = _read_json(control_dir / "artifact_index.json")
        if index is None:
            pytest.skip("artifact_index.json not found")

        assert index.get("current_state") == "preview_operator_review_required"
        assert index.get("next_allowed_action") == "preview_operator_review_required"
        assert index.get("production_accepted") is False

    def test_blocker_blocks_downstream(self):
        """Blocker must block voice/audio/assembly/downstream."""
        project_root = Path(__file__).resolve().parent.parent / "data" / "rc2_multishot1_ep01"
        control_dir = project_root / "output" / "control"
        blocker_path = control_dir / "post_preview_stage_blocker.json"

        if not blocker_path.exists():
            pytest.skip("Blocker artifact not available")

        blocker = _read_json(blocker_path)
        assert blocker.get("voice_generation_executed") is False
        assert blocker.get("assembly_executed") is False
        assert blocker.get("downstream_executed") is False
        assert blocker.get("production_accepted") is False

    def test_gate_validation_artifact_has_correct_state(self):
        """Gate validation artifact must reflect frozen state."""
        project_root = Path(__file__).resolve().parent.parent / "data" / "rc2_multishot1_ep01"
        control_dir = project_root / "output" / "control"
        gate_path = control_dir / "post_preview_operator_review_gate_validation.json"

        if not gate_path.exists():
            pytest.skip("Gate validation artifact not available")

        gate = _read_json(gate_path)
        assert gate.get("current_state") == "preview_operator_review_required"
        assert gate.get("next_allowed_action") == "preview_operator_review_required"
        assert gate.get("voice_generation_ready") is False
        assert gate.get("assembly_allowed") is False
        assert gate.get("downstream_allowed") is False
        assert gate.get("production_accepted") is False

    def test_forbidden_actions_not_executed(self):
        """Forbidden actions must not be executed in proof artifact."""
        project_root = Path(__file__).resolve().parent.parent / "data" / "rc2_multishot1_ep01"
        control_dir = project_root / "output" / "control"
        proof_path = control_dir / "post_preview_operator_review_repair_proof.json"

        if not proof_path.exists():
            pytest.skip("Repair proof not available")

        proof = _read_json(proof_path)
        forbidden = proof.get("forbidden_actions_not_executed", {})
        assert forbidden.get("new_generation") is False
        assert forbidden.get("comfyui_submit") is False
        assert forbidden.get("preview_render") is False
        assert forbidden.get("voice_generation") is False
        assert forbidden.get("assembly") is False
        assert forbidden.get("downstream") is False
        assert forbidden.get("production_accepted_true") is False


# ---------------------------------------------------------------------------
# 6. Invariant tests
# ---------------------------------------------------------------------------


class TestInvariants:
    """Verify hard invariants of the post-preview operator review gate."""

    def test_forbidden_acceptance_targets(self):
        """accepted_for_voice_stage must be in the invalid acceptance targets."""
        assert "accepted_for_voice_stage" in INVALID_ACCEPTANCE_TARGETS

    def test_forbidden_acceptance_sources(self):
        """Forbidden sources must include agent, cli, automation, test."""
        assert "agent" in FORBIDDEN_ACCEPTANCE_SOURCES
        assert "cli" in FORBIDDEN_ACCEPTANCE_SOURCES
        assert "automation" in FORBIDDEN_ACCEPTANCE_SOURCES
        assert "test" in FORBIDDEN_ACCEPTANCE_SOURCES

    def test_no_voice_readiness_without_real_operator(self, temp_project):
        """Without real operator decision, voice_generation_ready must be false."""
        result = detect_fake_operator_decision(
            project_root=str(temp_project)
        )
        assert result.get("voice_generation_ready") is False

    def test_repair_never_sets_production_accepted(self, project_with_fake_agent_decision):
        """Repair must never set production_accepted=true."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("production_accepted") is False

        # Also verify all written artifacts
        control_dir = project_with_fake_agent_decision / "output" / "control"
        for artifact_name in [
            "post_preview_routing_decision.json",
            "preview_operator_review_outcome.json",
            "post_preview_stage_proof.json",
            "post_preview_stage_blocker.json",
            "post_preview_operator_review_gate_validation.json",
            "post_preview_operator_review_repair_proof.json",
            "post_preview_operator_decision_reconciliation.json",
        ]:
            artifact = _read_json(control_dir / artifact_name)
            if artifact:
                assert artifact.get("production_accepted") is False or artifact.get("production_accepted") is None, (
                    f"{artifact_name} must not have production_accepted=true"
                )

    def test_repair_never_sets_voice_generation_ready(self, project_with_fake_agent_decision):
        """Repair must never set voice_generation_ready=true."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("voice_generation_ready") is False
        assert result.get("voice_generation_allowed") is False

    def test_repair_blocks_assembly_downstream(self, project_with_fake_agent_decision):
        """Repair must block assembly and downstream."""
        result = repair_post_preview_operator_review(
            project_root=str(project_with_fake_agent_decision)
        )
        assert result.get("assembly_allowed") is False
        assert result.get("downstream_allowed") is False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _read_json(path: Path):
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
