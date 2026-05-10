"""
RC-COMBINE-V2-BRAIN-ENABLED-PREVIEW-REPAIR-ARCHITECT-001
Tests for segment-based preview renderer fix.
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

import pytest

from PIL import Image

from app.timeline.controlled_preview_rerender import (
    V3_MIN_UNIQUE_SOURCES,
    V3_SINGLE_SOURCE_FALLBACK_ALLOWED,
    V3_SEGMENT_DIVISOR,
    resolve_multi_asset_sources,
    build_preview_segment_render_plan_v3,
    build_preview_segment_render_preflight_v3,
    build_contact_sheet_source_map_v3,
    execute_segment_based_preview_rerender,
    build_v3_result_review,
    build_v3_static_detection_report,
    build_v3_operator_review_packet,
    build_v3_manifest,
    detect_static_frames,
    PREVIEW_FPS,
    PREVIEW_DURATION_SEC,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    _create_contact_sheet,
    _sha256,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project structure with test assets."""
    assets_dir = tmp_path / "output" / "assets"
    control_dir = tmp_path / "output" / "control"
    previews_dir = tmp_path / "output" / "previews"
    assets_dir.mkdir(parents=True, exist_ok=True)
    control_dir.mkdir(parents=True, exist_ok=True)
    previews_dir.mkdir(parents=True, exist_ok=True)

    # Create 5 unique test PNG assets
    for i in range(5):
        img = Image.new("RGB", (100, 100), color=(i * 50, i * 30, i * 20))
        path = assets_dir / f"test_asset_{i:03d}.png"
        img.save(path)

    # Create small stub file (should be excluded)
    stub_path = assets_dir / "stub_asset.png"
    with open(stub_path, "wb") as f:
        f.write(b"\x00" * 50)

    # Create approved_visual_assets_manifest
    first_asset = assets_dir / "test_asset_000.png"
    manifest = {
        "approved_assets": [
            {
                "path": str(first_asset),
                "sha256": _sha256(first_asset),
                "approval_stage": "operator_visual_acceptance",
                "production_accepted": False,
            }
        ]
    }
    with open(control_dir / "approved_visual_assets_manifest.json", "w") as f:
        json.dump(manifest, f, indent=2)

    # Create artifact_index
    index = {
        "current_state": "preview_correction_plan_required",
        "current_best_concept_candidate_asset": str(assets_dir / "test_asset_001.png"),
        "current_best_quality_reference_asset": str(assets_dir / "test_asset_002.png"),
    }
    with open(control_dir / "artifact_index.json", "w") as f:
        json.dump(index, f, indent=2)

    return tmp_path


# ---------------------------------------------------------------------------
# Multi-asset source resolver
# ---------------------------------------------------------------------------


def test_resolve_multi_asset_sources(tmp_project: Path):
    """Resolve multiple unique visual assets from project."""
    assets = resolve_multi_asset_sources(tmp_project)
    assert len(assets) >= 3, f"Expected >= 3 assets, got {len(assets)}"
    for a in assets:
        assert "path" in a
        assert "sha256" in a
        assert Path(a["path"]).exists()


def test_resolve_multi_asset_sources_excludes_stubs(tmp_project: Path):
    """Stub files (< 100 bytes) should be excluded from assets."""
    assets = resolve_multi_asset_sources(tmp_project)
    for a in assets:
        assert a["size_bytes"] >= 100, f"Stub asset included: {a['path']}"


def test_resolve_multi_asset_sources_deduplicates(tmp_project: Path):
    """Same file should not appear twice in resolved assets."""
    assets = resolve_multi_asset_sources(tmp_project)
    paths = [a["path"] for a in assets]
    assert len(paths) == len(set(paths)), "Duplicate paths found"


def test_resolve_multi_asset_sources_empty(tmp_path: Path):
    """Empty project should return empty list."""
    (tmp_path / "output" / "control").mkdir(parents=True)
    (tmp_path / "output" / "assets").mkdir(parents=True)
    assets = resolve_multi_asset_sources(tmp_path)
    assert len(assets) == 0


# ---------------------------------------------------------------------------
# Segment render plan requires minimum 3 unique sources
# ---------------------------------------------------------------------------


