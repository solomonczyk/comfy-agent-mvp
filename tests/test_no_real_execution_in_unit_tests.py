"""CRASH-FIX1 regression tests — verify unit tests cannot trigger real execution.

These tests verify the safety guards added in CRASH-FIX1 are in place and
effective. They do **not** run ComfyUI, ffmpeg, TTS, or any production system.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from app.brief.models import CharacterDef, ProjectMeta
from app.pipeline import Pipeline, PipelineConfig
from app.reference.grid_generator import ReferenceGridGenerator


def test_reference_grid_generate_blocks_by_default() -> None:
    """ReferenceGridGenerator must refuse live submit unless explicitly enabled."""
    gen = ReferenceGridGenerator()
    assert gen.allow_live_submit is False

    char = CharacterDef(name="Test", visual_description="test")
    meta = ProjectMeta(
        title="T", fps=1, target_duration_sec=1.0, style_hint="", mood=""
    )
    with pytest.raises(RuntimeError, match="live ComfyUI submit is disabled"):
        gen.generate(char, meta, output_dir=Path("/tmp/test_grid"))


def test_pipeline_config_defaults_are_safe() -> None:
    """PipelineConfig defaults must not enable live reference generation."""
    config = PipelineConfig(
        lora_dir="test/loras",
        voice_map={},
        fallback_voice_id="tts_en_01",
    )
    assert config.use_reference_grid is False
    assert config.allow_live_reference_generation is False


def test_pipeline_run_does_not_call_comfyui_by_default(monkeypatch) -> None:
    """With default config, Pipeline.run() must never invoke ReferenceGridGenerator.generate."""
    from app.reference import grid_generator as gg_mod

    called = {"n": 0}

    def _trap(*args, **kwargs):
        called["n"] += 1
        raise AssertionError("ReferenceGridGenerator.generate was called unexpectedly")

    monkeypatch.setattr(gg_mod.ReferenceGridGenerator, "generate", _trap)

    brief = """
## Meta
title: Test
duration: 5

## Characters
- name: Hero
  visual: knight

## Scenes
- action: hero walks
"""
    config = PipelineConfig(
        lora_dir="test/loras",
        voice_map={},
        fallback_voice_id="tts_en_01",
    )
    pipeline = Pipeline(config)
    result = pipeline.run(brief)
    assert called["n"] == 0
    assert result.title == "Test"


def test_video_qc_real_export_skips_without_env_var(tmp_path) -> None:
    """_real_export must skip unless RUN_REAL_FFMPEG_TESTS=1 is set."""
    import importlib
    test_video_qc = importlib.import_module("test_video_qc")
    _real_export = test_video_qc._real_export

    processed_dir = tmp_path / "processed"
    processed_dir.mkdir()
    export_path = tmp_path / "export.mp4"

    # Ensure env var is absent
    with patch.dict(os.environ, {}, clear=False):
        # Explicitly remove it if present
        env = os.environ.copy()
        env.pop("RUN_REAL_FFMPEG_TESTS", None)
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(pytest.skip.Exception, match="real ffmpeg tests disabled"):
                _real_export(processed_dir, export_path)
