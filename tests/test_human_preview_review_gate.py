"""RC-COMBINE-V2-HUMAN-PREVIEW-REVIEW-GATE-001 — Human Preview Review Decision Gate Tests.

Covers: operator decision validation, ingestion, target state resolution with
state machine validation, gate proof creation, blocker creation, artifact index
and ledger updates, dry-run, and forbidden actions enforcement.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.orchestrator.state_machine import CombineStateMachine
from app.preview_review.human_preview_review_gate import (
    TASK_ID,
    VALID_VERDICTS,
    VERDICT_TO_TARGET_STATE,
    validate_operator_decision,
    read_operator_decision,
    resolve_target_state,
    build_gate_proof,
    build_blocker_packet,
    build_artifact_index_update,
    build_ledger_events,
    run_human_preview_review_gate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_episode(tmp_path: Path) -> Path:
    """Create a minimal episode directory structure with required artifacts."""
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Minimal preview artifacts (needed for earlier stage, gate only needs control dir)
    _write_json_file(preview_dir / "preview_lowres.mp4", b"fake mp4 content")
    _write_json_file(preview_dir / "preview.gif", b"fake gif content")
    _write_json_file(preview_dir / "contact_sheet.jpg", b"fake jpg content")

    # Minimal control artifacts
    _write_json_file(control_dir / "preview_render_report.json", {"rendered": True})
    _write_json_file(control_dir / "preview_result_review.json", {"valid": True})
    _write_json_file(
        control_dir / "preview_operator_review_packet.json", {"review": True}
    )

    # Artifact index and ledger
    _write_json_file(
        control_dir / "artifact_index.json",
        {
            "current_state": "preview_operator_review_required",
            "next_allowed_action": "preview_operator_review_required",
            "production_accepted": False,
        },
    )
    _write_json_file(control_dir / "episode_ledger.json", [])

    return tmp_path


def _write_json_file(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(data, bytes):
        path.write_bytes(data)
    else:
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def _make_accepted_decision() -> Dict[str, Any]:
    return {
        "operator_verdict": "accepted_for_voice_stage",
        "operator_notes": "Preview looks good, proceed to voice stage.",
        "visual_review_performed_by_operator": True,
        "preview_lowres_reviewed": True,
        "preview_gif_reviewed": True,
        "contact_sheet_reviewed": True,
        "production_accepted": False,
    }


def _make_rejected_decision() -> Dict[str, Any]:
    return {
        "operator_verdict": "rejected",
        "operator_notes": "Major pacing issues, needs re-edit.",
        "visual_review_performed_by_operator": True,
        "preview_lowres_reviewed": True,
        "preview_gif_reviewed": True,
        "contact_sheet_reviewed": True,
        "production_accepted": False,
    }


def _make_needs_fix_decision() -> Dict[str, Any]:
    return {
        "operator_verdict": "needs_fix",
        "operator_notes": "Subtitle timing is slightly off on sub_002.",
        "visual_review_performed_by_operator": True,
        "preview_lowres_reviewed": True,
        "preview_gif_reviewed": True,
        "contact_sheet_reviewed": True,
        "production_accepted": False,
    }


# ---------------------------------------------------------------------------
# 1. Operator Decision Validation Tests
# ---------------------------------------------------------------------------


class TestValidateOperatorDecision:
    """Agent must NOT choose/accept/override verdicts."""

    def test_rejects_empty_decision(self) -> None:
        """Rejects empty decision object."""
        valid, msg = validate_operator_decision({})
        assert valid is False
        assert "Missing required fields" in msg

    def test_rejects_production_accepted_true(self) -> None:
        """production_accepted must be false at this gate."""
        decision = _make_accepted_decision()
        decision["production_accepted"] = True
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "production_accepted" in msg

    def test_rejects_visual_review_not_performed(self) -> None:
        """Agent must not set visual_review_performed_by_operator."""
        decision = _make_accepted_decision()
        decision["visual_review_performed_by_operator"] = False
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "visual_review_performed_by_operator" in msg

    def test_rejects_unknown_verdict(self) -> None:
        """Agent must not fabricate verdicts."""
        decision = _make_accepted_decision()
        decision["operator_verdict"] = "fake_accept"
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "Unknown operator_verdict" in msg
        assert "Agent must not fabricate" in msg

    def test_accepts_valid_accepted(self) -> None:
        """Valid accepted_for_voice_stage verdict."""
        valid, msg = validate_operator_decision(_make_accepted_decision())
        assert valid is True

    def test_accepts_valid_rejected(self) -> None:
        """Valid rejected verdict."""
        valid, msg = validate_operator_decision(_make_rejected_decision())
        assert valid is True

    def test_accepts_valid_needs_fix(self) -> None:
        """Valid needs_fix verdict."""
        valid, msg = validate_operator_decision(_make_needs_fix_decision())
        assert valid is True

    def test_rejects_non_dict_input(self) -> None:
        """Non-dict input is rejected."""
        valid, msg = validate_operator_decision("not_a_dict")  # type: ignore[arg-type]
        assert valid is False
        assert "not a valid JSON object" in msg


# ---------------------------------------------------------------------------
# 2. Operator Decision Ingestion Tests
# ---------------------------------------------------------------------------


class TestReadOperatorDecision:
    def test_blocks_missing_decision(self, tmp_episode: Path) -> None:
        """Blocks when decision file does not exist."""
        control_dir = tmp_episode / "output" / "control"
        found, _, msg = read_operator_decision(control_dir)
        assert found is False
        assert "not found" in msg

    def test_rejects_fake_production_accepted(self, tmp_episode: Path) -> None:
        """Rejects fake production_accepted=true."""
        control_dir = tmp_episode / "output" / "control"
        decision = _make_accepted_decision()
        decision["production_accepted"] = True
        _write_json_file(
            control_dir / "preview_operator_decision_input.json", decision
        )

        found, _, msg = read_operator_decision(control_dir)
        assert found is False, "Should not find invalid decision"
        assert "production_accepted" in msg

    def test_reads_valid_decision(self, tmp_episode: Path) -> None:
        """Reads a valid operator decision."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        found, data, msg = read_operator_decision(control_dir)
        assert found is True
        assert data is not None
        assert data["operator_verdict"] == "accepted_for_voice_stage"
        assert "valid" in msg.lower()

    def test_reads_with_custom_path(self, tmp_episode: Path) -> None:
        """Reads decision from a custom file path."""
        custom_path = tmp_episode / "custom_decision.json"
        _write_json_file(custom_path, _make_rejected_decision())

        found, data, msg = read_operator_decision(
            tmp_episode / "output" / "control", decision_file=str(custom_path)
        )
        assert found is True
        assert data is not None
        assert data["operator_verdict"] == "rejected"


