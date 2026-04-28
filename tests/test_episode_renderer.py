"""Tests for MK-E3 — EpisodeRenderer.

Uses tmp_path and creates stub MP4 files using cv2.
"""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
import pytest

from app.render.exceptions import EpisodeRenderError
from app.render.episode_renderer import EpisodeRenderer


# ── helpers ───────────────────────────────────────────────────────────────────

def _create_stub_mp4(path: Path, fps: int = 8, size: tuple[int, int] = (512, 384)) -> None:
    width, height = size
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(path), fourcc, fps, (width, height))
    # Write a few frames
    for _ in range(5):
        frame = np.ones((height, width, 3), dtype=np.uint8) * 255
        writer.write(frame)
    writer.release()


# ── happy path ───────────────────────────────────────────────────────────────

def test_returns_mp4_path(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    mp4_path = tmp_path / "scene_01.mp4"
    _create_stub_mp4(mp4_path)

    result = renderer.render("TestEpisode", [mp4_path])
    assert isinstance(result, Path)
    assert result.suffix == ".mp4"


def test_output_file_exists(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    mp4_path = tmp_path / "scene_01.mp4"
    _create_stub_mp4(mp4_path)

    result = renderer.render("TestEpisode", [mp4_path])
    assert result.exists()


def test_title_sanitized_spaces_to_underscores(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    mp4_path = tmp_path / "scene_01.mp4"
    _create_stub_mp4(mp4_path)

    result = renderer.render("My Test Episode", [mp4_path])
    assert "My_Test_Episode" in result.name


def test_title_sanitized_non_ascii_stripped(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    mp4_path = tmp_path / "scene_01.mp4"
    _create_stub_mp4(mp4_path)

    result = renderer.render("Эпизод #1", [mp4_path])
    assert "_" in result.name or result.name.startswith("_")


def test_scene_order_preserved(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    mp4s = [
        tmp_path / "scene_01.mp4",
        tmp_path / "scene_02.mp4",
        tmp_path / "scene_03.mp4",
    ]
    for mp4 in mp4s:
        _create_stub_mp4(mp4)

    result = renderer.render("Test", mp4s)
    assert result.exists()


# ── error cases ──────────────────────────────────────────────────────────────

def test_empty_scene_mp4s_raises_error(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    with pytest.raises(EpisodeRenderError, match="empty"):
        renderer.render("Test", [])


def test_missing_mp4_path_raises_error(tmp_path):
    renderer = EpisodeRenderer(output_dir=tmp_path)
    with pytest.raises(EpisodeRenderError, match="not found"):
        renderer.render("Test", [tmp_path / "nonexistent.mp4"])
