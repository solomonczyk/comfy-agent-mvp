"""RC-COMBINE-V2-REAL-HUMAN-PREVIEW-REVIEW-DECISION-001 — Regression tests.

Tests for the real human operator preview review decision intake package:
- Rejects agent/CLI/automation-generated decisions
- Requires real human operator evidence for valid decisions
- Routes correctly for accepted_for_next_stage, rejected, needs_manual_review
- Keeps production_accepted=false in all branches
- Keeps voice/assembly/downstream blocked
- Creates all required canonical artifacts
- Updates artifact_index and episode_ledger
- Prevents fake progression
"""

import json
import tempfile
from pathlib import Path

import pytest

from app.post_preview.operator_decision_intake import (
    TASK_ID,
    VALID_VERDICTS,
    REQUIRED_PREVIEW_ARTIFACTS,
    FORBIDDEN_ACCEPTANCE_SOURCES,
    EXPECTED_DECISION_FILENAME,
    validate_human_operator_decision,
    find_human_operator_decision,
    build_validation_report,
    build_decision_schema_artifact,
    build_decision_blocker,
    get_routing_for_verdict,
    process_human_operator_decision,
    combine_validate_post_preview_human_decision,
    combine_process_post_preview_human_decision,
)

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

VALID_HUMAN_ACCEPTED_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "operator_name_or_id": "operator_123",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "review_notes": "Preview looks good, proceed to voice authorization.",
    "review_timestamp": "2026-05-09T12:00:00+00:00",
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
    "voice_generation_authorized": False,
    "assembly_authorized": False,
    "downstream_authorized": False,
}

VALID_HUMAN_REJECTED_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "rejected",
    "operator_name_or_id": "operator_123",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "review_notes": "Preview quality not acceptable. Several issues need correction.",
    "review_timestamp": "2026-05-09T12:00:00+00:00",
    "visual_or_editorial_issues": [
        "color_banding",
        "frame_skip",
    ],
    "next_required_action": "post_preview_corrective_plan_required",
    "production_accepted": False,
}

VALID_HUMAN_MANUAL_REVIEW_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "needs_manual_review",
    "operator_name_or_id": "operator_123",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "review_notes": "Some elements need closer analysis.",
    "next_required_action": "preview_operator_review_required",
    "production_accepted": False,
}

AGENT_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
    "created_by": "agent_verification",
    "voice_generation_authorized": False,
    "assembly_authorized": False,
    "downstream_authorized": False,
}

CLI_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
    "created_by": "cli_test_runner",
    "voice_generation_authorized": False,
    "assembly_authorized": False,
    "downstream_authorized": False,
}

AUTOMATION_DECISION = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
    "created_by": "automation_pipeline",
    "voice_generation_authorized": False,
    "assembly_authorized": False,
    "downstream_authorized": False,
}

DECISION_WITH_PROD_ACCEPTED = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": True,
}

DECISION_MISSING_ARTIFACTS = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
}

DECISION_INVALID_VERDICT = {
    "decision_source": "human_operator",
    "operator_verdict": "invalid_verdict_value",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
}