# ---------------------------------------------------------------------------
# 3. Target State Resolution Tests
# ---------------------------------------------------------------------------


class TestResolveTargetState:
    def test_accepted_resolves_to_voice_auth(self) -> None:
        """accepted_for_voice_stage -> voice_generation_authorization_required."""
        valid, state, msg = resolve_target_state("accepted_for_voice_stage")
        assert valid is True
        assert state == "voice_generation_authorization_required"

    def test_rejected_resolves_to_correction_auth(self) -> None:
        """rejected -> preview_correction_authorization_required."""
        valid, state, msg = resolve_target_state("rejected")
        assert valid is True
        assert state == "preview_correction_authorization_required"

    def test_needs_fix_resolves_to_targeted_fix_auth(self) -> None:
        """needs_fix -> targeted_preview_fix_authorization_required."""
        valid, state, msg = resolve_target_state("needs_fix")
        assert valid is True
        assert state == "targeted_preview_fix_authorization_required"

    def test_unknown_verdict_fails(self) -> None:
        """Unknown verdict returns invalid."""
        valid, state, msg = resolve_target_state("bogus_verdict")
        assert valid is False
        assert state == ""

    def test_all_states_are_valid_in_state_machine(self) -> None:
        """Every target state exists in the CombineStateMachine."""
        for verdict, target_state in VERDICT_TO_TARGET_STATE.items():
            assert CombineStateMachine.is_valid_state(target_state), (
                f"Target state '{target_state}' (for verdict '{verdict}') "
                f"is not a valid state machine state."
            )

    def test_all_transitions_allowed_by_state_machine(self) -> None:
        """Every verdict transition is allowed by the state machine."""
        from_state = "preview_operator_review_required"
        for verdict, target_state in VERDICT_TO_TARGET_STATE.items():
            assert CombineStateMachine.can_transition(from_state, target_state), (
                f"Transition '{from_state}' -> '{target_state}' "
                f"(verdict '{verdict}') is not allowed by the state machine."
            )


# ---------------------------------------------------------------------------
# 4. Gate Run — Missing Decision Tests
# ---------------------------------------------------------------------------


