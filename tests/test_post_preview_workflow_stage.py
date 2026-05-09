"""RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001 — Post-Preview Workflow Stage Tests.

Covers: validation, operator decision ingestion, branch routing,
voice/audio readiness package, corrective plan, targeted fix,
blocker creation, state/ledger/index updates, dry-run, and CLI output.
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

from app.post_preview.post_preview_stage import (
    TASK_ID,
    VALID_VERDICTS,
    validate_post_preview_stage,
    validate_operator_decision,
    read_operator_decision,
    run_post_preview_stage,
    _build_voice_readiness_package,
    _build_voice_script_package,
    _build_voice_casting_review_package,
    _build_voice_audition_plan,
    _build_audio_qa_contract,
    _build_audio_timeline_sync_contract,
    _build_assembly_preflight_contract,
    _build_voice_generation_authorization_packet,
    _build_preview_operator_rejection_record,
    _build_preview_corrective_plan,
    _build_timeline_correction_plan,
    _build_editing_correction_plan,
    _build_subtitle_correction_plan,
    _build_transition_correction_plan,
    _build_preview_correction_authorization_packet,
    _build_preview_needs_fix_record,
    _build_targeted_preview_fix_plan,
    _build_targeted_timeline_fix_plan,
    _build_targeted_subtitle_fix_plan,
    _build_targeted_transition_fix_plan,
    _build_targeted_preview_fix_authorization_packet,
    _build_post_preview_stage_blocker,
    _build_operator_preview_review_required_packet,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_episode(tmp_path: Path) -> Path:
    """Create a minimal episode directory structure with all required artifacts."""
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)

    # Preview artifacts
    _write_json_file(preview_dir / "preview_lowres.mp4", b"fake mp4 content")
    _write_json_file(preview_dir / "preview.gif", b"fake gif content")
    _write_json_file(preview_dir / "contact_sheet.jpg", b"fake jpg content")

    # Control artifacts
    _write_json_file(control_dir / "preview_render_report.json", {"rendered": True})
    _write_json_file(control_dir / "preview_result_review.json", {"valid": True})
    _write_json_file(control_dir / "preview_operator_review_packet.json", {"review": True})

    # Editorial contracts
    _write_json_file(
        control_dir / "timeline_model.json",
        {
            "project_id": "test_ep01",
            "timeline_version": "mvp_v1",
            "fps": 24,
            "resolution": {"width": 1344, "height": 768},
            "scenes": [{"scene_id": "scene_001", "duration_sec": 30.0}],
        },
    )
    _write_json_file(control_dir / "marker_registry.json", {"markers": []})
    _write_json_file(
        control_dir / "edit_decision_list.json",
        {"edits": [{"edit_id": "edit_001", "type": "cut"}]},
    )
    _write_json_file(
        control_dir / "subtitle_plan.json",
        [
            {
                "subtitle_id": "sub_001",
                "text": "Test subtitle",
                "start_time": "00:00:02",
                "end_time": "00:00:06",
                "scene_id": "scene_001",
                "start_offset": 2.0,
                "duration": 4.0,
            },
            {
                "subtitle_id": "sub_002",
                "text": "Second subtitle",
                "start_time": "00:00:08",
                "end_time": "00:00:12",
                "scene_id": "scene_001",
                "start_offset": 8.0,
                "duration": 4.0,
            },
        ],
    )
    _write_json_file(
        control_dir / "transition_policy.json",
        {"transitions": [{"type": "cut", "duration_frames": 0}]},
    )
    _write_json_file(
        control_dir / "voice_casting_contract.json",
        {
            "language": "ru",
            "preferred_gender": "female",
            "age_range": "30-45",
            "tone": ["calm", "clear"],
            "pace": "medium",
            "full_voiceover_generation_allowed": False,
            "sample_required": True,
            "operator_review_required": True,
        },
    )

    # Artifact index and ledger
    _write_json_file(
        control_dir / "artifact_index.json",
        {"current_state": "preview_operator_review_required", "next_allowed_action": "preview_operator_review_required", "production_accepted": False},
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
# 1. Preview Stage Validator Tests
# ---------------------------------------------------------------------------


class TestValidatePostPreviewStage:
    def test_validates_complete_artifact_set(self, tmp_episode: Path) -> None:
        """1. validates complete preview artifact set."""
        result = validate_post_preview_stage(project_root=str(tmp_episode))
        assert result["valid"] is True, f"Expected valid, got errors: {result.get('errors')}"
        assert result["preview_lowres_mp4_exists"] is True
        assert result["preview_gif_exists"] is True
        assert result["contact_sheet_jpg_exists"] is True
        assert result["preview_render_report_json_exists"] is True
        assert result["preview_result_review_json_exists"] is True
        assert result["preview_operator_review_packet_json_exists"] is True
        assert result["timeline_model_json_exists"] is True
        assert result["marker_registry_json_exists"] is True
        assert result["edit_decision_list_json_exists"] is True
        assert result["subtitle_plan_json_exists"] is True
        assert result["transition_policy_json_exists"] is True
        assert result["voice_casting_contract_json_exists"] is True
        assert result["task_id"] == TASK_ID

    def test_blocks_missing_preview_lowres(self, tmp_episode: Path) -> None:
        """2. blocks missing preview_lowres.mp4."""
        os.remove(str(tmp_episode / "output" / "preview" / "preview_lowres.mp4"))
        result = validate_post_preview_stage(project_root=str(tmp_episode))
        assert result["valid"] is False
        assert result["preview_lowres_mp4_exists"] is False
        assert any("preview_lowres.mp4" in e for e in result["errors"])

    def test_blocks_missing_preview_gif(self, tmp_episode: Path) -> None:
        """3. blocks missing preview.gif."""
        os.remove(str(tmp_episode / "output" / "preview" / "preview.gif"))
        result = validate_post_preview_stage(project_root=str(tmp_episode))
        assert result["valid"] is False
        assert result["preview_gif_exists"] is False

    def test_blocks_missing_contact_sheet(self, tmp_episode: Path) -> None:
        """4. blocks missing contact_sheet.jpg."""
        os.remove(str(tmp_episode / "output" / "preview" / "contact_sheet.jpg"))
        result = validate_post_preview_stage(project_root=str(tmp_episode))
        assert result["valid"] is False
        assert result["contact_sheet_jpg_exists"] is False


# ---------------------------------------------------------------------------
# 2. Operator Decision Validation Tests
# ---------------------------------------------------------------------------


class TestValidateOperatorDecision:
    def test_rejects_missing_required_fields(self) -> None:
        valid, msg = validate_operator_decision({})
        assert valid is False
        assert "Missing required fields" in msg

    def test_rejects_production_accepted_true(self) -> None:
        decision = _make_accepted_decision()
        decision["production_accepted"] = True
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "production_accepted" in msg

    def test_rejects_visual_review_not_performed(self) -> None:
        decision = _make_accepted_decision()
        decision["visual_review_performed_by_operator"] = False
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "visual_review_performed_by_operator" in msg

    def test_rejects_unknown_verdict(self) -> None:
        decision = _make_accepted_decision()
        decision["operator_verdict"] = "invalid_verdict"
        valid, msg = validate_operator_decision(decision)
        assert valid is False
        assert "Unknown operator_verdict" in msg

    def test_accepts_valid_accepted_decision(self) -> None:
        valid, msg = validate_operator_decision(_make_accepted_decision())
        assert valid is True

    def test_accepts_valid_rejected_decision(self) -> None:
        valid, msg = validate_operator_decision(_make_rejected_decision())
        assert valid is True

    def test_accepts_valid_needs_fix_decision(self) -> None:
        valid, msg = validate_operator_decision(_make_needs_fix_decision())
        assert valid is True


# ---------------------------------------------------------------------------
# 3. Operator Decision Ingestion Tests
# ---------------------------------------------------------------------------


class TestReadOperatorDecision:
    def test_blocks_missing_decision(self, tmp_episode: Path) -> None:
        """5. blocks missing operator decision."""
        control_dir = tmp_episode / "output" / "control"
        found, _, msg = read_operator_decision(control_dir)
        assert found is False
        assert "not found" in msg

    def test_rejects_fake_production_accepted(self, tmp_episode: Path) -> None:
        """6. rejects fake production_accepted=true."""
        control_dir = tmp_episode / "output" / "control"
        decision = _make_accepted_decision()
        decision["production_accepted"] = True
        _write_json_file(control_dir / "preview_operator_decision_input.json", decision)

        found, data, msg = read_operator_decision(control_dir)
        # The file was found, but the decision is invalid
        assert found is False
        assert "production_accepted" in msg


# ---------------------------------------------------------------------------
# 4. Branch A — Accepted Preview Tests
# ---------------------------------------------------------------------------


class TestBranchAccepted:
    def test_accepts_accepted_for_voice_stage(self, tmp_episode: Path) -> None:
        """7. accepts accepted_for_voice_stage branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["selected_branch"] == "accepted_for_voice_stage"
        assert result["operator_verdict"] == "accepted_for_voice_stage"

    def test_creates_full_voice_readiness_package(self, tmp_episode: Path) -> None:
        """8. creates full voice/audio readiness package."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        # Check all expected voice readiness artifacts
        assert (control_dir / "voice_generation_readiness_package.json").exists()
        assert (control_dir / "voice_script_package.json").exists()
        assert (control_dir / "voice_casting_review_package.json").exists()
        assert (control_dir / "voice_audition_plan.json").exists()
        assert (control_dir / "audio_qa_contract.json").exists()
        assert (control_dir / "audio_timeline_sync_contract.json").exists()
        assert (control_dir / "assembly_preflight_contract.json").exists()
        assert (control_dir / "voice_generation_authorization_packet.json").exists()

        # Verify voice readiness package content
        readiness = json.loads(
            (control_dir / "voice_generation_readiness_package.json").read_text()
        )
        assert readiness["voice_generation_ready"] is True
        assert readiness["voice_generation_executed"] is False
        assert readiness["assembly_allowed"] is False
        assert readiness["downstream_allowed"] is False
        assert readiness["production_accepted"] is False

        # Verify voice script package
        script_pkg = json.loads(
            (control_dir / "voice_script_package.json").read_text()
        )
        assert script_pkg["total_segments"] == 2
        assert script_pkg["voice_generation_executed"] is False

    def test_creates_voice_auth_packet_no_voice_generation(self, tmp_episode: Path) -> None:
        """9. creates voice authorization packet but does not execute voice generation."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))

        assert result["voice_generation_executed"] is False

        auth_packet = json.loads(
            (control_dir / "voice_generation_authorization_packet.json").read_text()
        )
        assert auth_packet["voice_generation_authorized"] is False
        assert auth_packet["voice_generation_executed"] is False
        assert auth_packet["current_state"] == "voice_generation_authorization_required"

    def test_creates_assembly_preflight_no_assembly(self, tmp_episode: Path) -> None:
        """10. creates assembly preflight contract but does not execute assembly."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))

        assert result["assembly_allowed"] is False

        preflight = json.loads(
            (control_dir / "assembly_preflight_contract.json").read_text()
        )
        assert preflight["assembly_allowed"] is False
        assert preflight["final_render_allowed"] is False

    def test_voice_readiness_package_content(self, tmp_episode: Path) -> None:
        """Verify detailed voice readiness package fields."""
        control_dir = tmp_episode / "output" / "control"
        package = _build_voice_readiness_package(control_dir)
        assert package["language"] == "ru"
        assert package["script_source"] == "subtitle_plan"
        assert package["voice_generation_ready"] is True
        assert package["voice_generation_executed"] is False
        assert package["sample_generation_required_before_full_voiceover"] is True
        assert package["operator_voice_review_required"] is True
        assert package["audio_qa_required"] is True

    def test_voice_casting_review_content(self, tmp_episode: Path) -> None:
        """Verify voice casting review package."""
        control_dir = tmp_episode / "output" / "control"
        package = _build_voice_casting_review_package(control_dir)
        assert package["language"] == "ru"
        assert package["preferred_gender"] == "female"
        assert package["operator_voice_review_required"] is True

    def test_audio_qa_contract_content(self) -> None:
        """Verify audio QA contract fields."""
        package = _build_audio_qa_contract(control_dir=None)  # type: ignore[arg-type]
        assert package["audio_qa_required"] is True
        assert "silence_detection" in package["qa_checks"]
        assert package["operator_review_required"] is True
        assert package["voice_generation_executed"] is False

    def test_audio_timeline_sync_contract_content(self, tmp_episode: Path) -> None:
        """Verify audio timeline sync contract."""
        control_dir = tmp_episode / "output" / "control"
        package = _build_audio_timeline_sync_contract(control_dir)
        assert package["sync_required"] is True
        assert package["drift_tolerance_frames"] == 2
        assert package["subtitle_count"] == 2

    def test_assembly_preflight_content(self, tmp_episode: Path) -> None:
        """Verify assembly preflight contract."""
        control_dir = tmp_episode / "output" / "control"
        package = _build_assembly_preflight_contract(control_dir)
        assert package["assembly_allowed"] is False
        assert package["preconditions"]["voice_script_ready"] is True
        assert package["preconditions"]["voice_casting_approved"] is False


# ---------------------------------------------------------------------------
# 5. Branch B — Rejected Tests
# ---------------------------------------------------------------------------


class TestBranchRejected:
    def test_handles_rejected_branch(self, tmp_episode: Path) -> None:
        """11. handles rejected branch and creates corrective plan package."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["selected_branch"] == "rejected"
        assert result["corrective_plan_created"] is True

        # Verify corrective plan artifacts
        assert (control_dir / "preview_operator_rejection_record.json").exists()
        assert (control_dir / "preview_corrective_plan.json").exists()
        assert (control_dir / "timeline_correction_plan.json").exists()
        assert (control_dir / "editing_correction_plan.json").exists()
        assert (control_dir / "subtitle_correction_plan.json").exists()
        assert (control_dir / "transition_correction_plan.json").exists()
        assert (control_dir / "preview_correction_authorization_packet.json").exists()

    def test_rejection_record_content(self) -> None:
        """Verify rejection record fields."""
        decision = _make_rejected_decision()
        record = _build_preview_operator_rejection_record(decision)
        assert record["operator_verdict"] == "rejected"
        assert record["preview_rejected"] is True
        assert record["production_accepted"] is False
        assert record["agent_may_not_override"] is True
        assert record["operator_notes"] == "Major pacing issues, needs re-edit."

    def test_corrective_plan_content(self) -> None:
        """Verify corrective plan fields."""
        decision = _make_rejected_decision()
        plan = _build_preview_corrective_plan(decision)
        assert plan["preview_rejected"] is True
        assert plan["operator_notes_captured"] is True
        assert plan["preview_rerender_required"] is True
        assert plan["preview_rerender_authorized"] is False
        assert plan["assembly_allowed"] is False

    def test_correction_authorization_packet(self) -> None:
        """Verify correction authorization packet."""
        packet = _build_preview_correction_authorization_packet()
        assert packet["correction_authorized"] is False
        assert packet["preview_rerender_authorized"] is False
        assert packet["current_state"] == "preview_correction_authorization_required"
        assert packet["assembly_allowed"] is False