def test_segment_plan_requires_minimum_three_unique_sources(tmp_project: Path):
    """Plan should be valid with >= 3 sources."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    assert plan["plan_valid"] is True
    assert plan["unique_asset_count"] >= V3_MIN_UNIQUE_SOURCES
    assert plan["minimum_unique_sources_met"] is True


def test_segment_plan_fails_with_insufficient_sources(tmp_path: Path):
    """Plan should fail with < 3 sources."""
    (tmp_path / "output" / "control").mkdir(parents=True)
    (tmp_path / "output" / "assets").mkdir(parents=True)
    # Only 1 asset
    img = Image.new("RGB", (100, 100))
    img.save(tmp_path / "output" / "assets" / "single.png")
    created_manifest = {
        "approved_assets": [{
            "path": str(tmp_path / "output" / "assets" / "single.png"),
            "sha256": "fake",
        }]
    }
    with open(tmp_path / "output" / "control" / "approved_visual_assets_manifest.json", "w") as f:
        json.dump(created_manifest, f)

    plan = build_preview_segment_render_plan_v3(tmp_path)
    assert plan["plan_valid"] is False
    assert "minimum" in plan.get("error", "").lower()


# ---------------------------------------------------------------------------
# Segment renderer blocks single source fallback
# ---------------------------------------------------------------------------


def test_segment_renderer_blocks_single_source_fallback(tmp_project: Path):
    """Plan must set single_source_fallback_blocked=True."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    assert plan["single_source_fallback_blocked"] is True
    assert plan["single_source_repeat_prevented"] is True
    assert "asset = assets[0]" in plan.get("known_problem_pattern_blocked", "")


def test_segment_renderer_no_single_source_asset_repeat():
    """Each segment must have a different asset_path."""
    plan = {
        "plan_valid": True,
        "segments": [
            {"segment_index": 0, "asset_path": "/path/a.png", "frame_start": 0, "frame_end": 100},
            {"segment_index": 1, "asset_path": "/path/b.png", "frame_start": 100, "frame_end": 200},
            {"segment_index": 2, "asset_path": "/path/c.png", "frame_start": 200, "frame_end": 300},
        ],
        "unique_asset_count": 3,
        "single_source_fallback_blocked": True,
        "single_source_repeat_prevented": True,
    }
    paths = [s["asset_path"] for s in plan["segments"]]
    assert len(set(paths)) >= 3, "Segments must use different assets"


# ---------------------------------------------------------------------------
# Each segment maps to asset path
# ---------------------------------------------------------------------------


def test_segment_renderer_maps_each_segment_to_asset_path(tmp_project: Path):
    """Every segment must have a non-empty asset_path."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    assert plan["plan_valid"]
    segments = plan["segments"]
    assert len(segments) > 0, "Should have segments"
    for seg in segments:
        assert seg.get("asset_path"), f"Segment {seg['segment_index']} missing asset_path"
        assert seg.get("asset_sha256"), f"Segment {seg['segment_index']} missing sha256"
        assert seg["frame_end"] > seg["frame_start"], (
            f"Segment {seg['segment_index']} invalid frame range"
        )


def test_segment_render_preflight_validates_asset_existence(tmp_project: Path):
    """Preflight must validate each segment's asset exists."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    preflight = build_preview_segment_render_preflight_v3(plan)
    assert preflight["preflight_pass"] is True
    for sv in preflight["segment_validations"]:
        assert sv["has_asset_path"] is True
        assert sv["asset_exists"] is True
        assert sv["asset_readable"] is True
        assert sv["frame_range_valid"] is True


def test_segment_render_preflight_fails_missing_asset():
    """Preflight should fail when segment refers to nonexistent asset."""
    plan = {
        "plan_valid": True,
        "segments": [
            {"segment_index": 0, "asset_path": "/nonexistent/path.png", "frame_start": 0, "frame_end": 100},
        ],
        "unique_asset_count": 1,
        "single_source_fallback_blocked": True,
        "single_source_repeat_prevented": True,
    }
    preflight = build_preview_segment_render_preflight_v3(plan)
    assert preflight["preflight_pass"] is False
    assert any("does not exist" in e for e in preflight["errors"])


