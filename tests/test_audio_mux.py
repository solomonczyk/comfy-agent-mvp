"""Tests for SceneAudioMuxer."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.audio.mux import SceneAudioMuxer


def _make_fake_mp4(path: Path) -> Path:
    path.write_bytes(b"\x00" * 128)
    return path


def _make_fake_wav(path: Path) -> Path:
    path.write_bytes(b"\x00" * 64)
    return path


@pytest.fixture
def muxer() -> SceneAudioMuxer:
    return SceneAudioMuxer()


# ── missing input guards ─────────────────────────────────────────────────────


def test_missing_video_raises(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    wav = _make_fake_wav(tmp_path / "s01.wav")
    out = tmp_path / "s01_with_audio.mp4"
    with pytest.raises(RuntimeError, match="video not found"):
        muxer.mux(tmp_path / "missing.mp4", wav, out)


def test_missing_audio_raises(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    mp4 = _make_fake_mp4(tmp_path / "s01.mp4")
    out = tmp_path / "s01_with_audio.mp4"
    with pytest.raises(RuntimeError, match="audio not found"):
        muxer.mux(mp4, tmp_path / "missing.wav", out)


# ── ffmpeg success path ──────────────────────────────────────────────────────


def test_mux_returns_output_path(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    mp4 = _make_fake_mp4(tmp_path / "s01.mp4")
    wav = _make_fake_wav(tmp_path / "s01.wav")
    out = tmp_path / "s01_with_audio.mp4"

    fake_result = MagicMock()
    fake_result.returncode = 0

    with patch("subprocess.run", return_value=fake_result):
        out.write_bytes(b"\x00" * 256)
        result = muxer.mux(mp4, wav, out)

    assert result == out


def test_mux_output_file_exists(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    mp4 = _make_fake_mp4(tmp_path / "s01.mp4")
    wav = _make_fake_wav(tmp_path / "s01.wav")
    out = tmp_path / "s01_with_audio.mp4"

    fake_result = MagicMock()
    fake_result.returncode = 0

    with patch("subprocess.run", return_value=fake_result):
        out.write_bytes(b"\x00" * 256)
        muxer.mux(mp4, wav, out)

    assert out.exists()


# ── ffmpeg failure ────────────────────────────────────────────────────────────


def test_ffmpeg_nonzero_raises_runtime_error(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    mp4 = _make_fake_mp4(tmp_path / "s01.mp4")
    wav = _make_fake_wav(tmp_path / "s01.wav")
    out = tmp_path / "s01_with_audio.mp4"

    fake_result = MagicMock()
    fake_result.returncode = 1
    fake_result.stderr = "some ffmpeg error"

    with patch("subprocess.run", return_value=fake_result):
        with pytest.raises(RuntimeError, match="ffmpeg failed"):
            muxer.mux(mp4, wav, out)


def test_ffmpeg_command_shape(tmp_path: Path, muxer: SceneAudioMuxer) -> None:
    mp4 = _make_fake_mp4(tmp_path / "s01.mp4")
    wav = _make_fake_wav(tmp_path / "s01.wav")
    out = tmp_path / "s01_with_audio.mp4"

    fake_result = MagicMock()
    fake_result.returncode = 0

    with patch("subprocess.run", return_value=fake_result) as mock_run:
        out.write_bytes(b"\x00" * 256)
        muxer.mux(mp4, wav, out)

    cmd = mock_run.call_args[0][0]
    assert cmd[0] == "ffmpeg"
    assert "-c:v" in cmd
    assert "copy" in cmd
    assert "-c:a" in cmd
    assert "aac" in cmd
    assert "-shortest" in cmd