class TestGateMissingDecision:
    def test_blocks_missing_operator_decision(self, tmp_episode: Path) -> None:
        """Gate blocks when operator decision is absent."""
        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "blocked"
        assert result["gate_blocked"] is True
        assert result["fake_visual_acceptance_prevented"] is True
        assert result["agent_may_not_choose_verdict"] is True
        assert result["current_state"] == "preview_operator_review_required"

    def test_blocker_artifacts_created(self, tmp_episode: Path) -> None:
        """Blocker artifacts are created on disk."""
        control_dir = tmp_episode / "output" / "control"
        run_human_preview_review_gate(project_root=str(tmp_episode))

        assert (control_dir / "human_preview_review_gate_proof.json").exists()
        assert (control_dir / "human_preview_review_gate_blocker.json").exists()

    def test_blocker_content(self) -> None:
        """Verify blocker packet content."""
        blocker = build_blocker_packet()
        assert blocker["gate_blocked"] is True
        assert blocker["blocker_type"] == "missing_operator_decision"
        assert blocker["agent_may_not_choose_verdict"] is True
        assert blocker["agent_may_not_accept_preview"] is True
        assert blocker["current_state"] == "preview_operator_review_required"

    def test_index_not_updated_beyond_meta(self, tmp_episode: Path) -> None:
        """Artifact index remains in preview_operator_review_required when blocked."""
        control_dir = tmp_episode / "output" / "control"
        run_human_preview_review_gate(project_root=str(tmp_episode))

        index = json.loads(
            (control_dir / "artifact_index.json").read_text()
        )
        assert index["current_state"] == "preview_operator_review_required"


# ---------------------------------------------------------------------------
# 5. Gate Run — Accepted Branch Tests
# ---------------------------------------------------------------------------


class TestGateAccepted:
    def test_passes_with_accepted_verdict(self, tmp_episode: Path) -> None:
        """Gate passes for accepted_for_voice_stage."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["gate_passed"] is True
        assert result["selected_branch"] == "accepted_for_voice_stage"
        assert result["operator_verdict"] == "accepted_for_voice_stage"

    def test_transitions_to_voice_auth_state(self, tmp_episode: Path) -> None:
        """Target state is voice_generation_authorization_required."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["to_state"] == "voice_generation_authorization_required"
        assert result["current_state"] == "voice_generation_authorization_required"

    def test_creates_gate_proof(self, tmp_episode: Path) -> None:
        """Gate proof artifact is created."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        run_human_preview_review_gate(project_root=str(tmp_episode))

        proof_path = control_dir / "human_preview_review_gate_proof.json"
        assert proof_path.exists()
        proof = json.loads(proof_path.read_text())
        assert proof["task_id"] == TASK_ID
        assert proof["feature_completed"] is True
        assert proof["agent_did_not_choose_verdict"] is True
        assert proof["agent_did_not_accept_preview"] is True
        assert proof["agent_did_not_override"] is True
        assert proof["operator_decision_found"] is True
        assert proof["operator_decision_valid"] is True
        assert proof["blocked"] is False
        assert proof["voice_generation_executed"] is False
        assert proof["production_accepted"] is False

    def test_voice_generation_not_executed(self, tmp_episode: Path) -> None:
        """Voice generation is NOT executed when gate passes."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["voice_generation_executed"] is False
        assert result["assembly_executed"] is False
        assert result["downstream_executed"] is False
        assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# 6. Gate Run — Rejected Branch Tests
# ---------------------------------------------------------------------------


class TestGateRejected:
    def test_passes_with_rejected_verdict(self, tmp_episode: Path) -> None:
        """Gate passes for rejected verdict."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_rejected_decision(),
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["selected_branch"] == "rejected"
        assert result["current_state"] == "preview_correction_authorization_required"

    def test_proof_records_rejected_verdict(self, tmp_episode: Path) -> None:
        """Gate proof records the rejected verdict."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_rejected_decision(),
        )

        run_human_preview_review_gate(project_root=str(tmp_episode))
        proof = json.loads(
            (control_dir / "human_preview_review_gate_proof.json").read_text()
        )
        assert proof["operator_verdict"] == "rejected"
        assert proof["target_state"] == "preview_correction_authorization_required"


# ---------------------------------------------------------------------------
# 7. Gate Run — Needs Fix Branch Tests
# ---------------------------------------------------------------------------