DECISION_WITH_VOICE_AUTHORIZED = {
    "decision_source": "human_operator",
    "operator_verdict": "accepted_for_next_stage",
    "reviewed_preview_artifacts": [
        "preview_lowres.mp4",
        "preview.gif",
        "contact_sheet.jpg",
    ],
    "acceptance_scope": "preview_stage_only",
    "production_accepted": False,
    "voice_generation_authorized": True,
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
def project_with_human_accepted_decision(temp_project):
    """Create a project with a valid human accepted decision."""
    control_dir = temp_project / "output" / "control"
    _write_json(control_dir / EXPECTED_DECISION_FILENAME, VALID_HUMAN_ACCEPTED_DECISION)
    yield temp_project


@pytest.fixture
def project_with_human_rejected_decision(temp_project):
    """Create a project with a valid human rejected decision."""
    control_dir = temp_project / "output" / "control"
    _write_json(control_dir / EXPECTED_DECISION_FILENAME, VALID_HUMAN_REJECTED_DECISION)
    yield temp_project


@pytest.fixture
def project_with_human_manual_review_decision(temp_project):
    """Create a project with a valid human needs_manual_review decision."""
    control_dir = temp_project / "output" / "control"
    _write_json(control_dir / EXPECTED_DECISION_FILENAME, VALID_HUMAN_MANUAL_REVIEW_DECISION)
    yield temp_project


# ---------------------------------------------------------------------------
# 1. Missing operator decision keeps state at preview_operator_review_required
# ---------------------------------------------------------------------------


class TestMissingDecision:
    """Tests for when no human operator decision file exists."""

    def test_missing_decision_keeps_state_blocked(self, temp_project):
        """Missing operator decision must keep state at preview_operator_review_required."""
        result = process_human_operator_decision(project_root=str(temp_project))

        assert result.get("decision_found") is False
        assert result.get("operator_verdict") == "missing"
        assert result.get("current_state") == "preview_operator_review_required"
        assert result.get("next_allowed_action") == "preview_operator_review_required"
        assert result.get("production_accepted") is False
        assert result.get("voice_generation_executed") is False

    def test_missing_decision_creates_blocker(self, temp_project):
        """Missing decision must create a blocker artifact."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        blocker_path = control_dir / "post_preview_operator_decision_blocker.json"
        assert blocker_path.exists()

        blocker = _read_json(blocker_path)
        assert blocker.get("blocker_type") == "missing_human_operator_preview_review"
        assert blocker.get("stage_blocked") is True
        assert blocker.get("current_state") == "preview_operator_review_required"
        assert blocker.get("production_accepted") is False

    def test_missing_decision_validate_returns_blocked_status(self, temp_project):
        """Validate command must return blocked_waiting_for_human_operator_decision."""
        result = combine_validate_post_preview_human_decision(
            project_root=str(temp_project)
        )
        assert result.get("status") == "blocked_waiting_for_human_operator_decision"
        assert result.get("decision_found") is False


# ---------------------------------------------------------------------------
# 2-4. Agent/CLI/automation-generated decisions are rejected
# ---------------------------------------------------------------------------


class TestRejectNonHumanDecisions:
    """Tests that agent/CLI/automation-generated decisions are rejected."""

    @pytest.mark.parametrize("decision,source_label", [
        (AGENT_DECISION, "agent"),
        (CLI_DECISION, "CLI"),
        (AUTOMATION_DECISION, "automation"),
    ])
    def test_non_human_source_rejected(self, temp_project, decision, source_label):
        """Decisions with forbidden created_by source must be rejected."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / EXPECTED_DECISION_FILENAME, decision)

        result = process_human_operator_decision(project_root=str(temp_project))
        assert result.get("decision_valid") is False, (
            f"{source_label}-generated decision should be rejected"
        )
        assert result.get("decision_found") is False
        assert result.get("current_state") == "preview_operator_review_required"
        assert result.get("production_accepted") is False

    def test_all_forbidden_sources_are_rejected(self, temp_project):
        """Each forbidden source must be rejected individually."""
        for source in FORBIDDEN_ACCEPTANCE_SOURCES:
            decision = dict(VALID_HUMAN_ACCEPTED_DECISION)
            decision["created_by"] = source
            decision["decision_source"] = "human_operator"

            control_dir = temp_project / "output" / "control"
            _write_json(control_dir / EXPECTED_DECISION_FILENAME, decision)

            valid, msg = validate_human_operator_decision(decision)
            assert not valid, (
                f"Forbidden source '{source}' should be rejected. "
                f"Got message: {msg}"
            )
            assert source in msg.lower() or "forbidden" in msg.lower(), (
                f"Message should reference the forbidden source. Got: {msg}"
            )

    def test_non_human_decision_source_rejected(self, temp_project):
        """decision_source != human_operator must be rejected."""
        bad_source = AGENT_DECISION.copy()
        bad_source["decision_source"] = "agent"
        bad_source.pop("created_by", None)

        valid, msg = validate_human_operator_decision(bad_source)
        assert not valid
        assert "agent" in msg


# ---------------------------------------------------------------------------
# 5-9. accepted_for_next_stage routing
# ---------------------------------------------------------------------------


class TestAcceptedForNextStage:
    """Tests for accepted_for_next_stage verdict routing."""

    def test_accepted_routes_to_voice_authorization(self, project_with_human_accepted_decision):
        """Accepted verdict must route to voice_generation_authorization_required."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        assert result.get("operator_verdict") == "accepted_for_next_stage"
        assert result.get("current_state") == "voice_generation_authorization_required"
        assert result.get("next_allowed_action") == "voice_generation_authorization_required"

    def test_accepted_does_not_execute_voice(self, project_with_human_accepted_decision):
        """Accepted verdict must NOT execute voice generation."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        assert result.get("voice_generation_executed") is False
        assert result.get("voice_generation_ready") is False

    def test_accepted_does_not_authorize_assembly(self, project_with_human_accepted_decision):
        """Accepted verdict must NOT authorize assembly."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        assert result.get("assembly_allowed") is False

    def test_accepted_does_not_authorize_downstream(self, project_with_human_accepted_decision):
        """Accepted verdict must NOT authorize downstream."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        assert result.get("downstream_allowed") is False

    def test_accepted_does_not_set_production_accepted(self, project_with_human_accepted_decision):
        """Accepted verdict must NOT set production_accepted=true."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        assert result.get("production_accepted") is False

        # Also verify all written artifacts
        control_dir = project_with_human_accepted_decision / "output" / "control"
        for artifact_name in [
            "post_preview_operator_decision_proof.json",
            "post_preview_operator_decision_routing_result.json",
            "post_preview_operator_decision_validation_report.json",
        ]:
            artifact = _read_json(control_dir / artifact_name)
            if artifact:
                pa = artifact.get("production_accepted")
                assert pa is False or pa is None, (
                    f"{artifact_name} must not have production_accepted=true"
                )

    def test_accepted_valid_human_decision_passes_validation(self, temp_project):
        """A valid human accepted decision must pass validation."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / EXPECTED_DECISION_FILENAME, VALID_HUMAN_ACCEPTED_DECISION)

        found, decision, msg = find_human_operator_decision(control_dir)
        assert found, f"Decision should be found. Got: {msg}"
        assert decision is not None


# ---------------------------------------------------------------------------
# 10. Rejected decision routing
# ---------------------------------------------------------------------------


class TestRejectedDecision:
    """Tests for rejected verdict routing."""

    def test_rejected_routes_to_corrective_plan(self, project_with_human_rejected_decision):
        """Rejected verdict must route to post_preview_corrective_plan_required."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_rejected_decision)
        )
        assert result.get("operator_verdict") == "rejected"
        assert result.get("current_state") == "post_preview_corrective_plan_required"
        assert result.get("next_allowed_action") == "post_preview_corrective_plan_required"
        assert result.get("production_accepted") is False
        assert result.get("voice_generation_executed") is False

    def test_rejected_review_notes_required(self, temp_project):
        """Rejected verdict must have review notes."""
        bad = dict(VALID_HUMAN_REJECTED_DECISION)
        bad.pop("review_notes", None)

        valid, msg = validate_human_operator_decision(bad)
        assert not valid
        assert "review_notes" in msg.lower() or "rejected" in msg.lower()


# ---------------------------------------------------------------------------
# 11. needs_manual_review routing
# ---------------------------------------------------------------------------


class TestNeedsManualReview:
    """Tests for needs_manual_review verdict routing."""

    def test_manual_review_keeps_state_blocked(self, project_with_human_manual_review_decision):
        """needs_manual_review must keep state at preview_operator_review_required."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_manual_review_decision)
        )
        assert result.get("operator_verdict") == "needs_manual_review"
        assert result.get("current_state") == "preview_operator_review_required"
        assert result.get("next_allowed_action") == "preview_operator_review_required"
        assert result.get("production_accepted") is False

    def test_manual_review_blocks_downstream(self, project_with_human_manual_review_decision):
        """needs_manual_review must keep all downstream blocked."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_manual_review_decision)
        )
        assert result.get("voice_generation_executed") is False
        assert result.get("assembly_allowed") is False
        assert result.get("downstream_allowed") is False


# ---------------------------------------------------------------------------
# 12. Missing preview artifacts reference rejects decision
# ---------------------------------------------------------------------------


class TestMissingArtifacts:
    """Tests that missing preview artifact references reject the decision."""

    def test_missing_reviewed_artifacts_rejected(self, temp_project):
        """Decision without reviewed_preview_artifacts must be rejected."""
        valid, msg = validate_human_operator_decision(DECISION_MISSING_ARTIFACTS)
        assert not valid
        assert "artifact" in msg.lower()

    def test_empty_reviewed_artifacts_rejected(self, temp_project):
        """Decision with empty reviewed_preview_artifacts must be rejected."""
        bad = dict(VALID_HUMAN_ACCEPTED_DECISION)
        bad["reviewed_preview_artifacts"] = []

        valid, msg = validate_human_operator_decision(bad)
        assert not valid
        assert "artifact" in msg.lower()


# ---------------------------------------------------------------------------
# 13. Invalid verdict rejects decision
# ---------------------------------------------------------------------------


class TestInvalidVerdict:
    """Tests that invalid verdict values are rejected."""

    def test_invalid_verdict_value_rejected(self, temp_project):
        """Invalid verdict must be rejected."""
        valid, msg = validate_human_operator_decision(DECISION_INVALID_VERDICT)
        assert not valid
        assert "operator_verdict" in msg or "verdict" in msg.lower()

    def test_empty_verdict_rejected(self, temp_project):
        """Empty verdict must be rejected."""
        bad = dict(VALID_HUMAN_ACCEPTED_DECISION)
        bad["operator_verdict"] = ""

        valid, msg = validate_human_operator_decision(bad)
        assert not valid

    def test_all_valid_verdicts_accepted(self, temp_project):
        """All valid verdicts must be accepted when other fields are valid."""
        base = dict(VALID_HUMAN_ACCEPTED_DECISION)
        for verdict in VALID_VERDICTS:
            d = dict(base)
            d["operator_verdict"] = verdict
            if verdict == "rejected":
                d["review_notes"] = "Not acceptable."
            if verdict == "accepted_for_next_stage":
                d["acceptance_scope"] = "preview_stage_only"
            if verdict == "needs_manual_review":
                d.pop("acceptance_scope", None)

            valid, msg = validate_human_operator_decision(d)
            assert valid, f"Verdict '{verdict}' should be valid. Got: {msg}"


# ---------------------------------------------------------------------------
# 14. Invalid JSON creates blocker
# ---------------------------------------------------------------------------


class TestInvalidJSON:
    """Tests that invalid JSON in the decision file creates a blocker."""

    def test_invalid_json_creates_blocker(self, temp_project):
        """Invalid JSON must create a blocker and keep state."""
        control_dir = temp_project / "output" / "control"
        # Write non-JSON content
        decision_path = control_dir / EXPECTED_DECISION_FILENAME
        with open(decision_path, "w") as f:
            f.write("this is not json")

        result = process_human_operator_decision(project_root=str(temp_project))
        assert result.get("decision_found") is False
        assert result.get("current_state") == "preview_operator_review_required"
        assert result.get("operator_verdict") == "missing"

        # Check blocker was created
        blocker_path = control_dir / "post_preview_operator_decision_blocker.json"
        assert blocker_path.exists()

    def test_corrupted_json_creates_blocker(self, temp_project):
        """Corrupted JSON file must create a blocker."""
        control_dir = temp_project / "output" / "control"
        decision_path = control_dir / EXPECTED_DECISION_FILENAME
        with open(decision_path, "w") as f:
            f.write("{invalid json content")

        found, decision, msg = find_human_operator_decision(control_dir)
        assert not found
        assert "invalid JSON" in msg


# ---------------------------------------------------------------------------
# 15-16. artifact_index and episode_ledger updated
# ---------------------------------------------------------------------------


class TestArtifactIndexAndLedger:
    """Tests that artifact_index.json and episode_ledger.json are updated."""

    def test_artifact_index_updated_missing_decision(self, temp_project):
        """Artifact index must be updated when decision is missing."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        index = _read_json(control_dir / "artifact_index.json")
        assert index is not None

        assert index.get("current_state") == "preview_operator_review_required"
        assert index.get("next_allowed_action") == "preview_operator_review_required"
        assert index.get("production_accepted") is False

        # Check new artifacts registered
        artifacts = index.get("post_preview_artifacts", [])
        assert "post_preview_operator_decision_schema.json" in artifacts
        assert "post_preview_operator_decision_validation_report.json" in artifacts
        assert "post_preview_operator_decision_routing_result.json" in artifacts
        assert "post_preview_operator_decision_blocker.json" in artifacts
        assert "post_preview_operator_decision_proof.json" in artifacts

    def test_artifact_index_updated_accepted_decision(self, project_with_human_accepted_decision):
        """Artifact index must be updated when decision is accepted."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )
        control_dir = project_with_human_accepted_decision / "output" / "control"
        index = _read_json(control_dir / "artifact_index.json")

        assert index.get("current_state") == "voice_generation_authorization_required"
        assert index.get("next_allowed_action") == "voice_generation_authorization_required"
        assert index.get("production_accepted") is False

    def test_episode_ledger_updated_missing_decision(self, temp_project):
        """Episode ledger must be updated when decision is missing."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        ledger = _read_json(control_dir / "episode_ledger.json")
        assert ledger is not None
        assert isinstance(ledger, list)

        events = [
            e for e in ledger
            if e.get("event") == "post_preview_human_operator_decision_required"
        ]
        assert len(events) >= 1

        event = events[0]
        assert event.get("task_id") == TASK_ID
        assert event.get("production_accepted") is False
        assert event.get("state_after") == "preview_operator_review_required"

    def test_episode_ledger_updated_accepted_decision(self, project_with_human_accepted_decision):
        """Episode ledger must reflect the accepted decision."""
        process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )

        control_dir = project_with_human_accepted_decision / "output" / "control"
        ledger = _read_json(control_dir / "episode_ledger.json")

        events = [
            e for e in ledger
            if e.get("event") == "post_preview_human_operator_decision_processed"
        ]
        assert len(events) >= 1

        event = events[0]
        assert event.get("operator_verdict") == "accepted_for_next_stage"
        assert event.get("production_accepted") is False
        assert event.get("voice_generation_executed") is False

    def test_episode_ledger_updated_rejected_decision(self, project_with_human_rejected_decision):
        """Episode ledger must reflect the rejected decision."""
        process_human_operator_decision(
            project_root=str(project_with_human_rejected_decision)
        )

        control_dir = project_with_human_rejected_decision / "output" / "control"
        ledger = _read_json(control_dir / "episode_ledger.json")

        events = [
            e for e in ledger
            if e.get("event") == "post_preview_human_operator_decision_processed"
        ]
        assert len(events) >= 1

        event = events[0]
        assert event.get("operator_verdict") == "rejected"
        assert event.get("state_after") == "post_preview_corrective_plan_required"
        assert event.get("production_accepted") is False


