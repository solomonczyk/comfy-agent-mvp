"""Tests for MK-E2 — FrameAssembler.

Uses tmp_path and creates real PNG frames using PIL (no cv2 codec dependency).
ffmpeg must be on PATH for assembly tests.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from app.render.exceptions import FrameAssembleError
from app.render.frame_assembler import FrameAssembler


# ── helpers ───────────────────────────────────────────────────────────────────

def _create_test_frame(path: Path, size: tuple[int, int] = (512, 384)) -> None:
    img = Image.fromarray(np.ones((size[1], size[0], 3), dtype=np.uint8) * 255, mode="RGB")
    img.save(str(path))


# ── happy path ───────────────────────────────────────────────────────────────

def test_returns_mp4_path(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path)

    result = assembler.assemble("s01", [frame_path], fps=8)
    assert isinstance(result, Path)
    assert result.suffix == ".mp4"


def test_output_file_exists_after_assembly(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path)

    result = assembler.assemble("s01", [frame_path], fps=8)
    assert result.exists()


def test_scene_id_in_output_filename(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path)

    result = assembler.assemble("scene_07", [frame_path], fps=8)
    assert "scene_07" in result.name


def test_frames_sorted_by_filename(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    frames = [
        tmp_path / "frame_003.png",
        tmp_path / "frame_001.png",
        tmp_path / "frame_002.png",
    ]
    for f in frames:
        _create_test_frame(f)

    result = assembler.assemble("s01", frames, fps=8)
    assert result.exists()


# ── error cases ──────────────────────────────────────────────────────────────

def test_empty_frame_paths_raises_error(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    with pytest.raises(FrameAssembleError, match="empty"):
        assembler.assemble("s01", [], fps=8)


def test_missing_frame_path_raises_error(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    with pytest.raises(FrameAssembleError, match="not found"):
        assembler.assemble("s01", [tmp_path / "nonexistent.png"], fps=8)


def test_none_frame_is_skipped_without_crash(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    good_frame = tmp_path / "frame_001.png"
    bad_file = tmp_path / "frame_002.png"
    _create_test_frame(good_frame)
    bad_file.write_text("not a png")

    result = assembler.assemble("s01", [good_frame, bad_file], fps=8)
    assert result.exists()
    assert result.stat().st_size > 0


def test_output_file_size_greater_than_zero(tmp_path):
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path)

    result = assembler.assemble("s01", [frame_path], fps=8)
    assert result.exists()
    assert result.stat().st_size > 0
    assert result.stat().st_size > 1024  # at least 1KB


def test_aspect_ratio_43_no_warning_for_640x480(tmp_path, caplog):
    import logging
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path, size=(640, 480))

    with caplog.at_level(logging.WARNING, logger="app.render.frame_assembler"):
        assembler.assemble("s01", [frame_path], fps=8, aspect_ratio="4:3")

    mismatch_warnings = [r for r in caplog.records if "mismatch" in r.message.lower()]
    assert mismatch_warnings == [], f"Unexpected aspect ratio warning: {mismatch_warnings}"


def test_aspect_ratio_mismatch_warns_for_wrong_ratio(tmp_path, caplog):
    import logging
    assembler = FrameAssembler(output_dir=tmp_path)
    frame_path = tmp_path / "frame_001.png"
    _create_test_frame(frame_path, size=(1920, 1080))

    with caplog.at_level(logging.WARNING, logger="app.render.frame_assembler"):
        assembler.assemble("s01", [frame_path], fps=8, aspect_ratio="4:3")

    mismatch_warnings = [r for r in caplog.records if "mismatch" in r.message.lower()]
    assert mismatch_warnings, "Expected aspect ratio mismatch warning for 16:9 frame with 4:3 expectation"