class TestGateNeedsFix:
    def test_passes_with_needs_fix_verdict(self, tmp_episode: Path) -> None:
        """Gate passes for needs_fix verdict."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_needs_fix_decision(),
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["selected_branch"] == "needs_fix"
        assert result["current_state"] == "targeted_preview_fix_authorization_required"

    def test_proof_records_needs_fix_verdict(self, tmp_episode: Path) -> None:
        """Gate proof records the needs_fix verdict."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_needs_fix_decision(),
        )

        run_human_preview_review_gate(project_root=str(tmp_episode))
        proof = json.loads(
            (control_dir / "human_preview_review_gate_proof.json").read_text()
        )
        assert proof["operator_verdict"] == "needs_fix"
        assert proof["target_state"] == "targeted_preview_fix_authorization_required"


# ---------------------------------------------------------------------------
# 8. State Machine Integration Tests
# ---------------------------------------------------------------------------


class TestStateMachineIntegration:
    def test_transition_from_preview_operator_review_required_to_all_states(
        self,
    ) -> None:
        """All post-preview routing states are reachable from preview_operator_review_required."""
        from_state = "preview_operator_review_required"
        for target_state in [
            "voice_generation_authorization_required",
            "preview_correction_authorization_required",
            "targeted_preview_fix_authorization_required",
        ]:
            assert CombineStateMachine.can_transition(from_state, target_state), (
                f"State machine must allow {from_state} -> {target_state}"
            )

    def test_forbidden_transitions_are_blocked(self) -> None:
        """Post-preview routing states cannot skip to generation/assembly/downstream."""
        for state in [
            "voice_generation_authorization_required",
            "preview_correction_authorization_required",
            "targeted_preview_fix_authorization_required",
        ]:
            for forbidden_to in [
                "generate_assets",
                "assembly_required",
                "completed",
                "production_accepted",
                "final_qc_required",
                "final_operator_acceptance",
            ]:
                assert not CombineStateMachine.can_transition(state, forbidden_to), (
                    f"State machine must forbid {state} -> {forbidden_to}"
                )

    def test_new_states_can_go_to_blocked_manual_review(self) -> None:
        """All new states can fall back to blocked_manual_review."""
        for state in [
            "voice_generation_authorization_required",
            "preview_correction_authorization_required",
            "targeted_preview_fix_authorization_required",
        ]:
            assert CombineStateMachine.can_transition(
                state, "blocked_manual_review"
            ), f"{state} -> blocked_manual_review must be allowed"


# ---------------------------------------------------------------------------
# 9. Artifact Index and Ledger Tests
# ---------------------------------------------------------------------------


class TestIndexAndLedger:
    def test_artifact_index_updated_after_accepted(self, tmp_episode: Path) -> None:
        """Artifact index reflects new state after gate passes."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        run_human_preview_review_gate(project_root=str(tmp_episode))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "voice_generation_authorization_required"
        assert index["human_preview_review_gate_executed"] is True
        assert index["operator_verdict"] == "accepted_for_voice_stage"
        assert index["production_accepted"] is False

    def test_artifact_index_unchanged_when_blocked(self, tmp_episode: Path) -> None:
        """Artifact index stays in current state when blocked."""
        control_dir = tmp_episode / "output" / "control"
        run_human_preview_review_gate(project_root=str(tmp_episode))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index["current_state"] == "preview_operator_review_required"

    def test_episode_ledger_updated_for_accepted(self, tmp_episode: Path) -> None:
        """Episode ledger records the gate execution event."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        run_human_preview_review_gate(project_root=str(tmp_episode))

        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("task_id") == TASK_ID]
        assert len(events) >= 1
        event = events[-1]
        assert event["event_type"] == "human_preview_review_gate_executed"
        assert event["operator_verdict"] == "accepted_for_voice_stage"
        assert event["agent_did_not_choose_verdict"] is True
        assert event["production_accepted"] is False

    def test_episode_ledger_records_blocker(self, tmp_episode: Path) -> None:
        """Episode ledger records the blocker event."""
        control_dir = tmp_episode / "output" / "control"
        run_human_preview_review_gate(project_root=str(tmp_episode))

        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("task_id") == TASK_ID]
        assert len(events) >= 1
        event = events[-1]
        assert event["event_type"] == "human_preview_review_gate_blocked"
        assert event["fake_visual_acceptance_prevented"] is True
        assert event["agent_may_not_choose_verdict"] is True