# ---------------------------------------------------------------------------
# 6. Branch C — Needs Fix Tests
# ---------------------------------------------------------------------------


class TestBranchNeedsFix:
    def test_handles_needs_fix_branch(self, tmp_episode: Path) -> None:
        """12. handles needs_fix branch and creates targeted fix package."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_needs_fix_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["status"] == "ok"
        assert result["selected_branch"] == "needs_fix"
        assert result["targeted_fix_plan_created"] is True

        # Verify targeted fix artifacts
        assert (control_dir / "preview_needs_fix_record.json").exists()
        assert (control_dir / "targeted_preview_fix_plan.json").exists()
        assert (control_dir / "targeted_timeline_fix_plan.json").exists()
        assert (control_dir / "targeted_subtitle_fix_plan.json").exists()
        assert (control_dir / "targeted_transition_fix_plan.json").exists()
        assert (control_dir / "targeted_preview_fix_authorization_packet.json").exists()

    def test_needs_fix_record_content(self) -> None:
        """Verify needs-fix record fields."""
        decision = _make_needs_fix_decision()
        record = _build_preview_needs_fix_record(decision)
        assert record["operator_verdict"] == "needs_fix"
        assert record["preview_needs_fix"] is True
        assert record["preview_accepted"] is False

    def test_targeted_fix_plan_content(self) -> None:
        """Verify targeted fix plan fields."""
        decision = _make_needs_fix_decision()
        plan = _build_targeted_preview_fix_plan(decision)
        assert plan["preview_needs_fix"] is True
        assert plan["operator_notes_captured"] is True
        assert plan["preview_rerender_authorized"] is False

    def test_targeted_fix_authorization_packet(self) -> None:
        """Verify targeted fix authorization packet."""
        packet = _build_targeted_preview_fix_authorization_packet()
        assert packet["fix_authorized"] is False
        assert packet["preview_rerender_authorized"] is False
        assert packet["current_state"] == "targeted_preview_fix_authorization_required"


# ---------------------------------------------------------------------------
# 7. Branch D — Missing Decision Tests
# ---------------------------------------------------------------------------


class TestBranchMissingDecision:
    def test_blocks_missing_operator_decision(self, tmp_episode: Path) -> None:
        """5 (double-coverage): blocks when operator decision is absent."""
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["status"] == "accepted_with_blockers"
        assert result["selected_branch"] == "blocked_missing_operator_decision"
        assert result["fake_visual_acceptance_prevented"] is True
        assert result["state_remains_preview_operator_review_required"] is True
        assert result["current_state"] == "preview_operator_review_required"

    def test_blocker_created(self, tmp_episode: Path) -> None:
        """Verify blocker artifacts are created."""
        control_dir = tmp_episode / "output" / "control"
        run_post_preview_stage(project_root=str(tmp_episode))
        assert (control_dir / "post_preview_stage_blocker.json").exists()
        assert (control_dir / "operator_preview_review_required_packet.json").exists()

    def test_blocker_content(self) -> None:
        """Verify blocker content."""
        blocker = _build_post_preview_stage_blocker()
        assert blocker["stage_blocked"] is True
        assert blocker["blocker_type"] == "missing_operator_decision"
        assert blocker["fake_visual_acceptance_prevented"] is True
        assert blocker["agent_may_not_choose_verdict"] is True
        assert blocker["current_state"] == "preview_operator_review_required"

    def test_review_required_packet_content(self) -> None:
        """Verify operator review required packet."""
        packet = _build_operator_preview_review_required_packet()
        assert packet["operator_preview_review_required"] is True
        assert packet["agent_may_not_accept_preview"] is True
        assert packet["production_accepted"] is False
        assert "accepted_for_voice_stage" in packet["allowed_verdicts"]


# ---------------------------------------------------------------------------
# 8. State Transition Tests
# ---------------------------------------------------------------------------


class TestStateTransitions:
    def test_accepted_state_transition(self, tmp_episode: Path) -> None:
        """13a. validates state transition for accepted branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["current_state"] == "voice_generation_authorization_required"
        assert result["next_allowed_action"] == "voice_generation_authorization_required"

    def test_rejected_state_transition(self, tmp_episode: Path) -> None:
        """13b. validates state transition for rejected branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["current_state"] == "preview_correction_authorization_required"
        assert result["next_allowed_action"] == "preview_correction_authorization_required"

    def test_needs_fix_state_transition(self, tmp_episode: Path) -> None:
        """13c. validates state transition for needs_fix branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_needs_fix_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["current_state"] == "targeted_preview_fix_authorization_required"
        assert result["next_allowed_action"] == "targeted_preview_fix_authorization_required"

    def test_missing_decision_state_remains(self, tmp_episode: Path) -> None:
        """13d. state remains preview_operator_review_required when decision missing."""
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["current_state"] == "preview_operator_review_required"


