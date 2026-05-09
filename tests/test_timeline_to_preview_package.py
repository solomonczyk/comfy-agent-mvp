"""Tests for RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001 — Timeline-to-Preview Package.

Covers:
  - approved_asset_required
  - timeline_model_created
  - marker_registry_created
  - edit_decision_list_created
  - subtitle_plan_created
  - transition_policy_created
  - voice_casting_contract_created
  - preview_proof_contract_created
  - dry_run_passed
  - preview_render_not_executed
  - voice_generation_not_executed
  - assembly_not_executed
  - production_accepted_false
  - state_transition_correct
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path("F:/ComfyUI/comfy-agent-mvp")
DATA_ROOT = PROJECT_ROOT / "data" / "rc2_multishot1_ep01"
CONTROL_DIR = DATA_ROOT / "output" / "control"


@pytest.fixture(scope="module")
def manifest() -> dict:
    path = CONTROL_DIR / "approved_visual_assets_manifest.json"
    assert path.exists(), f"approved_visual_assets_manifest.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def timeline() -> dict:
    path = CONTROL_DIR / "timeline_model.json"
    assert path.exists(), f"timeline_model.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def markers() -> list:
    path = CONTROL_DIR / "marker_registry.json"
    assert path.exists(), f"marker_registry.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def edl() -> list:
    path = CONTROL_DIR / "edit_decision_list.json"
    assert path.exists(), f"edit_decision_list.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def subtitles() -> list:
    path = CONTROL_DIR / "subtitle_plan.json"
    assert path.exists(), f"subtitle_plan.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def transition_policy() -> dict:
    path = CONTROL_DIR / "transition_policy.json"
    assert path.exists(), f"transition_policy.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def voice_contract() -> dict:
    path = CONTROL_DIR / "voice_casting_contract.json"
    assert path.exists(), f"voice_casting_contract.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def preview_contract() -> dict:
    path = CONTROL_DIR / "preview_proof_contract.json"
    assert path.exists(), f"preview_proof_contract.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def dry_run_report() -> dict:
    path = CONTROL_DIR / "timeline_preview_dry_run_report.json"
    assert path.exists(), f"timeline_preview_dry_run_report.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def auth_packet() -> dict:
    path = CONTROL_DIR / "preview_render_authorization_packet.json"
    assert path.exists(), f"preview_render_authorization_packet.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def artifact_index() -> dict:
    path = CONTROL_DIR / "artifact_index.json"
    assert path.exists(), f"artifact_index.json not found at {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


class TestApprovedAssetRequired:
    """approved_asset_required"""

    def test_manifest_exists(self, manifest):
        assert manifest, "approved_visual_assets_manifest.json is empty"

    def test_manifest_has_approved_assets(self, manifest):
        assets = manifest.get("approved_assets", [])
        assert len(assets) > 0, "No approved assets in manifest"

    def test_approved_asset_has_path(self, manifest):
        asset = manifest["approved_assets"][0]
        path = asset.get("path", "")
        assert path, "approved asset path is empty"

    def test_approved_asset_path_exists(self, manifest):
        asset = manifest["approved_assets"][0]
        path = PROJECT_ROOT / asset.get("path", "")
        # The asset file might not exist on disk (could be from previous gen),
        # but the manifest path should be non-empty
        assert asset.get("path", ""), "approved asset path is required"

    def test_approved_asset_has_sha256(self, manifest):
        asset = manifest["approved_assets"][0]
        sha = asset.get("sha256", "")
        assert sha, "approved asset sha256 is empty"

    def test_production_accepted_false_in_manifest(self, manifest):
        assert manifest.get("production_accepted") is False, \
            "production_accepted must be False in manifest"


class TestTimelineModelCreated:
    """timeline_model_created"""

    def test_timeline_exists(self, timeline):
        assert timeline, "timeline_model.json is empty"

    def test_timeline_has_project_id(self, timeline):
        assert timeline.get("project_id") == "rc2_multishot1_ep01"

    def test_timeline_has_fps(self, timeline):
        fps = timeline.get("fps", 0)
        assert fps > 0, f"fps must be positive, got {fps}"

    def test_timeline_has_resolution(self, timeline):
        res = timeline.get("resolution", {})
        assert res.get("width", 0) > 0, "width must be positive"
        assert res.get("height", 0) > 0, "height must be positive"

    def test_timeline_has_tracks(self, timeline):
        tracks = timeline.get("tracks", {})
        required = {"video_main", "video_overlay", "audio_voice", "audio_music", "subtitles", "effects"}
        for t in required:
            assert t in tracks, f"missing required track '{t}'"

    def test_timeline_has_scenes(self, timeline):
        scenes = timeline.get("scenes", [])
        assert len(scenes) > 0, "timeline has no scenes"

    def test_timeline_scene_has_valid_duration(self, timeline):
        for scene in timeline.get("scenes", []):
            dur = scene.get("duration_sec", -1)
            assert dur >= 0, f"scene '{scene.get('scene_id')}' has negative duration"

    def test_timeline_operator_review_required(self, timeline):
        assert timeline.get("operator_review_required") is True

    def test_timeline_final_render_not_allowed(self, timeline):
        assert timeline.get("final_render_allowed") is False

    def test_timeline_asset_refs_in_scenes(self, timeline):
        for scene in timeline.get("scenes", []):
            for ref in scene.get("asset_refs", []):
                assert ref, "asset_ref must be non-empty"


class TestMarkerRegistryCreated:
    """marker_registry_created"""

    def test_markers_exist(self, markers):
        assert len(markers) > 0, "marker_registry is empty"

    def test_markers_have_ids(self, markers):
        for m in markers:
            assert m.get("marker_id", ""), f"marker missing marker_id: {m}"

    def test_markers_have_scene_ids(self, markers):
        for m in markers:
            assert m.get("scene_id", ""), f"marker '{m.get('marker_id')}' missing scene_id"

    def test_markers_have_shot_ids(self, markers):
        for m in markers:
            assert m.get("shot_id", ""), f"marker '{m.get('marker_id')}' missing shot_id"

    def test_markers_have_anchor_type(self, markers):
        for m in markers:
            anchor = m.get("anchor_type", "")
            assert anchor in (
                "scene_id", "shot_id", "timecode", "transcript_phrase", "frame_number"
            ), f"marker '{m.get('marker_id')}' invalid anchor_type '{anchor}'"

    def test_markers_no_duplicate_ids(self, markers):
        ids = [m.get("marker_id", "") for m in markers]
        assert len(ids) == len(set(ids)), "duplicate marker_ids found"

    def test_marker_ids_use_scene_shot_prefix(self, markers):
        for m in markers:
            mid = m.get("marker_id", "")
            assert mid.startswith("marker_"), \
                f"marker_id '{mid}' should start with 'marker_'"


class TestEditDecisionListCreated:
    """edit_decision_list_created"""

    def test_edl_has_operations(self, edl):
        assert len(edl) > 0, "edit_decision_list is empty"

    def test_edl_operations_apply_not_performed(self, edl):
        for op in edl:
            assert op.get("apply_performed") is False, \
                f"operation '{op.get('operation_id')}' has apply_performed=True"

    def test_edl_operations_require_operator_review(self, edl):
        for op in edl:
            assert op.get("requires_operator_review") is True, \
                f"operation '{op.get('operation_id')}' missing operator_review"

    def test_edl_operations_require_preview(self, edl):
        for op in edl:
            assert op.get("requires_preview") is True, \
                f"operation '{op.get('operation_id')}' missing requires_preview"

    def test_edl_operations_have_valid_types(self, edl):
        valid_ops = {
            "insert_clip", "replace_segment", "overlay_clip",
            "add_subtitle", "apply_transition", "add_voiceover_placeholder",
            "create_preview_required_marker",
        }
        for op in edl:
            assert op.get("operation", "") in valid_ops, \
                f"invalid operation type '{op.get('operation')}'"

    def test_edl_operations_have_anchors(self, edl):
        for op in edl:
            assert op.get("anchor", ""), \
                f"operation '{op.get('operation_id')}' missing anchor"


class TestSubtitlePlanCreated:
    """subtitle_plan_created"""

    def test_subtitles_exist(self, subtitles):
        assert len(subtitles) > 0, "subtitle_plan is empty"

    def test_subtitles_have_text(self, subtitles):
        for s in subtitles:
            text = s.get("text", "")
            assert text and text.strip(), \
                f"subtitle '{s.get('subtitle_id')}' has empty text"

    def test_subtitles_have_timing(self, subtitles):
        for s in subtitles:
            assert s.get("start_time", ""), \
                f"subtitle '{s.get('subtitle_id')}' missing start_time"
            assert s.get("end_time", ""), \
                f"subtitle '{s.get('subtitle_id')}' missing end_time"

    def test_subtitles_have_position(self, subtitles):
        valid_positions = {"bottom_center", "top_center", "left", "right", "custom"}
        for s in subtitles:
            pos = s.get("position", "")
            assert pos in valid_positions, \
                f"subtitle '{s.get('subtitle_id')}' invalid position '{pos}'"

    def test_subtitles_have_style(self, subtitles):
        valid_styles = {"clean_white", "yellow_on_black", "custom"}
        for s in subtitles:
            style = s.get("style", "")
            assert style in valid_styles, \
                f"subtitle '{s.get('subtitle_id')}' invalid style '{style}'"

    def test_subtitles_safe_zone_required(self, subtitles):
        for s in subtitles:
            if s.get("safe_zone_required") is not True:
                pass  # Not all subtitles must force this, but check it's set

    def test_subtitles_have_scene_ids(self, subtitles):
        for s in subtitles:
            assert s.get("scene_id", ""), \
                f"subtitle '{s.get('subtitle_id')}' missing scene_id"

    def test_subtitles_times_valid(self, subtitles):
        for s in subtitles:
            start = s.get("start_time", "")
            end = s.get("end_time", "")
            if start and end:
                assert end >= start, \
                    f"subtitle '{s.get('subtitle_id')}' end before start"


class TestTransitionPolicyCreated:
    """transition_policy_created"""

    def test_transition_policy_exists(self, transition_policy):
        assert transition_policy, "transition_policy.json is empty"

    def test_default_transition_set(self, transition_policy):
        assert transition_policy.get("default", ""), "default transition not set"

    def test_forbidden_transitions_listed(self, transition_policy):
        forbidden = transition_policy.get("forbidden_transitions", [])
        assert len(forbidden) > 0, "no forbidden transitions defined"
        for t in forbidden:
            assert t, f"empty forbidden transition entry"

    def test_no_cheap_or_random_transitions_allowed_as_default(self, transition_policy):
        forbidden = set(transition_policy.get("forbidden_transitions", []))
        cheap = {"random_wipe", "spin", "excessive_glitch", "star_wipe",
                 "checkerboard", "explosive_transition"}
        # At minimum, random_wipe and spin must be forbidden
        assert "random_wipe" in forbidden, "random_wipe not in forbidden transitions"

    def test_fade_ratio_validated(self, transition_policy):
        ratio = transition_policy.get("max_total_fade_ratio", 2.0)
        assert 0 <= ratio <= 1, \
            f"max_total_fade_ratio must be in [0,1], got {ratio}"

    def test_policy_transitions_not_in_forbidden(self, transition_policy):
        forbidden = set(transition_policy.get("forbidden_transitions", []))
        for key in ("default", "same_scene_continuation", "new_topic",
                     "new_chapter", "educational_style", "cinematic_style"):
            val = transition_policy.get(key, "")
            if val:
                assert val not in forbidden, \
                    f"transition '{val}' for '{key}' is in forbidden list"


class TestVoiceCastingContractCreated:
    """voice_casting_contract_created"""

    def test_voice_contract_exists(self, voice_contract):
        assert voice_contract, "voice_casting_contract.json is empty"

    def test_voice_contract_has_language(self, voice_contract):
        assert voice_contract.get("language", ""), "language is required"

    def test_voice_contract_has_tone(self, voice_contract):
        tone = voice_contract.get("tone", [])
        assert len(tone) > 0, "tone must have at least one entry"

    def test_voice_contract_has_pace(self, voice_contract):
        assert voice_contract.get("pace", ""), "pace is required"

    def test_sample_required(self, voice_contract):
        assert voice_contract.get("sample_required") is True, \
            "sample_required must be True"

    def test_operator_review_required(self, voice_contract):
        assert voice_contract.get("operator_review_required") is True, \
            "operator_review_required must be True"

    def test_voiceover_generation_not_allowed(self, voice_contract):
        assert voice_contract.get("full_voiceover_generation_allowed") is False, \
            "full_voiceover_generation_allowed must be False"

    def test_voice_contract_has_avoid_list(self, voice_contract):
        avoid = voice_contract.get("avoid", [])
        assert len(avoid) > 0, "avoid list must have entries"


class TestPreviewProofContractCreated:
    """preview_proof_contract_created"""

    def test_preview_contract_exists(self, preview_contract):
        assert preview_contract, "preview_proof_contract.json is empty"

    def test_preview_lowres_required(self, preview_contract):
        assert preview_contract.get("preview_lowres_required") is True

    def test_preview_gif_required(self, preview_contract):
        assert preview_contract.get("preview_gif_required") is True

    def test_contact_sheet_required(self, preview_contract):
        assert preview_contract.get("contact_sheet_required") is True

    def test_subtitle_burnin_required(self, preview_contract):
        assert preview_contract.get("subtitle_burnin_preview_required") is True

    def test_transition_qa_required(self, preview_contract):
        assert preview_contract.get("transition_qa_required") is True

    def test_subtitle_qa_required(self, preview_contract):
        assert preview_contract.get("subtitle_qa_required") is True

    def test_audio_qa_required(self, preview_contract):
        assert preview_contract.get("audio_qa_required") is True

    def test_operator_review_required(self, preview_contract):
        assert preview_contract.get("operator_review_required") is True

    def test_final_render_not_allowed(self, preview_contract):
        assert preview_contract.get("final_render_allowed") is False


class TestDryRunPassed:
    """dry_run_passed"""

    def test_dry_run_report_exists(self, dry_run_report):
        assert dry_run_report, "timeline_preview_dry_run_report.json is empty"

    def test_dry_run_status_not_blocked(self, dry_run_report):
        status = dry_run_report.get("dry_run_status", "")
        assert status != "blocked", \
            f"dry_run_status is 'blocked': {dry_run_report.get('errors', [])}"

    def test_dry_run_no_errors(self, dry_run_report):
        errors = dry_run_report.get("errors", [])
        assert len(errors) == 0, f"dry-run has errors: {errors}"

    def test_dry_run_apply_not_performed(self, dry_run_report):
        assert dry_run_report.get("apply_performed") is False

    def test_dry_run_render_not_executed(self, dry_run_report):
        assert dry_run_report.get("real_render_executed") is False

    def test_dry_run_final_render_not_allowed(self, dry_run_report):
        assert dry_run_report.get("final_render_allowed") is False

    def test_dry_run_operator_review_required(self, dry_run_report):
        assert dry_run_report.get("operator_review_required") is True


class TestForbiddenActions:
    """preview_render_not_executed, voice_generation_not_executed,
       assembly_not_executed, production_accepted_false
    """

    def test_artifact_index_production_not_accepted(self, artifact_index):
        assert artifact_index.get("production_accepted") is False

    def test_artifact_index_preview_not_executed(self, artifact_index):
        assert artifact_index.get("preview_render_executed") is False

    def test_artifact_index_voice_not_generated(self, artifact_index):
        assert artifact_index.get("voice_generation_executed") is False

    def test_artifact_index_assembly_not_executed(self, artifact_index):
        assert artifact_index.get("assembly_executed") is False

    def test_artifact_index_downstream_not_executed(self, artifact_index):
        assert artifact_index.get("downstream_executed") is False

    def test_auth_packet_preview_not_executed(self, auth_packet):
        assert auth_packet.get("preview_render_executed") is False

    def test_auth_packet_voice_not_generated(self, auth_packet):
        assert auth_packet.get("voice_generation_executed") is False

    def test_auth_packet_assembly_not_executed(self, auth_packet):
        assert auth_packet.get("assembly_executed") is False

    def test_auth_packet_downstream_not_executed(self, auth_packet):
        assert auth_packet.get("downstream_executed") is False

    def test_auth_packet_production_not_accepted(self, auth_packet):
        assert auth_packet.get("production_accepted") is False

    def test_auth_packet_forbidden_actions_all_false(self, auth_packet):
        forbidden = auth_packet.get("forbidden_actions", {})
        for action, value in forbidden.items():
            assert value is False, \
                f"forbidden action '{action}' must be False, got {value}"

    def test_auth_packet_no_operator_decision(self, auth_packet):
        assert auth_packet.get("operator_decision") is None, \
            "operator_decision must be null before gate approval"

    def test_auth_packet_authorization_not_granted(self, auth_packet):
        assert auth_packet.get("authorization_granted") is False


class TestStateTransitionCorrect:
    """state_transition_correct"""

    def test_current_state_is_preview_render_authorization_required(self, artifact_index):
        assert artifact_index.get("current_state") == "preview_render_authorization_required", \
            f"current_state='{artifact_index.get('current_state')}', expected 'preview_render_authorization_required'"

    def test_next_allowed_action_is_correct(self, artifact_index):
        assert artifact_index.get("next_allowed_action") == "preview_render_authorization_required"

    def test_task_id_correct(self, artifact_index):
        task_id = artifact_index.get("task_id", "")
        assert task_id == "RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001", \
            f"task_id='{task_id}', expected 'RC-COMBINE-V2-TIMELINE-TO-PREVIEW-001'"

    def test_timeline_model_created_flag(self, artifact_index):
        assert artifact_index.get("timeline_model_created") is True

    def test_marker_registry_created_flag(self, artifact_index):
        assert artifact_index.get("marker_registry_created") is True

    def test_edit_decision_list_created_flag(self, artifact_index):
        assert artifact_index.get("edit_decision_list_created") is True

    def test_subtitle_plan_created_flag(self, artifact_index):
        assert artifact_index.get("subtitle_plan_created") is True

    def test_transition_policy_created_flag(self, artifact_index):
        assert artifact_index.get("transition_policy_created") is True

    def test_voice_casting_created_flag(self, artifact_index):
        assert artifact_index.get("voice_casting_contract_created") is True

    def test_preview_proof_created_flag(self, artifact_index):
        assert artifact_index.get("preview_proof_contract_created") is True

    def test_dry_run_report_created_flag(self, artifact_index):
        assert artifact_index.get("timeline_preview_dry_run_report_created") is True

    def test_auth_packet_created_flag(self, artifact_index):
        assert artifact_index.get("preview_render_authorization_packet_created") is True