# ---------------------------------------------------------------------------
# 10. Dry-Run Tests
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_does_not_write_artifacts(self, tmp_episode: Path) -> None:
        """Dry-run does not write artifacts to disk."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        result = run_human_preview_review_gate(
            project_root=str(tmp_episode), dry_run=True
        )
        assert result["dry_run"] is True

        # No artifacts written
        assert not (control_dir / "human_preview_review_gate_proof.json").exists()
        assert not (control_dir / "human_preview_review_gate_blocker.json").exists()

    def test_dry_run_reports_correct_branch(self, tmp_episode: Path) -> None:
        """Dry-run correctly reports the branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_rejected_decision(),
        )

        result = run_human_preview_review_gate(
            project_root=str(tmp_episode), dry_run=True
        )
        assert result["selected_branch"] == "rejected"
        assert result["to_state"] == "preview_correction_authorization_required"

    def test_dry_run_blocker_no_files_written(self, tmp_episode: Path) -> None:
        """Dry-run for missing decision does not write blocker files."""
        control_dir = tmp_episode / "output" / "control"
        result = run_human_preview_review_gate(
            project_root=str(tmp_episode), dry_run=True
        )
        assert result["status"] == "blocked"
        assert not (control_dir / "human_preview_review_gate_blocker.json").exists()
        assert not (control_dir / "human_preview_review_gate_proof.json").exists()

    def test_dry_run_index_not_updated(self, tmp_episode: Path) -> None:
        """Dry-run does not update artifact index."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            _make_accepted_decision(),
        )

        run_human_preview_review_gate(
            project_root=str(tmp_episode), dry_run=True
        )

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index.get("human_preview_review_gate_executed") is None


# ---------------------------------------------------------------------------
# 11. Invalid Decision Tests
# ---------------------------------------------------------------------------


class TestInvalidDecision:
    def test_rejects_invalid_decision_format(self, tmp_episode: Path) -> None:
        """Gate blocks on invalid decision JSON."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json",
            {"invalid": True},
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "blocked"
        assert result["gate_blocked"] is True

    def test_rejects_fabricated_verdict(self, tmp_episode: Path) -> None:
        """Gate blocks on a fabricated verdict."""
        control_dir = tmp_episode / "output" / "control"
        decision = _make_accepted_decision()
        decision["operator_verdict"] = "accepted_no_questions_asked"
        _write_json_file(
            control_dir / "preview_operator_decision_input.json", decision
        )

        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["status"] == "blocked"
        assert result["gate_blocked"] is True


# ---------------------------------------------------------------------------
# 12. Forbidden Actions Tests
# ---------------------------------------------------------------------------


class TestForbiddenActions:
    def test_forbidden_actions_false_across_all_branches(
        self, tmp_episode: Path
    ) -> None:
        """Forbidden actions are false for all branches."""
        control_dir = tmp_episode / "output" / "control"

        for decision_factory in [
            _make_accepted_decision,
            _make_rejected_decision,
            _make_needs_fix_decision,
        ]:
            _write_json_file(
                control_dir / "preview_operator_decision_input.json",
                decision_factory(),
            )
            result = run_human_preview_review_gate(project_root=str(tmp_episode))
            assert result["voice_generation_executed"] is False
            assert result["assembly_executed"] is False
            assert result["downstream_executed"] is False
            assert result["production_accepted"] is False
            for key in ["voice_generation", "assembly", "downstream",
                        "production_accepted"]:
                assert result["forbidden_actions"][key] is False, (
                    f"forbidden_actions.{key} must be False "
                    f"in {decision_factory.__name__}"
                )

            # Clean up generated artifacts
            _clean_control_dir(control_dir)


# ---------------------------------------------------------------------------
# 13. Production Accepted Tests
# ---------------------------------------------------------------------------


class TestProductionAccepted:
    def test_production_accepted_false_across_all_scenarios(
        self, tmp_episode: Path
    ) -> None:
        """production_accepted is false across all scenarios."""
        control_dir = tmp_episode / "output" / "control"

        # All verdicts + missing
        for decision_factory in [
            _make_accepted_decision,
            _make_rejected_decision,
            _make_needs_fix_decision,
        ]:
            _write_json_file(
                control_dir / "preview_operator_decision_input.json",
                decision_factory(),
            )
            result = run_human_preview_review_gate(project_root=str(tmp_episode))
            assert result["production_accepted"] is False
            _clean_control_dir(control_dir)

        # Missing decision
        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# 14. JSON Output Tests
# ---------------------------------------------------------------------------


