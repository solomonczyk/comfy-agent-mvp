"""Tests for MK-F1 — ExecutionRunner.

All external dependencies (ComfySubmitter, FrameAssembler, EpisodeRenderer, Pipeline) are mocked.
"""
from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.comfy.exceptions import ComfySubmitError, ComfyTimeoutError
from app.comfy.models import SubmitResult
from app.pipeline import PipelineConfig
from app.runner import ExecutionRunner


# ── helpers ───────────────────────────────────────────────────────────────────

def _config():
    return PipelineConfig(
        lora_dir="test/loras",
        voice_map={"tts_ru_01": {"engine": "coqui", "lang": "ru"}},
        fallback_voice_id="tts_en_01",
    )


def _workflow_template():
    return {"__inject__": {"positive_prompt_node": "6"}, "6": {"inputs": {"text": ""}}}


def _brief_text():
    return """
## Meta
title: Test
duration: 5

## Characters
- name: Hero
  visual: knight

## Scenes
- action: hero walks
"""


# ── happy path ───────────────────────────────────────────────────────────────

@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.FrameAssembler")
@patch("app.runner.EpisodeRenderer")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_run_returns_path(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_renderer, mock_assembler, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="TestEpisode",
        scenes=[Mock(scene_id="s01", fps=8, total_frames=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_submitter.return_value.submit.return_value = SubmitResult(
        prompt_id="x",
        scene_id="s01",
        frame_paths=[Path("frame1.png")],
        elapsed_sec=1.0,
    )
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")
    mock_assembler.return_value.assemble.return_value = Path("s01.mp4")
    mock_renderer.return_value.render.return_value = Path("TestEpisode_20250101.mp4")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    result = runner.run(_brief_text())

    assert isinstance(result, Path)


@patch("app.runner.Pipeline")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_pipeline_run_called_once(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    with patch("app.runner.ComfySubmitter") as mock_submitter:
        mock_submitter.return_value.submit.return_value = SubmitResult(
            prompt_id="x",
            scene_id="s01",
            frame_paths=[],
            elapsed_sec=1.0,
        )
        with patch("app.runner.FrameAssembler"), patch("app.runner.EpisodeRenderer"):
            runner.run(_brief_text())

    mock_pipeline.return_value.run.assert_called_once()


@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.FrameAssembler")
@patch("app.runner.EpisodeRenderer")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_submitter_called_per_scene(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_renderer, mock_assembler, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_episode = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"]), Mock(scene_id="s02", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_pipeline.return_value.run.return_value = mock_episode
    mock_submitter.return_value.submit.return_value = SubmitResult(
        prompt_id="x",
        scene_id="s01",
        frame_paths=[],
        elapsed_sec=1.0,
    )
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    runner.run(_brief_text())

    assert mock_submitter.return_value.submit.call_count == 2


@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.FrameAssembler")
@patch("app.runner.EpisodeRenderer")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_assembler_called_per_scene(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_renderer, mock_assembler, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_episode = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"]), Mock(scene_id="s02", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_pipeline.return_value.run.return_value = mock_episode
    mock_submitter.return_value.submit.side_effect = [
        SubmitResult("x", "s01", [], 1.0),
        SubmitResult("y", "s02", [], 1.0),
    ]
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    runner.run(_brief_text())

    assert mock_assembler.return_value.assemble.call_count == 2


@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.FrameAssembler")
@patch("app.runner.EpisodeRenderer")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_renderer_called_once(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_renderer, mock_assembler, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_submitter.return_value.submit.return_value = SubmitResult(
        prompt_id="x",
        scene_id="s01",
        frame_paths=[],
        elapsed_sec=1.0,
    )
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")
    mock_assembler.return_value.assemble.return_value = Path("s01.mp4")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    runner.run(_brief_text())

    mock_renderer.return_value.render.assert_called_once()


# ── error cases ───────────────────────────────────────────────────────────────

@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_timeout_error_raised(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_submitter.return_value.submit.side_effect = ComfyTimeoutError("Timeout")
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    with patch("app.runner.FrameAssembler"), patch("app.runner.EpisodeRenderer"):
        with pytest.raises(ComfyTimeoutError, match="Timeout"):
            runner.run(_brief_text())


@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_submit_error_raised(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="Test",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_submitter.return_value.submit.side_effect = ComfySubmitError("HTTP 500")
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    with patch("app.runner.FrameAssembler"), patch("app.runner.EpisodeRenderer"):
        with pytest.raises(ComfySubmitError, match="HTTP 500"):
            runner.run(_brief_text())


@patch("app.runner.Pipeline")
@patch("app.runner.ComfySubmitter")
@patch("app.runner.FrameAssembler")
@patch("app.runner.EpisodeRenderer")
@patch("app.runner.SceneAudioBuilder")
@patch("app.audio.mux.subprocess")
@patch("pathlib.Path.exists")
@patch("pathlib.Path.stat")
def test_brief_example_md_completes(mock_stat, mock_exists, mock_subprocess, mock_audio, mock_renderer, mock_assembler, mock_submitter, mock_pipeline):
    mock_exists.return_value = True
    mock_stat.return_value.st_size = 1000
    mock_stat.return_value.st_mode = 16877  # S_IFDIR | 0755
    mock_subprocess.run.return_value = Mock(returncode=0, stderr="")
    mock_pipeline.return_value.run.return_value = Mock(
        title="Кот и луна",
        scenes=[Mock(scene_id="s01", fps=8, characters_in_scene=[], voice_ids=["tts_en_01"])],
        aspect_ratio="4:3",
    )
    mock_submitter.return_value.submit.return_value = SubmitResult(
        prompt_id="x",
        scene_id="s01",
        frame_paths=[],
        elapsed_sec=1.0,
    )
    mock_audio.return_value.synthesize_scene.return_value = Path("s01.wav")
    mock_assembler.return_value.assemble.return_value = Path("s01.mp4")
    mock_renderer.return_value.render.return_value = Path("final.mp4")

    with open("data/brief_example.md", encoding="utf-8") as f:
        brief_text = f.read()

    runner = ExecutionRunner(config=_config(), workflow_template=_workflow_template())
    result = runner.run(brief_text)

    assert isinstance(result, Path)