# ---------------------------------------------------------------------------
# 17. Proof JSON schema valid
# ---------------------------------------------------------------------------


class TestProofSchema:
    """Tests that the proof artifact has valid schema."""

    def test_proof_has_required_fields(self, temp_project):
        """Proof must have all required fields from the task specification."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        proof = _read_json(control_dir / "post_preview_operator_decision_proof.json")
        assert proof is not None

        required_fields = [
            "task_id",
            "feature_completed",
            "full_feature_loop_executed",
            "allowed_scope_respected",
            "forbidden_actions_not_executed",
            "operator_decision_schema_created",
            "operator_decision_validation_implemented",
            "operator_decision_routing_implemented",
            "real_human_operator_decision_present",
            "operator_decision_valid",
            "operator_verdict",
            "fake_operator_decision_rejected",
            "generation_performed",
            "comfyui_submit_executed",
            "preview_render_executed",
            "voice_generation_executed",
            "audio_generation_executed",
            "visual_acceptance_executed",
            "assembly_executed",
            "downstream_executed",
            "production_accepted",
            "voice_generation_ready",
            "assembly_allowed",
            "downstream_allowed",
            "required_artifacts_created",
            "artifact_index_updated",
            "episode_ledger_updated",
            "state_updated",
            "current_state",
            "next_allowed_action",
            "blockers",
        ]
        for field in required_fields:
            assert field in proof, f"Proof missing required field: {field}"

    def test_proof_forbidden_actions_false(self, temp_project):
        """Proof must show all forbidden actions as false."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        proof = _read_json(control_dir / "post_preview_operator_decision_proof.json")

        assert proof.get("generation_performed") is False
        assert proof.get("comfyui_submit_executed") is False
        assert proof.get("retry_attempted") is False
        assert proof.get("preview_render_executed") is False
        assert proof.get("voice_generation_executed") is False
        assert proof.get("audio_generation_executed") is False
        assert proof.get("visual_qa_executed") is False
        assert proof.get("visual_acceptance_executed") is False
        assert proof.get("assembly_executed") is False
        assert proof.get("downstream_executed") is False
        assert proof.get("production_accepted") is False

    def test_proof_blockers_structure(self, temp_project):
        """Proof blockers must have correct structure."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        proof = _read_json(control_dir / "post_preview_operator_decision_proof.json")

        blockers = proof.get("blockers", [])
        assert len(blockers) >= 1

        blocker = blockers[0]
        assert "blocker_type" in blocker
        assert "status" in blocker
        assert "blocks" in blocker
        assert "voice_generation_execution" in blocker["blocks"]
        assert "production_accepted_true" in blocker["blocks"]


# ---------------------------------------------------------------------------
# 18. Unrelated dirty files are not modified
# ---------------------------------------------------------------------------


class TestUnrelatedFilesNotModified:
    """Tests that unrelated dirty files are not modified."""

    UNRELATED_FILES = [
        "data/artifact_proofs/prompt_pack.json",
        "data/mk_real3r_proof/control_status.json",
        "data/mk_real3r_proof/ep01_shot01_observed_settings.json",
        "data/mk_real3r_proof/ep01_shot01_submitted_workflow.json",
    ]

    def test_module_does_not_write_unrelated_files(self):
        """The intake module must not write to unrelated dirty files.

        The module may reference unrelated file paths for status reporting
        in the proof artifact, but must not call _write_json or os operations
        on those paths. This test verifies that no write-path functions
        contain unrelated file references.
        """
        import ast

        module_path = Path(__file__).resolve().parent.parent / "app" / "post_preview" / "operator_decision_intake.py"
        with open(module_path) as f:
            tree = ast.parse(f.read())

        # Collect all string literals inside function calls (potential write targets)
        write_related_strings = set()
        for node in ast.walk(tree):
            # Look for _write_json calls or open() calls with unrelated paths
            if isinstance(node, ast.Call):
                for arg in node.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        write_related_strings.add(arg.value)

        for unrelated in self.UNRELATED_FILES:
            # The file path should NOT appear as a direct argument to any call
            direct_refs = [s for s in write_related_strings if s == unrelated]
            assert len(direct_refs) == 0, (
                f"Module must not use unrelated dirty file path in a call: {unrelated}. "
                f"Found direct references: {direct_refs}"
            )


# ---------------------------------------------------------------------------
# 19. Generation/retry/comfyui/preview/voice/audio/assembly/downstream flags
# ---------------------------------------------------------------------------


class TestForbiddenFlags:
    """Tests that all forbidden action flags remain false."""

    FORBIDDEN_FLAGS = {
        "generation_performed": False,
        "retry_attempted": False,
        "comfyui_submit_executed": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "audio_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
    }

    def test_forbidden_flags_false_in_proof(self, temp_project):
        """All forbidden flags must be false in the proof artifact."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        proof = _read_json(control_dir / "post_preview_operator_decision_proof.json")

        for flag, expected in self.FORBIDDEN_FLAGS.items():
            value = proof.get(flag)
            assert value is False or value is None, (
                f"Forbidden flag '{flag}' must be false, got {value}"
            )

    def test_forbidden_flags_false_in_result(self, project_with_human_accepted_decision):
        """All forbidden flags must be false in the process result."""
        result = process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )

        for flag in self.FORBIDDEN_FLAGS:
            value = result.get(flag)
            assert value is False or value is None, (
                f"Forbidden flag '{flag}' must be false in result, got {value}"
            )

    def test_forbidden_flags_false_in_all_artifacts(self, project_with_human_accepted_decision):
        """All forbidden flags must be false across all artifacts."""
        process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )

        control_dir = project_with_human_accepted_decision / "output" / "control"
        for artifact_name in [
            "post_preview_operator_decision_proof.json",
            "post_preview_operator_decision_routing_result.json",
            "post_preview_operator_decision_validation_report.json",
        ]:
            artifact = _read_json(control_dir / artifact_name)
            if not artifact:
                continue
            for flag in self.FORBIDDEN_FLAGS:
                value = artifact.get(flag)
                if value is not None:
                    assert value is False, (
                        f"Flag '{flag}' in {artifact_name} must be false, got {value}"
                    )