class TestJsonOutput:
    def test_gate_result_is_json_serializable(self, tmp_episode: Path) -> None:
        """Gate result is JSON-serializable."""
        result = run_human_preview_review_gate(project_root=str(tmp_episode))
        json_str = json.dumps(result, indent=2)
        parsed = json.loads(json_str)
        assert parsed["task_id"] == TASK_ID
        assert parsed["status"] == "blocked"

    def test_gate_proof_is_json_serializable(self) -> None:
        """Gate proof artifact is JSON-serializable."""
        proof = build_gate_proof(
            verdict_found=True,
            verdict="accepted_for_voice_stage",
            decision_valid=True,
            target_state="voice_generation_authorization_required",
            transition_valid=True,
            blocked=False,
            blocker_reason=None,
            artifacts_created=["test.json"],
        )
        json_str = json.dumps(proof, indent=2)
        parsed = json.loads(json_str)
        assert parsed["task_id"] == TASK_ID
        assert parsed["agent_did_not_choose_verdict"] is True


# ---------------------------------------------------------------------------
# 15. Blocker Packet Tests
# ---------------------------------------------------------------------------


class TestBlockerPacket:
    def test_blocker_packet_has_required_fields(self) -> None:
        """Blocker packet has all required fields."""
        blocker = build_blocker_packet()
        assert blocker["gate_blocked"] is True
        assert blocker["blocker_type"] == "missing_operator_decision"
        assert blocker["agent_may_not_choose_verdict"] is True
        assert blocker["agent_may_not_accept_preview"] is True
        assert blocker["fake_visual_acceptance_prevented"] is True
        assert blocker["voice_generation_executed"] is False
        assert blocker["assembly_executed"] is False
        assert blocker["downstream_executed"] is False
        assert blocker["production_accepted"] is False
        assert blocker["current_state"] == "preview_operator_review_required"
        assert blocker["next_allowed_action"] == "preview_operator_review_required"

    def test_blocker_mentions_valid_verdicts(self) -> None:
        """Blocker mentions valid verdicts for resolution."""
        blocker = build_blocker_packet()
        for v in VALID_VERDICTS:
            assert v in blocker["resolution"], (
                f"Blocker resolution must mention '{v}'"
            )


# ---------------------------------------------------------------------------
# 16. Gate Proof Content Tests
# ---------------------------------------------------------------------------


class TestGateProof:
    def test_gate_proof_records_decision_true_state(self) -> None:
        """Gate proof correctly records when decision was found and valid."""
        proof = build_gate_proof(
            verdict_found=True,
            verdict="accepted_for_voice_stage",
            decision_valid=True,
            target_state="voice_generation_authorization_required",
            transition_valid=True,
            blocked=False,
            blocker_reason=None,
            artifacts_created=["human_preview_review_gate_proof.json"],
        )
        assert proof["operator_decision_found"] is True
        assert proof["operator_decision_valid"] is True
        assert proof["blocked"] is False
        assert proof["state_machine_transition_valid"] is True

    def test_gate_proof_records_blocked_state(self) -> None:
        """Gate proof correctly records when blocked."""
        proof = build_gate_proof(
            verdict_found=False,
            verdict=None,
            decision_valid=False,
            target_state="preview_operator_review_required",
            transition_valid=True,
            blocked=True,
            blocker_reason="No decision file found.",
            artifacts_created=["human_preview_review_gate_proof.json"],
        )
        assert proof["operator_decision_found"] is False
        assert proof["blocked"] is True
        assert proof["blocker_reason"] == "No decision file found."
        assert proof["target_state"] == "preview_operator_review_required"

    def test_gate_proof_freeze_agent_invariants(self) -> None:
        """Gate proof always records agent invariants."""
        for blocked in [True, False]:
            proof = build_gate_proof(
                verdict_found=not blocked,
                verdict="accepted_for_voice_stage" if not blocked else None,
                decision_valid=not blocked,
                target_state="voice_generation_authorization_required",
                transition_valid=True,
                blocked=blocked,
                blocker_reason="test" if blocked else None,
                artifacts_created=["test.json"],
            )
            assert proof["agent_did_not_choose_verdict"] is True
            assert proof["agent_did_not_accept_preview"] is True
            assert proof["agent_did_not_override"] is True
            assert proof["production_accepted"] is False
            assert proof["voice_generation_executed"] is False
            assert proof["assembly_executed"] is False
            assert proof["downstream_executed"] is False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clean_control_dir(control_dir: Path) -> None:
    """Remove generated artifacts but keep essential files."""
    keep = {
        "artifact_index.json",
        "episode_ledger.json",
        "preview_operator_decision_input.json",
    }
    for f in control_dir.iterdir():
        if f.suffix == ".json" and f.name not in keep:
            f.unlink()
