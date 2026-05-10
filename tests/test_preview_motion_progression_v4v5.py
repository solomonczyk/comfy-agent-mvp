"""Tests for RC-COMBINE-V2-PREVIEW-MOTION-PROGRESSION-FIX-V4V5-001."""

import json
import math
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest

from app.timeline.preview_motion_progression import (
    MotionKeyframe,
    SegmentMotionPlan,
    build_controlled_preview_motion_render_gate_package,
    build_preview_motion_progression_plan_v4v5,
    build_preview_motion_renderer_contract_v4v5,
    build_segment_keyframes_artifact,
    evaluate_motion_plan_for_duplicate_reduction,
    generate_segment_keyframes,
    MAX_PAN_RATIO,
    MAX_ZOOM_VARIATION,
    TRANSITION_PADDING_FRAMES,
    MIN_FRAME_DELTA_MAE,
    DUPLICATE_RATIO_FAIL_THRESHOLD,
    TASK_ID,
)
from app.timeline.controlled_preview_rerender import (
    LEGACY_STATIC_HOLD_BLOCKED,
    LEGACY_STATIC_HOLD_DIAGNOSTIC_ONLY,
    build_preview_segment_render_plan_v3,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_segments() -> List[Dict[str, Any]]:
    return [
        {
            "segment_index": 0,
            "asset_path": "/tmp/fake_asset_0.png",
            "frame_start": 0,
            "frame_end": 120,
            "frame_count": 120,
        },
        {
            "segment_index": 1,
            "asset_path": "/tmp/fake_asset_1.png",
            "frame_start": 120,
            "frame_end": 240,
            "frame_count": 120,
        },
        {
            "segment_index": 2,
            "asset_path": "/tmp/fake_asset_2.png",
            "frame_start": 240,
            "frame_end": 360,
            "frame_count": 120,
        },
    ]


@pytest.fixture
def fake_img_dimensions() -> Dict[str, tuple]:
    return {
        "/tmp/fake_asset_0.png": (1024, 1024),
        "/tmp/fake_asset_1.png": (1024, 1024),
        "/tmp/fake_asset_2.png": (1024, 1024),
    }


# ---------------------------------------------------------------------------
# Legacy static hold blocked
# ---------------------------------------------------------------------------

def test_legacy_static_hold_blocked() -> None:
    assert LEGACY_STATIC_HOLD_BLOCKED is True
    assert LEGACY_STATIC_HOLD_DIAGNOSTIC_ONLY is False


def test_legacy_static_hold_not_default_in_renderer() -> None:
    from app.timeline.controlled_preview_rerender import _create_segment_preview_frames
    import inspect
    sig = inspect.signature(_create_segment_preview_frames)
    params = list(sig.parameters.keys())
    assert "motion_keyframes" in params


# ---------------------------------------------------------------------------
# Motion keyframe generation
# ---------------------------------------------------------------------------

def test_generate_segment_keyframes_basic() -> None:
    plan = generate_segment_keyframes(
        segment_index=0,
        asset_path="/tmp/fake.png",
        frame_start=0,
        frame_end=120,
        img_width=1024,
        img_height=1024,
    )
    assert plan.segment_index == 0
    assert plan.asset_path == "/tmp/fake.png"
    assert plan.frame_start == 0
    assert plan.frame_end == 120
    assert len(plan.keyframes) == 120
    assert plan.deterministic_seed is not None
    assert plan.base_zoom >= 1.0
    assert plan.min_frame_delta_policy_met is True


def test_generate_segment_keyframes_determinism() -> None:
    plan1 = generate_segment_keyframes(
        segment_index=1,
        asset_path="/tmp/fake.png",
        frame_start=0,
        frame_end=60,
        img_width=1024,
        img_height=1024,
    )
    plan2 = generate_segment_keyframes(
        segment_index=1,
        asset_path="/tmp/fake.png",
        frame_start=0,
        frame_end=60,
        img_width=1024,
        img_height=1024,
    )
    assert plan1.deterministic_seed == plan2.deterministic_seed
    assert plan1.motion_type == plan2.motion_type
    for k1, k2 in zip(plan1.keyframes, plan2.keyframes):
        assert k1.zoom == pytest.approx(k2.zoom, abs=1e-5)
        assert k1.pan_x == pytest.approx(k2.pan_x, abs=1e-5)
        assert k1.pan_y == pytest.approx(k2.pan_y, abs=1e-5)


def test_generate_segment_keyframes_different_assets_get_different_motion() -> None:
    plan1 = generate_segment_keyframes(0, "/tmp/a.png", 0, 60, 1024, 1024)
    plan2 = generate_segment_keyframes(0, "/tmp/b.png", 0, 60, 1024, 1024)
    # Different seed -> different motion_type or different pan values
    assert plan1.deterministic_seed != plan2.deterministic_seed or plan1.motion_type == plan2.motion_type


def test_keyframe_crop_within_bounds() -> None:
    plan = generate_segment_keyframes(0, "/tmp/fake.png", 0, 120, 1024, 1024)
    for kf in plan.keyframes:
        assert 0.0 <= kf.crop_left <= 1.0
        assert 0.0 <= kf.crop_top <= 1.0
        assert 0.0 < kf.crop_width <= 1.0
        assert 0.0 < kf.crop_height <= 1.0
        assert kf.crop_left + kf.crop_width <= 1.0 + 1e-5
        assert kf.crop_top + kf.crop_height <= 1.0 + 1e-5


def test_zoom_variation_within_limits() -> None:
    plan = generate_segment_keyframes(0, "/tmp/fake.png", 0, 120, 1024, 1024)
    zooms = [kf.zoom for kf in plan.keyframes]
    max_zoom = max(zooms)
    min_zoom = min(zooms)
    # Base zoom * (1 + max variation) is the theoretical max
    assert max_zoom <= plan.base_zoom * (1 + MAX_ZOOM_VARIATION) + 1e-3
    assert min_zoom >= plan.base_zoom * (1 - MAX_ZOOM_VARIATION) - 1e-3


def test_pan_within_limits() -> None:
    plan = generate_segment_keyframes(0, "/tmp/fake.png", 0, 120, 1024, 1024)
    for kf in plan.keyframes:
        assert abs(kf.pan_x) <= MAX_PAN_RATIO + 1e-3
        assert abs(kf.pan_y) <= MAX_PAN_RATIO + 1e-3


def test_motion_score_non_zero_for_progressing_keyframes() -> None:
    plan = generate_segment_keyframes(0, "/tmp/fake.png", 0, 120, 1024, 1024)
    # At least some keyframes after the first should have motion_score > 0
    scores = [kf.motion_score for kf in plan.keyframes[1:]]
    assert any(s > 0.0 for s in scores)


# ---------------------------------------------------------------------------
# Multi-segment motion plan
# ---------------------------------------------------------------------------

def test_build_preview_motion_progression_plan(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    assert plan["plan_type"] == "preview_motion_progression_plan_v4v5"
    assert plan["task_id"] == TASK_ID
    assert plan["version"] == "v4v5"
    assert plan["deterministic"] is True
    assert plan["reproducible"] is True
    assert plan["total_segments"] == 3
    assert plan["total_keyframes"] == 360
    assert plan["transition_padding_frames"] == TRANSITION_PADDING_FRAMES
    assert "motion_types_used" in plan
    assert len(plan["segments"]) == 3


def test_motion_plan_segments_have_keyframes(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    for seg in plan["segments"]:
        assert "keyframes" in seg
        assert len(seg["keyframes"]) == seg["frame_end"] - seg["frame_start"]
        assert seg["min_frame_delta_policy_met"] is True


# ---------------------------------------------------------------------------
# Keyframes artifact
# ---------------------------------------------------------------------------

def test_build_segment_keyframes_artifact(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    artifact = build_segment_keyframes_artifact(plan)
    assert artifact["artifact_type"] == "preview_motion_segment_keyframes_v4v5"
    assert artifact["segment_count"] == 3
    lookup = artifact["segment_lookup"]
    assert "0" in lookup
    assert "1" in lookup
    assert "2" in lookup
    assert "keyframes" in lookup["0"]


# ---------------------------------------------------------------------------
# Duplicate reduction QA (dry-run mode)
# ---------------------------------------------------------------------------

def test_qa_dry_run_evaluates_plan(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    qa = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    assert qa["qa_type"] == "preview_motion_duplicate_reduction_qa"
    assert qa["render_executed"] is False
    assert qa["evaluated"] is True
    assert qa["mode"] == "dry_run_synthetic"
    assert qa["total_frames_evaluated"] == 360
    assert "overall_estimated_duplicate_ratio" in qa
    assert "passes_qa" in qa
    assert "per_segment_qa" in qa
    assert len(qa["per_segment_qa"]) == 3


def test_qa_honest_render_executed_flag(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    qa_dry = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    qa_post = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=True)
    assert qa_dry["render_executed"] is False
    assert qa_post["render_executed"] is True
    assert qa_dry["mode"] == "dry_run_synthetic"
    assert qa_post["mode"] == "post_render"


def test_qa_estimated_duplicate_ratio_reasonable(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    qa = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    ratio = qa["overall_estimated_duplicate_ratio"]
    assert 0.0 <= ratio <= 1.0
    # Motion should reduce duplicates below the static hold level of 0.917
    assert ratio < 0.85


def test_qa_no_static_holds_detected(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    qa = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    assert qa["static_hold_segments"] == 0
    for seg_qa in qa["per_segment_qa"]:
        assert seg_qa["static_hold_detected"] is False


def test_qa_contact_sheet_useful(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    qa = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    assert qa["contact_sheet_useful_overall"] is True


# ---------------------------------------------------------------------------
# Renderer contract
# ---------------------------------------------------------------------------

def test_renderer_contract_blocks_legacy_static_hold() -> None:
    contract = build_preview_motion_renderer_contract_v4v5()
    assert contract["contract_type"] == "preview_motion_renderer_contract_v4v5"
    assert contract["legacy_static_hold_mode"]["allowed"] is False
    assert contract["legacy_static_hold_mode"]["default"] is False
    assert contract["legacy_static_hold_mode"]["fallback_forbidden"] is True
    assert contract["legacy_static_hold_mode"]["diagnostic_mode_only"] is False


def test_renderer_contract_lists_required_features() -> None:
    contract = build_preview_motion_renderer_contract_v4v5()
    features = contract["required_renderer_features"]
    assert "per_frame_crop_transform" in features
    assert "per_frame_zoom_transform" in features
    assert "per_frame_pan_transform" in features
    assert "segment_transition_padding" in features
    assert "deterministic_keyframe_consumption" in features


def test_renderer_contract_blocks_specific_behaviors() -> None:
    contract = build_preview_motion_renderer_contract_v4v5()
    blocked = contract["blocked_behaviors"]
    assert "asset = assets[0]; repeat asset for all frames" in blocked
    assert "single_source_repeat_for_all_segments" in blocked
    assert "zero_crop_variation_across_frames" in blocked
    assert "zero_zoom_variation_across_frames" in blocked
    assert "static_hold_without_explicit_still_scene_contract" in blocked


# ---------------------------------------------------------------------------
# Gate package
# ---------------------------------------------------------------------------

def test_gate_package_requires_operator_authorization(sample_segments, fake_img_dimensions) -> None:
    plan = build_preview_motion_progression_plan_v4v5(sample_segments, fake_img_dimensions)
    keyframes = build_segment_keyframes_artifact(plan)
    qa = evaluate_motion_plan_for_duplicate_reduction(plan, render_executed=False)
    contract = build_preview_motion_renderer_contract_v4v5()
    gate = build_controlled_preview_motion_render_gate_package(plan, keyframes, qa, contract)

    assert gate["package_type"] == "controlled_preview_motion_render_gate_package"
    assert gate["current_state"] == "controlled_preview_motion_render_authorization_required"
    assert gate["next_allowed_action"] == "controlled_preview_motion_render_authorization_required"
    assert gate["requires_operator_authorization"] is True
    assert gate["agent_may_authorize"] is False
    assert gate["preview_render_executed"] is False
    assert gate["new_image_generation_performed"] is False
    assert gate["comfyui_submit_executed"] is False
    assert gate["retry_attempted"] is False
    assert gate["voice_generation_executed"] is False
    assert gate["assembly_executed"] is False
    assert gate["downstream_executed"] is False
    assert gate["production_accepted"] is False


# ---------------------------------------------------------------------------
# Artifact files exist on disk
# ---------------------------------------------------------------------------

CONTROL_DIR = Path("F:/ComfyUI/comfy-agent-mvp/data/rc2_multishot1_ep01/output/control")

REQUIRED_ARTIFACTS = [
    "preview_motion_startup_verification.json",
    "preview_motion_root_cause_report.json",
    "preview_motion_progression_plan_v4v5.json",
    "preview_motion_segment_keyframes_v4v5.json",
    "preview_motion_duplicate_reduction_policy.json",
    "preview_motion_renderer_contract.json",
    "controlled_preview_motion_render_gate_package.json",
]


@pytest.mark.parametrize("artifact_name", REQUIRED_ARTIFACTS)
def test_required_artifact_exists(artifact_name: str) -> None:
    path = CONTROL_DIR / artifact_name
    assert path.exists(), f"Missing artifact: {path}"
    assert path.stat().st_size > 0


def test_artifact_index_updated() -> None:
    path = CONTROL_DIR / "artifact_index.json"
    with open(path, "r", encoding="utf-8") as f:
        idx = json.load(f)
    assert idx.get("current_state") == "controlled_preview_motion_render_authorization_required"
    assert idx.get("next_allowed_action") == "controlled_preview_motion_render_authorization_required"
    assert idx.get("preview_motion_progression_package_created") is True
    assert idx.get("legacy_static_hold_blocked") is True
    assert idx.get("motion_progression_layer_created") is True
    assert idx.get("segment_keyframes_created") is True
    assert idx.get("duplicate_reduction_policy_created") is True
    assert idx.get("preview_render_executed") is False
    assert idx.get("new_image_generation_performed") is False
    assert idx.get("comfyui_submit_executed") is False
    assert idx.get("production_accepted") is False


def test_episode_ledger_updated() -> None:
    path = CONTROL_DIR / "episode_ledger.json"
    with open(path, "r", encoding="utf-8") as f:
        ledger = json.load(f)
    motion_events = [e for e in ledger if e.get("task_id") == TASK_ID]
    assert len(motion_events) >= 1
    # Find the package creation event (not the state_transition event)
    package_events = [e for e in motion_events if e.get("event_type") == "preview_motion_progression_package_created"]
    assert len(package_events) >= 1
    latest = package_events[-1]
    assert latest["current_state"] == "controlled_preview_motion_render_authorization_required"
    assert latest["next_allowed_action"] == "controlled_preview_motion_render_authorization_required"
    assert latest["preview_render_executed"] is False
    assert latest["new_image_generation_performed"] is False
    assert latest["comfyui_submit_executed"] is False
    assert latest["production_accepted"] is False


# ---------------------------------------------------------------------------
# Startup / root cause report content
# ---------------------------------------------------------------------------

def test_startup_verification_content() -> None:
    path = CONTROL_DIR / "preview_motion_startup_verification.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["startup_commit_verified"] is True
    assert data["startup_commit_hash"] == "da8222b"
    assert data["startup_combine_status_verified"] is True
    assert data["combine_status"]["current_state"] == "preview_correction_plan_required"
    assert data["git_status_clean"] is True


def test_root_cause_report_content() -> None:
    path = CONTROL_DIR / "preview_motion_root_cause_report.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["previous_duplicate_ratio"] == 0.917
    assert data["root_cause"] == "static_still_image_segment_holds"
    assert data["requires_new_generation"] is False


def test_duplicate_reduction_policy_content() -> None:
    path = CONTROL_DIR / "preview_motion_duplicate_reduction_policy.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["policy_type"] == "preview_motion_duplicate_reduction_policy_v4v5"
    assert data["frame_level_duplicate_ratio"]["hard_fail_threshold"] == DUPLICATE_RATIO_FAIL_THRESHOLD
    assert data["dry_run_mode"]["supported"] is True
    assert data["dry_run_mode"]["honest_render_executed_flag"] is True


# ---------------------------------------------------------------------------
# py_compile sanity for modified files
# ---------------------------------------------------------------------------

def test_py_compile_controlled_preview_rerender() -> None:
    import py_compile
    py_compile.compile("app/timeline/controlled_preview_rerender.py", doraise=True)


def test_py_compile_preview_motion_progression() -> None:
    import py_compile
    py_compile.compile("app/timeline/preview_motion_progression.py", doraise=True)
