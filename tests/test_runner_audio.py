"""Tests for ExecutionRunner audio integration."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from app.pipeline import PipelineConfig
from app.scenes.models import BuiltScene

_DUMMY_VOICE_MAP = {
    "tts_ru_01": {"engine": "silero", "lang": "ru", "speaker": "aidar", "sample_rate": 48000},
}


def _make_config() -> PipelineConfig:
    return PipelineConfig(
        lora_dir="/tmp/loras",
        voice_map=_DUMMY_VOICE_MAP,
        fallback_voice_id="tts_ru_01",
    )


def _make_scene(
    scene_id: str = "s01",
    dialogue: str | None = "Привет",
    voice_ids: list[str] | None = None,
) -> BuiltScene:
    return BuiltScene(
        scene_id=scene_id,
        positive_prompt="a portrait",
        negative_prompt="bad",
        lora_stack=[],
        voice_ids=voice_ids if voice_ids is not None else ["tts_ru_01"],
        total_frames=8,
        duration_sec=1.0,
        fps=8,
        dialogue=dialogue,
    )


def _make_submit_result(scene_id: str, frame_paths: list[Path]) -> MagicMock:
    r = MagicMock()
    r.scene_id = scene_id
    r.frame_paths = frame_paths
    return r


def _make_episode(scenes: list[BuiltScene]) -> MagicMock:
    ep = MagicMock()
    ep.title = "test_episode"
    ep.scenes = scenes
    ep.aspect_ratio = "4:3"
    ep.reference_paths = {}
    return ep


# ── scene with dialogue triggers synth + mux ────────────────────────────────


def test_scene_with_dialogue_triggers_synth_and_mux(tmp_path: Path) -> None:
    scene = _make_scene(dialogue="Привет", voice_ids=["tts_ru_01"])
    episode = _make_episode([scene])
    mp4 = tmp_path / "s01.mp4"
    mp4.write_bytes(b"\x00" * 64)
    wav = tmp_path / "audio" / "s01.wav"
    muxed = tmp_path / "s01_with_audio.mp4"
    submit_result = _make_submit_result("s01", [mp4])

    with (
        patch("app.runner.Pipeline") as mock_pipeline_cls,
        patch("app.runner.ComfySubmitter") as mock_submitter_cls,
        patch("app.runner.FrameAssembler") as mock_assembler_cls,
        patch("app.runner.EpisodeRenderer") as mock_renderer_cls,
        patch("app.runner.SceneAudioBuilder") as mock_audio_cls,
        patch("app.runner.SceneAudioMuxer") as mock_muxer_cls,
    ):
        mock_pipeline_cls.return_value.run.return_value = episode
        mock_submitter = mock_submitter_cls.return_value
        mock_submitter.submit.return_value = submit_result
        mock_assembler_cls.return_value.assemble.return_value = mp4
        mock_renderer_cls.return_value.render.return_value = tmp_path / "episode.mp4"
        mock_audio_builder = mock_audio_cls.return_value
        mock_audio_builder.synthesize_scene.return_value = wav
        mock_muxer = mock_muxer_cls.return_value
        mock_muxer.mux.return_value = muxed

        from app.runner import ExecutionRunner

        runner = ExecutionRunner(_make_config(), workflow_template={})
        runner.run("brief.md", output_dir=tmp_path)

    mock_audio_builder.synthesize_scene.assert_called_once()
    mock_muxer.mux.assert_called_once()


# ── scene without dialogue skips audio ──────────────────────────────────────


def test_scene_without_dialogue_skips_audio(tmp_path: Path) -> None:
    scene = _make_scene(dialogue=None, voice_ids=["tts_ru_01"])
    episode = _make_episode([scene])
    mp4 = tmp_path / "s01.mp4"
    mp4.write_bytes(b"\x00" * 64)
    submit_result = _make_submit_result("s01", [mp4])

    with (
        patch("app.runner.Pipeline") as mock_pipeline_cls,
        patch("app.runner.ComfySubmitter") as mock_submitter_cls,
        patch("app.runner.FrameAssembler") as mock_assembler_cls,
        patch("app.runner.EpisodeRenderer") as mock_renderer_cls,
        patch("app.runner.SceneAudioBuilder") as mock_audio_cls,
        patch("app.runner.SceneAudioMuxer") as mock_muxer_cls,
    ):
        mock_pipeline_cls.return_value.run.return_value = episode
        mock_submitter_cls.return_value.submit.return_value = submit_result
        mock_assembler_cls.return_value.assemble.return_value = mp4
        mock_renderer_cls.return_value.render.return_value = tmp_path / "episode.mp4"
        mock_audio_builder = mock_audio_cls.return_value
        mock_audio_builder.synthesize_scene.return_value = None
        mock_muxer = mock_muxer_cls.return_value

        from app.runner import ExecutionRunner

        runner = ExecutionRunner(_make_config(), workflow_template={})
        runner.run("brief.md", output_dir=tmp_path)

    mock_muxer.mux.assert_not_called()


# ── final render is still called ─────────────────────────────────────────────


def test_final_render_always_called(tmp_path: Path) -> None:
    scene = _make_scene(dialogue=None, voice_ids=[])
    episode = _make_episode([scene])
    mp4 = tmp_path / "s01.mp4"
    mp4.write_bytes(b"\x00" * 64)
    submit_result = _make_submit_result("s01", [mp4])

    with (
        patch("app.runner.Pipeline") as mock_pipeline_cls,
        patch("app.runner.ComfySubmitter") as mock_submitter_cls,
        patch("app.runner.FrameAssembler") as mock_assembler_cls,
        patch("app.runner.EpisodeRenderer") as mock_renderer_cls,
        patch("app.runner.SceneAudioBuilder") as mock_audio_cls,
        patch("app.runner.SceneAudioMuxer"),
    ):
        mock_pipeline_cls.return_value.run.return_value = episode
        mock_submitter_cls.return_value.submit.return_value = submit_result
        mock_assembler_cls.return_value.assemble.return_value = mp4
        mock_renderer = mock_renderer_cls.return_value
        mock_renderer.render.return_value = tmp_path / "episode.mp4"
        mock_audio_cls.return_value.synthesize_scene.return_value = None

        from app.runner import ExecutionRunner

        runner = ExecutionRunner(_make_config(), workflow_template={})
        runner.run("brief.md", output_dir=tmp_path)

    mock_renderer.render.assert_called_once()


# ── mixed scenes (one audio, one silent) ─────────────────────────────────────


def test_mixed_scenes_succeed(tmp_path: Path) -> None:
    s1 = _make_scene(scene_id="s01", dialogue="Привет", voice_ids=["tts_ru_01"])
    s2 = _make_scene(scene_id="s02", dialogue=None, voice_ids=[])
    episode = _make_episode([s1, s2])
    mp4_s1 = tmp_path / "s01.mp4"
    mp4_s2 = tmp_path / "s02.mp4"
    for p in [mp4_s1, mp4_s2]:
        p.write_bytes(b"\x00" * 64)
    wav_s1 = tmp_path / "audio" / "s01.wav"
    muxed_s1 = tmp_path / "s01_with_audio.mp4"

    with (
        patch("app.runner.Pipeline") as mock_pipeline_cls,
        patch("app.runner.ComfySubmitter") as mock_submitter_cls,
        patch("app.runner.FrameAssembler") as mock_assembler_cls,
        patch("app.runner.EpisodeRenderer") as mock_renderer_cls,
        patch("app.runner.SceneAudioBuilder") as mock_audio_cls,
        patch("app.runner.SceneAudioMuxer") as mock_muxer_cls,
    ):
        mock_pipeline_cls.return_value.run.return_value = episode
        submit_s1 = _make_submit_result("s01", [mp4_s1])
        submit_s2 = _make_submit_result("s02", [mp4_s2])
        mock_submitter_cls.return_value.submit.side_effect = [submit_s1, submit_s2]
        mock_assembler_cls.return_value.assemble.side_effect = [mp4_s1, mp4_s2]
        mock_renderer = mock_renderer_cls.return_value
        mock_renderer.render.return_value = tmp_path / "episode.mp4"
        mock_audio_builder = mock_audio_cls.return_value
        mock_audio_builder.synthesize_scene.side_effect = [wav_s1, None]
        mock_muxer = mock_muxer_cls.return_value
        mock_muxer.mux.return_value = muxed_s1

        from app.runner import ExecutionRunner

        runner = ExecutionRunner(_make_config(), workflow_template={})
        runner.run("brief.md", output_dir=tmp_path)

    assert mock_audio_builder.synthesize_scene.call_count == 2
    mock_muxer.mux.assert_called_once()
    mock_renderer.render.assert_called_once()
    render_mp4s = mock_renderer.render.call_args[0][1]
    assert muxed_s1 in render_mp4s
    assert mp4_s2 in render_mp4s


# ── TTS failure stops run ─────────────────────────────────────────────────────


def test_tts_failure_reraises_and_stops_run(tmp_path: Path) -> None:
    scene = _make_scene(dialogue="Привет", voice_ids=["tts_ru_01"])
    episode = _make_episode([scene])
    mp4 = tmp_path / "s01.mp4"
    mp4.write_bytes(b"\x00" * 64)
    submit_result = _make_submit_result("s01", [mp4])

    with (
        patch("app.runner.Pipeline") as mock_pipeline_cls,
        patch("app.runner.ComfySubmitter") as mock_submitter_cls,
        patch("app.runner.FrameAssembler") as mock_assembler_cls,
        patch("app.runner.EpisodeRenderer") as mock_renderer_cls,
        patch("app.runner.SceneAudioBuilder") as mock_audio_cls,
        patch("app.runner.SceneAudioMuxer"),
    ):
        mock_pipeline_cls.return_value.run.return_value = episode
        mock_submitter_cls.return_value.submit.return_value = submit_result
        mock_assembler_cls.return_value.assemble.return_value = mp4
        mock_renderer = mock_renderer_cls.return_value
        mock_audio_cls.return_value.synthesize_scene.side_effect = RuntimeError(
            "TTS synthesis failed for scene 's01'"
        )

        from app.runner import ExecutionRunner

        runner = ExecutionRunner(_make_config(), workflow_template={})

        with pytest.raises(RuntimeError, match="TTS synthesis failed"):
            runner.run("brief.md", output_dir=tmp_path)

    mock_renderer.render.assert_not_called()