# ---------------------------------------------------------------------------
# Additional: Schema artifact creation
# ---------------------------------------------------------------------------


class TestSchemaArtifact:
    """Tests that the schema artifact is correctly created."""

    def test_schema_artifact_created(self, temp_project):
        """Schema artifact must be created by the process command."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        schema_path = control_dir / "post_preview_operator_decision_schema.json"
        assert schema_path.exists()

    def test_schema_has_valid_structure(self, temp_project):
        """Schema must have the correct structure."""
        schema = build_decision_schema_artifact()
        assert "$schema" in schema
        assert "title" in schema
        assert "schema_definition" in schema
        assert "routing_rules" in schema
        assert "forbidden_actions" in schema

        routing = schema.get("routing_rules", {})
        assert "accepted_for_next_stage" in routing
        assert "rejected" in routing
        assert "needs_manual_review" in routing
        assert "missing" in routing

    def test_schema_routing_rules_correct(self, temp_project):
        """Schema routing rules must match spec."""
        schema = build_decision_schema_artifact()
        routing = schema.get("routing_rules", {})

        accepted = routing["accepted_for_next_stage"]
        assert accepted["current_state"] == "voice_generation_authorization_required"
        assert accepted["production_accepted"] is False

        rejected = routing["rejected"]
        assert rejected["current_state"] == "post_preview_corrective_plan_required"
        assert rejected["production_accepted"] is False

        manual = routing["needs_manual_review"]
        assert manual["current_state"] == "preview_operator_review_required"
        assert manual["production_accepted"] is False

        missing = routing["missing"]
        assert missing["current_state"] == "preview_operator_review_required"
        assert missing["production_accepted"] is False

    def test_schema_forbidden_actions_all_false(self, temp_project):
        """Schema forbidden actions must all be false."""
        schema = build_decision_schema_artifact()
        forbidden = schema.get("forbidden_actions", {})
        for action, value in forbidden.items():
            assert value is False, (
                f"Forbidden action '{action}' must be false"
            )


# ---------------------------------------------------------------------------
# Additional: Routing result artifact
# ---------------------------------------------------------------------------


class TestRoutingResult:
    """Tests for the routing result artifact."""

    def test_routing_result_created(self, temp_project):
        """Routing result artifact must be created."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        routing_path = control_dir / "post_preview_operator_decision_routing_result.json"
        assert routing_path.exists()

    def test_routing_result_correct_for_missing(self, temp_project):
        """Routing result must show correct state for missing decision."""
        process_human_operator_decision(project_root=str(temp_project))

        control_dir = temp_project / "output" / "control"
        routing = _read_json(control_dir / "post_preview_operator_decision_routing_result.json")

        assert routing.get("operator_verdict") == "missing"
        assert routing.get("routing_state") == "preview_operator_review_required"
        assert routing.get("next_allowed_action") == "preview_operator_review_required"
        assert routing.get("production_accepted") is False

    def test_routing_result_correct_for_accepted(self, project_with_human_accepted_decision):
        """Routing result must show correct state for accepted decision."""
        process_human_operator_decision(
            project_root=str(project_with_human_accepted_decision)
        )

        control_dir = project_with_human_accepted_decision / "output" / "control"
        routing = _read_json(control_dir / "post_preview_operator_decision_routing_result.json")

        assert routing.get("operator_verdict") == "accepted_for_next_stage"
        assert routing.get("routing_state") == "voice_generation_authorization_required"
        assert routing.get("production_accepted") is False