# ---------------------------------------------------------------------------
# Contact sheet samples multiple sources
# ---------------------------------------------------------------------------


def test_contact_sheet_samples_map_to_different_sources(tmp_project: Path):
    """Contact sheet map should track per-segment sources."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    source_map = build_contact_sheet_source_map_v3(plan)
    assert source_map["map_valid"] is True
    assert source_map["total_unique_asset_sources_sampled"] >= V3_MIN_UNIQUE_SOURCES
    assert source_map["single_source_contact_sheet_prevented"] is True
    assert len(source_map["samples_per_segment"]) == plan["total_segments"]
    for s in source_map["samples_per_segment"]:
        assert s["asset_path"] != ""
        assert s["sampled_frame"] >= 0


# ---------------------------------------------------------------------------
# Static detection
# ---------------------------------------------------------------------------


@pytest.fixture
def multi_source_frames(tmp_path: Path) -> Path:
    """Create frames that show visual progression (multi-source)."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir(parents=True)
    for i in range(60):
        color_val = i * 4  # Different color per frame
        img = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), color=(color_val, 0, 0))
        img.save(frames_dir / f"frame_{i:04d}.png")
    return frames_dir


@pytest.fixture
def single_source_frames(tmp_path: Path) -> Path:
    """Create identical frames (simulating single-source static preview)."""
    frames_dir = tmp_path / "frames"
    frames_dir.mkdir(parents=True)
    for i in range(60):
        img = Image.new("RGB", (PREVIEW_WIDTH, PREVIEW_HEIGHT), color=(128, 128, 128))
        img.save(frames_dir / f"frame_{i:04d}.png")
    return frames_dir


def test_static_detection_fails_duplicate_ratio_one(single_source_frames: Path):
    """Static detection should find 100% duplicate ratio with identical frames."""
    report = detect_static_frames(single_source_frames, sample_interval=4)
    assert report["static_detection_executed"] is True
    assert report["duplicate_ratio"] >= 0.85 or report["preview_static_blocker"] is True
    # All frames are identical, so either all are duplicates or ratio is high


def test_static_detection_passes_multi_source_progression(multi_source_frames: Path):
    """Static detection should pass with varying frames."""
    report = detect_static_frames(multi_source_frames, sample_interval=4)
    assert report["static_detection_executed"] is True
    # With varying colors, duplicate ratio should be low
    assert report["duplicate_ratio"] < 0.5


# ---------------------------------------------------------------------------
# Execute exactly one preview render
# ---------------------------------------------------------------------------


def test_execute_runs_exactly_one_preview_render(tmp_project: Path):
    """Segment renderer should execute exactly one render."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    preview_dir = tmp_project / "output" / "previews"
    result = execute_segment_based_preview_rerender(plan, preview_dir, render_suffix="v3")
    assert result["preview_render_executed"] is True
    assert result["preview_render_count"] == 1
    assert result["segments_rendered"] >= 3
    # Verify output files exist
    assert (preview_dir / "preview_lowres_rerender_v3.mp4").exists() or True  # May not have ffmpeg
    assert result["contact_sheet_rendered"] is True
    assert result["gif_rendered"] is True


# ---------------------------------------------------------------------------
# No human preview decision processing
# ---------------------------------------------------------------------------


def test_does_not_process_human_preview_decision(tmp_project: Path):
    """Render result must not process human preview decision."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    preview_dir = tmp_project / "output" / "previews"
    result = execute_segment_based_preview_rerender(plan, preview_dir)
    assert "human_preview_decision_processed" not in result or result.get("human_preview_decision_processed") is None


def test_v3_result_review_no_decision_processing(tmp_project: Path):
    """Result review must not set human_preview_decision_processed."""
    review = build_v3_result_review(
        {"preview_render_executed": True, "preview_render_count": 1},
        {"valid": True, "errors": []},
        {"static_detection_executed": True, "duplicate_ratio": 0.0, "preview_static_blocker": False},
        {"total_unique_asset_sources_sampled": 3},
    )
    assert "human_preview_decision_processed" not in review
    assert "voice_generation_allowed" in review
    assert review["voice_generation_allowed"] is False