# ---------------------------------------------------------------------------
# 9. Artifact Index and Ledger Tests
# ---------------------------------------------------------------------------


class TestIndexAndLedger:
    def test_artifact_index_updated(self, tmp_episode: Path) -> None:
        """14. updates artifact_index."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index.get("current_state") == "voice_generation_authorization_required"
        assert index.get("post_preview_stage_executed") is True
        assert index.get("selected_branch") == "accepted_for_voice_stage"
        assert index.get("production_accepted") is False

    def test_artifact_index_blocker_no_mutation(self, tmp_episode: Path) -> None:
        """artifact index state unchanged when blocked."""
        control_dir = tmp_episode / "output" / "control"
        run_post_preview_stage(project_root=str(tmp_episode))

        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index.get("current_state") == "preview_operator_review_required"

    def test_episode_ledger_updated(self, tmp_episode: Path) -> None:
        """15. updates episode_ledger."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("task_id") == TASK_ID]
        assert len(events) >= 1
        last_event = events[-1]
        assert last_event["event_type"] == "preview_rejection_recorded"
        assert last_event["production_accepted"] is False

    def test_episode_ledger_accepted(self, tmp_episode: Path) -> None:
        """ledger for accepted branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        ledger = json.loads((control_dir / "episode_ledger.json").read_text())
        events = [e for e in ledger if e.get("event_type") == "voice_readiness_package_created"]
        assert len(events) == 1
        assert events[0]["voice_generation_executed"] is False


# ---------------------------------------------------------------------------
# 10. Dry-Run Tests
# ---------------------------------------------------------------------------


class TestDryRun:
    def test_dry_run_does_not_mutate_state(self, tmp_episode: Path) -> None:
        """16. dry-run does not mutate state."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        # Run dry-run
        result = run_post_preview_stage(project_root=str(tmp_episode), dry_run=True)
        assert result["dry_run"] is True

        # No artifacts should have been written
        assert (control_dir / "voice_generation_readiness_package.json").exists() is False
        assert (control_dir / "voice_script_package.json").exists() is False
        assert (control_dir / "post_preview_routing_decision.json").exists() is False

        # The index should NOT have been updated
        index = json.loads((control_dir / "artifact_index.json").read_text())
        assert index.get("current_state") == "preview_operator_review_required"
        assert index.get("post_preview_stage_executed") is None or index.get("post_preview_stage_executed") is False

    def test_dry_run_returns_expected_branch(self, tmp_episode: Path) -> None:
        """dry-run correctly reports the branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode), dry_run=True)
        assert result["selected_branch"] == "accepted_for_voice_stage"

    def test_dry_run_blocker_no_files_written(self, tmp_episode: Path) -> None:
        """dry-run for missing decision does not write blocker files."""
        control_dir = tmp_episode / "output" / "control"
        result = run_post_preview_stage(project_root=str(tmp_episode), dry_run=True)
        assert result["selected_branch"] == "blocked_missing_operator_decision"
        # Dry-run with missing decision still writes nothing (dry_run check at top)
        assert (control_dir / "post_preview_stage_blocker.json").exists() is False


# ---------------------------------------------------------------------------
# 11. Forbidden Actions Tests
# ---------------------------------------------------------------------------


class TestForbiddenActions:
    def test_forbidden_actions_remain_false(self, tmp_episode: Path) -> None:
        """17. forbidden actions remain false."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))

        for action_key in [
            "new_generation",
            "retry",
            "comfyui_submit",
            "preview_rerender",
            "voice_generation",
            "voice_api_submit",
            "assembly",
            "final_render",
            "downstream",
            "production_accepted",
        ]:
            assert result["forbidden_actions"][action_key] is False, (
                f"Forbidden action '{action_key}' must be False"
            )

    def test_all_branches_have_forbidden_actions_false(self, tmp_episode: Path) -> None:
        """Check forbidden actions for all branches."""
        control_dir = tmp_episode / "output" / "control"

        for decision_factory in [_make_accepted_decision, _make_rejected_decision, _make_needs_fix_decision]:
            _write_json_file(control_dir / "preview_operator_decision_input.json", decision_factory())
            result = run_post_preview_stage(project_root=str(tmp_episode))
            for key in ["voice_generation", "assembly", "downstream", "production_accepted"]:
                # Check both top-level and forbidden_actions
                top_level = result.get(key, result.get(key.replace("_", "_"), None))
                if top_level is not None:
                    assert top_level is False, f"{key} must be False in {decision_factory.__name__}"
                assert result["forbidden_actions"][key] is False, (
                    f"forbidden_actions.{key} must be False in {decision_factory.__name__}"
                )
            # Clean up for next iteration
            for f in control_dir.iterdir():
                if f.suffix == ".json" and f.name not in ("artifact_index.json", "episode_ledger.json", "preview_operator_decision_input.json"):
                    f.unlink()