# ---------------------------------------------------------------------------
# Additional: production_accepted=true rejection
# ---------------------------------------------------------------------------


class TestProductionAcceptedRejection:
    """Tests that production_accepted=true is rejected."""

    def test_production_accepted_true_rejected(self, temp_project):
        """A decision with production_accepted=true must be rejected."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / EXPECTED_DECISION_FILENAME, DECISION_WITH_PROD_ACCEPTED)

        result = process_human_operator_decision(project_root=str(temp_project))
        assert result.get("decision_valid") is False
        assert result.get("current_state") == "preview_operator_review_required"
        assert result.get("production_accepted") is False


# ---------------------------------------------------------------------------
# Additional: voice_generation_authorized=true rejection
# ---------------------------------------------------------------------------


class TestVoiceAuthorizedRejection:
    """Tests that voice_generation_authorized=true is rejected."""

    def test_voice_authorized_true_rejected(self, temp_project):
        """A decision with voice_generation_authorized=true must be rejected."""
        control_dir = temp_project / "output" / "control"
        _write_json(control_dir / EXPECTED_DECISION_FILENAME, DECISION_WITH_VOICE_AUTHORIZED)

        valid, msg = validate_human_operator_decision(DECISION_WITH_VOICE_AUTHORIZED)
        assert not valid
        assert "voice_generation_authorized" in msg


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
