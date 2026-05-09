"""Tests for RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001 — Timeline Preview Dry-Run.

Covers dry-run validation of all editorial artifacts:
  - timeline validity
  - asset existence
  - markers valid
  - subtitles no conflict
  - transitions allowed
  - preview render not executed
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.editorial.timeline_dry_run import TimelineDryRun
from app.editorial.timeline_model import TimelineModel
from app.editorial.marker_registry import MarkerRegistry
from app.editorial.edit_decision_planner import EditDecisionPlanner
from app.editorial.subtitle_planner import SubtitlePlanner
from app.editorial.transition_policy import TransitionPolicy
from app.editorial.voice_casting_policy import VoiceCastingContract
from app.editorial.preview_contract import PreviewProofContract

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = PROJECT_ROOT / "data" / "rc2_multishot1_ep01"
CONTROL_DIR = DATA_ROOT / "output" / "control"


def _load_json(rel_path: str):
    path = CONTROL_DIR / rel_path
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestDryRunFromArtifacts:
    """Run dry-run validation against the actual on-disk artifacts."""

    @pytest.fixture(scope="class")
    def dry_run_report(self):
        timeline_dict = _load_json("timeline_model.json")
        markers = _load_json("marker_registry.json") or []
        subtitles = _load_json("subtitle_plan.json") or []
        transition_policy = _load_json("transition_policy.json") or {}
        voice_casting = _load_json("voice_casting_contract.json") or {}
        preview_contract = _load_json("preview_proof_contract.json") or {}

        assert timeline_dict is not None, "timeline_model.json not found"
        assert markers, "marker_registry.json not found"
        assert subtitles, "subtitle_plan.json not found"

        dry_run = TimelineDryRun()
        return dry_run.run(
            timeline_dict=timeline_dict,
            markers=markers if isinstance(markers, list) else [],
            subtitles=subtitles if isinstance(subtitles, list) else [],
            transition_policy=transition_policy if isinstance(transition_policy, dict) else {},
            voice_casting_contract=voice_casting if isinstance(voice_casting, dict) else {},
            preview_proof_contract=preview_contract if isinstance(preview_contract, dict) else {},
        )

    def test_dry_run_passes(self, dry_run_report):
        assert dry_run_report.dry_run_status != "blocked", \
            f"dry run blocked: {dry_run_report.errors}"

    def test_dry_run_no_errors(self, dry_run_report):
        assert len(dry_run_report.errors) == 0, \
            f"dry run errors: {dry_run_report.errors}"

    def test_dry_run_apply_not_performed(self, dry_run_report):
        assert dry_run_report.apply_performed is False

    def test_dry_run_render_not_executed(self, dry_run_report):
        assert dry_run_report.real_render_executed is False

    def test_dry_run_operator_review_required(self, dry_run_report):
        assert dry_run_report.operator_review_required is True


class TestDryRunTimelineValidity:
    """timeline valid"""

    def test_timeline_model_valid(self):
        tm = _load_json("timeline_model.json")
        assert tm is not None, "timeline_model.json not found"
        assert tm.get("fps", 0) > 0, "FPS must be positive"
        assert len(tm.get("scenes", [])) > 0, "scenes required"
        for scene in tm["scenes"]:
            assert scene.get("duration_sec", -1) >= 0, \
                f"scene {scene.get('scene_id')} duration negative"

    def test_timeline_tracks_valid(self):
        tm = _load_json("timeline_model.json")
        tracks = tm.get("tracks", {})
        required = ["video_main", "video_overlay", "audio_voice", "audio_music", "subtitles", "effects"]
        for r in required:
            assert r in tracks, f"missing track '{r}'"

    def test_timeline_no_duplicate_scenes(self):
        tm = _load_json("timeline_model.json")
        scene_ids = [s.get("scene_id") for s in tm.get("scenes", [])]
        assert len(scene_ids) == len(set(scene_ids)), "duplicate scene_ids"

    def test_timeline_operations_not_applied(self):
        tm = _load_json("timeline_model.json")
        for op in tm.get("operations", []):
            assert op.get("apply_performed") is False, \
                f"operation '{op.get('operation_id')}' applied"


class TestAssetExists:
    """asset exists (check manifest reference)"""

    def test_approved_asset_manifest_exists(self):
        manifest = _load_json("approved_visual_assets_manifest.json")
        assert manifest is not None, "approved_visual_assets_manifest.json not found"

    def test_approved_asset_path_referenced(self):
        manifest = _load_json("approved_visual_assets_manifest.json")
        assets = manifest.get("approved_assets", [])
        assert len(assets) > 0, "no approved assets"
        path = assets[0].get("path", "")
        assert path, "asset path is empty"

    def test_approved_asset_sha256_present(self):
        manifest = _load_json("approved_visual_assets_manifest.json")
        assets = manifest.get("approved_assets", [])
        assert assets[0].get("sha256", ""), "sha256 missing"

    def test_timeline_references_approved_asset(self):
        manifest = _load_json("approved_visual_assets_manifest.json")
        asset_path = manifest["approved_assets"][0].get("path", "")
        tm = _load_json("timeline_model.json")
        refs_found = False
        for scene in tm.get("scenes", []):
            for ref in scene.get("asset_refs", []):
                if asset_path in ref:
                    refs_found = True
        assert refs_found, "approved asset not referenced in timeline model"


class TestMarkersValid:
    """markers valid"""

    def test_markers_have_valid_anchors(self):
        markers = _load_json("marker_registry.json") or []
        valid_anchors = {"scene_id", "shot_id", "timecode", "transcript_phrase", "frame_number"}
        for m in markers:
            assert m.get("anchor_type", "") in valid_anchors, \
                f"marker '{m.get('marker_id')}' invalid anchor"

    def test_markers_reference_known_scenes(self):
        tm = _load_json("timeline_model.json")
        known_scenes = {s.get("scene_id") for s in tm.get("scenes", [])}
        markers = _load_json("marker_registry.json") or []
        for m in markers:
            sid = m.get("scene_id", "")
            assert sid in known_scenes, \
                f"marker '{m.get('marker_id')}' references unknown scene '{sid}'"

    def test_markers_no_duplicates(self):
        markers = _load_json("marker_registry.json") or []
        ids = [m.get("marker_id") for m in markers]
        assert len(ids) == len(set(ids)), "duplicate marker_ids"

    def test_markers_have_timecode_or_anchor(self):
        markers = _load_json("marker_registry.json") or []
        for m in markers:
            assert m.get("timecode") or m.get("anchor_type"), \
                f"marker '{m.get('marker_id')}' has no timecode or anchor"


class TestSubtitlesNoConflict:
    """subtitles do not conflict"""

    def test_subtitles_have_valid_timing(self):
        subs = _load_json("subtitle_plan.json") or []
        for s in subs:
            start = s.get("start_time", "")
            end = s.get("end_time", "")
            assert start < end, \
                f"subtitle '{s.get('subtitle_id')}' timing invalid: {start} >= {end}"

    def test_subtitles_have_nonempty_text(self):
        subs = _load_json("subtitle_plan.json") or []
        for s in subs:
            assert s.get("text", "").strip(), \
                f"subtitle '{s.get('subtitle_id')}' has empty text"

    def test_subtitles_have_anchor_type(self):
        subs = _load_json("subtitle_plan.json") or []
        for s in subs:
            assert s.get("anchor_type", ""), \
                f"subtitle '{s.get('subtitle_id')}' missing anchor_type"


class TestTransitionsAllowed:
    """transitions allowed"""

    def test_forbidden_transitions_not_used(self):
        policy = _load_json("transition_policy.json") or {}
        forbidden = set(policy.get("forbidden_transitions", []))
        for key in ["default", "same_scene_continuation", "new_topic", "new_chapter"]:
            val = policy.get(key, "")
            if val:
                assert val not in forbidden, \
                    f"policy {key}='{val}' is in forbidden list"

    def test_random_wipe_forbidden(self):
        policy = _load_json("transition_policy.json") or {}
        forbidden = policy.get("forbidden_transitions", [])
        assert "random_wipe" in forbidden, "random_wipe must be forbidden"

    def test_spin_forbidden(self):
        policy = _load_json("transition_policy.json") or {}
        forbidden = policy.get("forbidden_transitions", [])
        assert "spin" in forbidden, "spin must be forbidden"

    def test_excessive_glitch_forbidden(self):
        policy = _load_json("transition_policy.json") or {}
        forbidden = policy.get("forbidden_transitions", [])
        assert "excessive_glitch" in forbidden, "excessive_glitch must be forbidden"

    def test_fade_ratio_in_range(self):
        policy = _load_json("transition_policy.json") or {}
        ratio = policy.get("max_total_fade_ratio", 2.0)
        assert 0 <= ratio <= 1, f"fade ratio {ratio} out of range [0,1]"


class TestPreviewRenderNotExecuted:
    """preview render not executed"""

    def test_dry_run_render_not_executed(self):
        report = _load_json("timeline_preview_dry_run_report.json") or {}
        assert report.get("real_render_executed") is False

    def test_authorization_packet_render_not_executed(self):
        packet = _load_json("preview_render_authorization_packet.json") or {}
        assert packet.get("preview_render_executed") is False

    def test_authorization_required(self):
        packet = _load_json("preview_render_authorization_packet.json") or {}
        assert packet.get("authorization_required") is True

    def test_authorization_not_granted(self):
        packet = _load_json("preview_render_authorization_packet.json") or {}
        assert packet.get("authorization_granted") is False

    def test_operator_decision_null(self):
        packet = _load_json("preview_render_authorization_packet.json") or {}
        assert packet.get("operator_decision") is None


class TestModuleLevelDryRun:
    """Test the TimelineDryRun class directly with programmatic data."""

    def test_dry_run_with_valid_data(self):
        dry_run = TimelineDryRun()

        timeline_dict = {
            "project_id": "test_project",
            "fps": 24,
            "resolution": {"width": 1344, "height": 768},
            "tracks": {
                "video_main": [], "video_overlay": [],
                "audio_voice": [], "audio_music": [],
                "subtitles": [], "effects": [],
            },
            "scenes": [
                {
                    "scene_id": "test_scene", "duration_sec": 10.0,
                    "shot_ids": ["shot_001"], "asset_refs": ["asset.png"],
                    "start_time": "00:00:00", "end_time": "00:00:10",
                    "status": "planned",
                }
            ],
            "operations": [],
            "operator_review_required": True,
            "final_render_allowed": False,
        }

        markers = []
        subs = []
        policy = TransitionPolicy.default_policy()
        voice = VoiceCastingContract()
        preview = PreviewProofContract()

        report = dry_run.run(
            timeline_dict=timeline_dict,
            markers=markers,
            subtitles=subs,
            transition_policy=policy.to_dict(),
            voice_casting_contract=voice.to_dict(),
            preview_proof_contract=preview.to_dict(),
        )

        assert report.dry_run_status != "blocked", f"unexpected errors: {report.errors}"
        assert report.apply_performed is False
        assert report.real_render_executed is False

    def test_dry_run_with_empty_timeline(self):
        dry_run = TimelineDryRun()
        report = dry_run.run(
            timeline_dict={},
            markers=[],
            subtitles=[],
            transition_policy={},
            voice_casting_contract={},
            preview_proof_contract={},
        )
        assert report.dry_run_status == "blocked", "empty timeline should block"
        assert len(report.errors) > 0, "expected errors for empty timeline"

    def test_dry_run_detects_final_render_allowed(self):
        dry_run = TimelineDryRun()
        bad_timeline = {
            "project_id": "test",
            "fps": 24,
            "resolution": {"width": 1920, "height": 1080},
            "tracks": {"video_main": [], "video_overlay": [],
                       "audio_voice": [], "audio_music": [],
                       "subtitles": [], "effects": []},
            "scenes": [],
            "operations": [],
            "final_render_allowed": True,
            "operator_review_required": True,
        }
        report = dry_run.run(
            timeline_dict=bad_timeline,
            markers=[],
            subtitles=[],
            transition_policy={},
            voice_casting_contract={},
            preview_proof_contract={},
        )
        assert report.dry_run_status == "blocked", "final_render_allowed should block"
        assert any("final_render_allowed" in e for e in report.errors), \
            "expected error about final_render_allowed"

    def test_dry_run_detects_apply_performed(self):
        dry_run = TimelineDryRun()
        timeline = {
            "project_id": "test",
            "fps": 24,
            "resolution": {"width": 1920, "height": 1080},
            "tracks": {"video_main": [], "video_overlay": [],
                       "audio_voice": [], "audio_music": [],
                       "subtitles": [], "effects": []},
            "scenes": [],
            "operations": [
                {"operation_id": "bad_op", "apply_performed": True,
                 "requires_operator_review": True}
            ],
            "final_render_allowed": False,
            "operator_review_required": True,
        }
        report = dry_run.run(
            timeline_dict=timeline,
            markers=[],
            subtitles=[],
            transition_policy={},
            voice_casting_contract={},
            preview_proof_contract={},
        )
        assert report.dry_run_status == "blocked", "apply_performed should block"
        assert any("apply_performed" in e for e in report.errors), \
            "expected error about apply_performed"

    def test_dry_run_detects_missing_operator_review(self):
        dry_run = TimelineDryRun()
        timeline = {
            "project_id": "test",
            "fps": 24,
            "resolution": {"width": 1920, "height": 1080},
            "tracks": {"video_main": [], "video_overlay": [],
                       "audio_voice": [], "audio_music": [],
                       "subtitles": [], "effects": []},
            "scenes": [],
            "operations": [],
            "final_render_allowed": False,
            "operator_review_required": False,
        }
        report = dry_run.run(
            timeline_dict=timeline,
            markers=[],
            subtitles=[],
            transition_policy={},
            voice_casting_contract={},
            preview_proof_contract={},
        )
        assert report.dry_run_status == "blocked", \
            "operator_review_required=False should block"