# ---------------------------------------------------------------------------
# 12. Production Accepted Tests
# ---------------------------------------------------------------------------


class TestProductionAccepted:
    def test_production_accepted_false_across_all_branches(self, tmp_episode: Path) -> None:
        """production_accepted is false across all branches."""
        control_dir = tmp_episode / "output" / "control"

        # Accepted branch
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["production_accepted"] is False
        _clean_control_dir(control_dir)

        # Rejected branch
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["production_accepted"] is False
        _clean_control_dir(control_dir)

        # Needs fix branch
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_needs_fix_decision())
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["production_accepted"] is False
        _clean_control_dir(control_dir)

        # Missing decision branch
        result = run_post_preview_stage(project_root=str(tmp_episode))
        assert result["production_accepted"] is False


# ---------------------------------------------------------------------------
# 13. CLI JSON Output Tests
# ---------------------------------------------------------------------------


class TestCLIJsonOutput:
    def test_validator_returns_valid_json(self, tmp_episode: Path) -> None:
        """18a. CLI validation JSON output is valid."""
        result = validate_post_preview_stage(project_root=str(tmp_episode))
        # Must be JSON-serializable
        json_str = json.dumps(result, indent=2)
        parsed = json.loads(json_str)
        assert parsed["task_id"] == TASK_ID
        assert "valid" in parsed
        assert "errors" in parsed

    def test_decision_reader_returns_valid_json(self, tmp_episode: Path) -> None:
        """18b. CLI decision reading JSON output is valid."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        found, decision, msg = read_operator_decision(control_dir)
        output = {"decision_found": found, "decision": decision, "message": msg}
        json_str = json.dumps(output, indent=2, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["decision_found"] is True
        assert parsed["decision"]["operator_verdict"] == "accepted_for_voice_stage"

    def test_stage_builder_returns_valid_json(self, tmp_episode: Path) -> None:
        """18c. CLI stage build JSON output is valid."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        result = run_post_preview_stage(project_root=str(tmp_episode))
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        parsed = json.loads(json_str)
        assert parsed["task_id"] == TASK_ID
        assert parsed["status"] == "ok"
        assert parsed["selected_branch"] == "accepted_for_voice_stage"