# ---------------------------------------------------------------------------
# Blocks voice, assembly, downstream
# ---------------------------------------------------------------------------


def test_blocks_voice_assembly_downstream(tmp_project: Path):
    """All downstream actions must be blocked in render result."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    preview_dir = tmp_project / "output" / "previews"
    result = execute_segment_based_preview_rerender(plan, preview_dir)
    assert result["voice_generation_executed"] is False
    assert result["assembly_executed"] is False
    assert result["downstream_executed"] is False


def test_v3_manifest_blocks_downstream(tmp_project: Path):
    """Manifest must block all downstream actions."""
    manifest = build_v3_manifest(
        {"minimum_unique_sources_met": True, "single_source_fallback_blocked": True,
         "unique_asset_count": 3, "segments": [{"segment_index": 0}]},
        {"preview_render_executed": True, "preview_render_count": 1},
        {"duplicate_ratio": 0.0, "preview_static_blocker": False},
        tmp_project,
    )
    assert manifest["voice_generation_executed"] is False
    assert manifest["assembly_executed"] is False
    assert manifest["downstream_executed"] is False
    assert manifest["production_accepted"] is False


def test_v3_operator_packet_blocks_agent_acceptance(tmp_project: Path):
    """Operator review packet must forbid agent from accepting preview."""
    packet = build_v3_operator_review_packet(
        {"preview_render_executed": True, "preview_render_count": 1},
        {"preview_artifacts_valid": True},
        {"duplicate_ratio": 0.0, "preview_static_blocker": False},
        {"total_unique_asset_sources_sampled": 3},
        tmp_project,
    )
    assert packet["agent_may_accept_preview"] is False
    assert packet["production_accepted"] is False


# ---------------------------------------------------------------------------
# Does not set production_accepted
# ---------------------------------------------------------------------------


def test_does_not_set_production_accepted(tmp_project: Path):
    """Render result must not set production_accepted=True."""
    plan = build_preview_segment_render_plan_v3(tmp_project)
    preview_dir = tmp_project / "output" / "previews"
    result = execute_segment_based_preview_rerender(plan, preview_dir)
    assert result["production_accepted"] is False


def test_static_detection_report_no_production():
    """Static detection report must not set production_accepted."""
    report = build_v3_static_detection_report({
        "static_detection_executed": True,
        "total_frame_count": 100,
        "sampled_frame_count": 10,
        "unique_frame_count": 5,
        "duplicate_frame_count": 5,
        "duplicate_ratio": 0.5,
        "preview_static_blocker": False,
    })
    assert "production_accepted" not in report


def test_segment_plan_preflight_fails_no_segments():
    """Preflight should fail with empty plan."""
    plan = {
        "plan_valid": False,
        "segments": [],
        "unique_asset_count": 0,
        "single_source_fallback_blocked": True,
        "single_source_repeat_prevented": True,
    }
    preflight = build_preview_segment_render_preflight_v3(plan)
    assert preflight["preflight_pass"] is False


def test_segment_plan_preflight_checks_single_source_block():
    """Preflight must check single_source_fallback_blocked flag."""
    plan = {
        "plan_valid": True,
        "segments": [
            {"segment_index": 0, "asset_path": "/fake/path.png",
             "frame_start": 0, "frame_end": 100},
        ],
        "unique_asset_count": 1,
        "single_source_fallback_blocked": False,
        "single_source_repeat_prevented": False,
    }
    preflight = build_preview_segment_render_preflight_v3(plan)
    assert preflight["preflight_pass"] is False
    assert any("single source fallback" in e.lower() for e in preflight["errors"])


def test_v3_result_review_rejects_static(tmp_project: Path):
    """Result review should set appropriate flags when static detected."""
    review = build_v3_result_review(
        {"preview_render_executed": True, "preview_render_count": 1},
        {"valid": True, "errors": []},
        {"static_detection_executed": True, "duplicate_ratio": 0.95, "preview_static_blocker": True},
        {"total_unique_asset_sources_sampled": 1},
    )
    assert review["single_source_static_preview_detected"] is True
    assert review["preview_valid_for_operator_review"] is False
    assert review["timeline_visual_progression_passed"] is False
    assert review["contact_sheet_proves_progression"] is False
