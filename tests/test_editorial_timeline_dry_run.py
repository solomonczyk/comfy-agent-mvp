"""Tests for editorial timeline dry-run validator."""
import pytest
from app.editorial.timeline_dry_run import TimelineDryRun, DryRunReport
from app.editorial.timeline_model import TimelineModel
from app.editorial.transition_policy import TransitionPolicy


def _make_valid_timeline_dict():
    model = TimelineModel(project_id="test_dryrun")
    return model.to_dict()


def _make_valid_markers():
    return []


def _make_valid_subtitles():
    return []


def _make_valid_transition_policy():
    return TransitionPolicy.default_policy().to_dict()


def _make_valid_voice_casting():
    from app.editorial.voice_casting_policy import VoiceCastingContract
    return VoiceCastingContract().to_dict()


def _make_valid_preview_contract():
    from app.editorial.preview_contract import PreviewProofContract
    return PreviewProofContract().to_dict()


class TestDryRunPassesValidContract:
    def test_valid_contract_passes(self):
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=_make_valid_timeline_dict(),
            markers=_make_valid_markers(),
            subtitles=_make_valid_subtitles(),
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "ready_for_operator_review"
        assert report.errors == []
        assert report.apply_performed is False
        assert report.real_render_executed is False
        assert report.final_render_allowed is False
        assert report.operator_review_required is True

    def test_dry_run_report_to_dict(self):
        report = DryRunReport(dry_run_status="ready_for_operator_review")
        data = report.to_dict()
        assert data["dry_run_status"] == "ready_for_operator_review"
        assert data["errors"] == []


class TestDryRunBlocksInvalidContract:
    def test_final_render_allowed_blocked(self):
        timeline = _make_valid_timeline_dict()
        timeline["final_render_allowed"] = True
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=timeline,
            markers=[],
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("final_render_allowed" in e for e in report.errors)

    def test_missing_tracks_blocked(self):
        timeline = _make_valid_timeline_dict()
        timeline["tracks"] = {}
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=timeline,
            markers=[],
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("missing track" in e for e in report.errors)

    def test_empty_timeline_blocked(self):
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict={},
            markers=[],
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"

    def test_forbidden_transition_blocked(self):
        tp = _make_valid_transition_policy()
        tp["default"] = "random_wipe"
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=_make_valid_timeline_dict(),
            markers=[],
            subtitles=[],
            transition_policy=tp,
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("forbidden" in e for e in report.errors)

    def test_voiceover_generation_allowed_blocked(self):
        vc = _make_valid_voice_casting()
        vc["full_voiceover_generation_allowed"] = True
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=_make_valid_timeline_dict(),
            markers=[],
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=vc,
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("voiceover generation" in e for e in report.errors)

    def test_empty_subtitle_text_blocked(self):
        subs = [{"subtitle_id": "s1", "text": "", "anchor_type": "timecode"}]
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=_make_valid_timeline_dict(),
            markers=[],
            subtitles=subs,
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("empty text" in e for e in report.errors)

    def test_duplicate_markers(self):
        markers = [
            {"marker_id": "dup", "scene_id": "", "anchor_type": "scene_id"},
            {"marker_id": "dup", "scene_id": "", "anchor_type": "scene_id"},
        ]
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=_make_valid_timeline_dict(),
            markers=markers,
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("duplicate marker_id" in e for e in report.errors)

    def test_operator_review_required(self):
        timeline = _make_valid_timeline_dict()
        timeline["operator_review_required"] = False
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict=timeline,
            markers=[],
            subtitles=[],
            transition_policy=_make_valid_transition_policy(),
            voice_casting_contract=_make_valid_voice_casting(),
            preview_proof_contract=_make_valid_preview_contract(),
        )
        assert report.dry_run_status == "blocked"
        assert any("operator_review_required must be True" in e for e in report.errors)
