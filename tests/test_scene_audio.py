"""Tests for SceneAudioBuilder."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.audio.scene_audio import SceneAudioBuilder
from app.scenes.models import BuiltScene


def _make_scene(
    scene_id: str = "s01",
    dialogue: str | None = "Привет мир",
    voice_ids: list[str] | None = None,
) -> BuiltScene:
    return BuiltScene(
        scene_id=scene_id,
        positive_prompt="test",
        negative_prompt="bad",
        lora_stack=[],
        voice_ids=voice_ids if voice_ids is not None else ["tts_ru_01"],
        total_frames=8,
        duration_sec=1.0,
        fps=8,
        dialogue=dialogue,
    )


_DUMMY_VOICE_MAP = {
    "tts_ru_01": {"engine": "silero", "lang": "ru", "speaker": "aidar", "sample_rate": 48000},
    "tts_en_01": {"engine": "kokoro", "lang": "en", "speaker": "af_heart", "sample_rate": 24000},
}


def _builder() -> SceneAudioBuilder:
    return SceneAudioBuilder(voice_map=_DUMMY_VOICE_MAP, fallback_voice_id="tts_ru_01")


# ── no audio cases ──────────────────────────────────────────────────────────


def test_no_dialogue_returns_none(tmp_path: Path) -> None:
    builder = _builder()
    scene = _make_scene(dialogue=None)
    result = builder.synthesize_scene(scene, output_dir=tmp_path)
    assert result is None


def test_empty_dialogue_returns_none(tmp_path: Path) -> None:
    builder = _builder()
    scene = _make_scene(dialogue="   ")
    result = builder.synthesize_scene(scene, output_dir=tmp_path)
    assert result is None


def test_no_voice_ids_returns_none(tmp_path: Path) -> None:
    builder = _builder()
    scene = _make_scene(dialogue="Hello", voice_ids=[])
    result = builder.synthesize_scene(scene, output_dir=tmp_path)
    assert result is None


# ── synthesis path ───────────────────────────────────────────────────────────


def test_dialogue_and_voice_id_calls_resolver(tmp_path: Path) -> None:
    builder = _builder()
    expected_wav = tmp_path / "s01.wav"

    with patch.object(builder._resolver, "synthesize", return_value=expected_wav) as mock_synth:
        scene = _make_scene(dialogue="Привет мир", voice_ids=["tts_ru_01"])
        result = builder.synthesize_scene(scene, output_dir=tmp_path)

    mock_synth.assert_called_once_with(
        voice_id="tts_ru_01",
        text="Привет мир",
        output_path=tmp_path / "s01.wav",
    )
    assert result == expected_wav


def test_output_filename_uses_scene_id(tmp_path: Path) -> None:
    builder = _builder()
    expected_wav = tmp_path / "scene_abc.wav"

    with patch.object(builder._resolver, "synthesize", return_value=expected_wav):
        scene = _make_scene(scene_id="scene_abc", dialogue="test", voice_ids=["tts_ru_01"])
        result = builder.synthesize_scene(scene, output_dir=tmp_path)

    assert result is not None
    assert result.name == "scene_abc.wav"


def test_uses_first_voice_id_only(tmp_path: Path) -> None:
    builder = _builder()

    with patch.object(builder._resolver, "synthesize", return_value=tmp_path / "s01.wav") as mock_synth:
        scene = _make_scene(voice_ids=["tts_en_01", "tts_ru_01"])
        builder.synthesize_scene(scene, output_dir=tmp_path)

    assert mock_synth.call_args[1]["voice_id"] == "tts_en_01"


def test_tts_failure_raises_runtime_error(tmp_path: Path) -> None:
    builder = _builder()

    with patch.object(builder._resolver, "synthesize", side_effect=RuntimeError("model error")):
        scene = _make_scene(dialogue="test", voice_ids=["tts_ru_01"])
        with pytest.raises(RuntimeError, match="TTS synthesis failed"):
            builder.synthesize_scene(scene, output_dir=tmp_path)


def test_silero_route_via_engine(tmp_path: Path) -> None:
    builder = _builder()
    with patch.object(builder._resolver, "synthesize", return_value=tmp_path / "s01.wav") as mock_synth:
        scene = _make_scene(voice_ids=["tts_ru_01"])
        builder.synthesize_scene(scene, output_dir=tmp_path)

    voice_id_used = mock_synth.call_args[1]["voice_id"]
    voice_entry = _DUMMY_VOICE_MAP[voice_id_used]
    assert voice_entry["engine"] == "silero"


def test_kokoro_route_via_engine(tmp_path: Path) -> None:
    builder = _builder()
    with patch.object(builder._resolver, "synthesize", return_value=tmp_path / "s01.wav") as mock_synth:
        scene = _make_scene(voice_ids=["tts_en_01"])
        builder.synthesize_scene(scene, output_dir=tmp_path)

    voice_id_used = mock_synth.call_args[1]["voice_id"]
    voice_entry = _DUMMY_VOICE_MAP[voice_id_used]
    assert voice_entry["engine"] == "kokoro"