# ---------------------------------------------------------------------------
# 14. Proof Contract Tests
# ---------------------------------------------------------------------------


class TestProofContract:
    def test_post_preview_stage_proof_created(self, tmp_episode: Path) -> None:
        """post_preview_stage_proof.json is created for every branch with decision."""
        control_dir = tmp_episode / "output" / "control"

        for decision_factory in [_make_accepted_decision, _make_rejected_decision, _make_needs_fix_decision]:
            _write_json_file(control_dir / "preview_operator_decision_input.json", decision_factory())
            run_post_preview_stage(project_root=str(tmp_episode))
            proof_path = control_dir / "post_preview_stage_proof.json"
            assert proof_path.exists(), f"Proof not created for {decision_factory.__name__}"
            proof = json.loads(proof_path.read_text())
            assert proof["task_id"] == TASK_ID
            assert proof["feature_completed"] is True
            assert proof["new_generation_performed"] is False
            assert proof["voice_generation_executed"] is False
            assert proof["production_accepted"] is False
            _clean_control_dir(control_dir)


# ---------------------------------------------------------------------------
# 15. Artifact Boundary Tests
# ---------------------------------------------------------------------------


class TestArtifactBoundaries:
    def test_voice_artifacts_not_created_for_rejected(self, tmp_episode: Path) -> None:
        """Voice readiness artifacts must NOT be created for rejected branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        assert not (control_dir / "voice_generation_readiness_package.json").exists()
        assert not (control_dir / "voice_script_package.json").exists()
        assert not (control_dir / "voice_generation_authorization_packet.json").exists()

    def test_corrective_artifacts_not_created_for_accepted(self, tmp_episode: Path) -> None:
        """Corrective plan artifacts must NOT be created for accepted branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_accepted_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        assert not (control_dir / "preview_operator_rejection_record.json").exists()
        assert not (control_dir / "preview_corrective_plan.json").exists()
        assert not (control_dir / "preview_needs_fix_record.json").exists()
        assert not (control_dir / "targeted_preview_fix_plan.json").exists()

    def test_needs_fix_artifacts_not_created_for_rejected(self, tmp_episode: Path) -> None:
        """Needs-fix artifacts must NOT be created for rejected branch."""
        control_dir = tmp_episode / "output" / "control"
        _write_json_file(control_dir / "preview_operator_decision_input.json", _make_rejected_decision())

        run_post_preview_stage(project_root=str(tmp_episode))

        assert not (control_dir / "preview_needs_fix_record.json").exists()
        assert not (control_dir / "targeted_preview_fix_plan.json").exists()


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
