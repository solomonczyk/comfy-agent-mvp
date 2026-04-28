"""Tests for MK-P7 — Pipeline.

Coverage:
  - Pipeline.run() returns Episode
  - end-to-end with brief_example.md from data/ — no exceptions
  - Episode.title matches brief title
  - Episode.scenes count matches brief scenes count
  - character with known voice_id → voice_ids non-empty in relevant scene
  - missing lora → warning raised, pipeline does not crash
  - idempotent
"""
from __future__ import annotations

import warnings
from pathlib import Path
from unittest.mock import patch

import pytest

from app.pipeline import Pipeline, PipelineConfig
from app.episode.models import Episode


# ── helpers ───────────────────────────────────────────────────────────────────

DEFAULT_CONFIG = PipelineConfig(
    lora_dir="F:\\ComfyUI\\models\\loras",
    voice_map={
        "tts_ru_01": {"engine": "coqui", "lang": "ru", "speed": 1.0, "pitch": 1.0},
        "tts_en_01": {"engine": "edge-tts", "lang": "en", "speed": 1.0, "pitch": 1.0},
    },
    fallback_voice_id="tts_en_01",
    use_reference_grid=False,
)


# ── return type ───────────────────────────────────────────────────────────────

def test_pipeline_run_returns_episode():
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
    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief)
    assert isinstance(result, Episode)


# ── end-to-end with brief_example.md ───────────────────────────────────────────

def test_end_to_end_brief_example_md_no_exceptions():
    brief_path = "data/brief_example.md"
    with open(brief_path, encoding="utf-8") as f:
        brief_text = f.read()

    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief_text)
    assert isinstance(result, Episode)
    assert result.title == "Кот и луна"


# ── episode fields ───────────────────────────────────────────────────────────

def test_episode_title_matches_brief():
    brief = """
## Meta
title: My Episode
duration: 10

## Characters
- name: A
  visual: hero

## Scenes
- action: test
"""
    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief)
    assert result.title == "My Episode"


def test_episode_scenes_count_matches_brief():
    brief = """
## Meta
title: Test
duration: 10

## Characters
- name: A
  visual: hero

## Scenes
- action: scene 1
- action: scene 2
- action: scene 3
"""
    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief)
    assert len(result.scenes) == 3


# ── voice resolution ─────────────────────────────────────────────────────────

def test_known_voice_id_in_scene():
    brief = """
## Meta
title: Test
duration: 5

## Characters
- name: Hero
  visual: knight
  voice_id: tts_ru_01

## Scenes
- characters: Hero
  action: hero speaks
"""
    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief)
    assert "tts_ru_01" in result.scenes[0].voice_ids


# ── missing lora warning ──────────────────────────────────────────────────────

def test_missing_lora_warning_raised_pipeline_continues():
    brief = """
## Meta
title: Test
duration: 5

## Characters
- name: Hero
  visual: knight
  lora: missing_lora.safetensors

## Scenes
- characters: Hero
  action: hero walks
"""
    pipeline = Pipeline(DEFAULT_CONFIG)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = pipeline.run(brief)
    from app.characters.resolver import CharacterResolveWarning
    assert any(issubclass(x.category, CharacterResolveWarning) for x in w)
    assert isinstance(result, Episode)


# ── idempotency ───────────────────────────────────────────────────────────────

def test_pipeline_idempotent():
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
    pipeline = Pipeline(DEFAULT_CONFIG)
    e1 = pipeline.run(brief)
    e2 = pipeline.run(brief)
    assert e1.title == e2.title
    assert len(e1.scenes) == len(e2.scenes)


# ── real execution guards ──────────────────────────────────────────────────────

def test_pipeline_does_not_generate_reference_grid_by_default(monkeypatch):
    """By default Pipeline.run() must never call ReferenceGridGenerator.generate."""
    from app.reference import grid_generator

    original_generate = grid_generator.ReferenceGridGenerator.generate

    def _assertion_fail(*args, **kwargs):
        raise AssertionError(
            "ReferenceGridGenerator.generate() was called unexpectedly — "
            "unit tests must not trigger live ComfyUI submission."
        )

    monkeypatch.setattr(grid_generator.ReferenceGridGenerator, "generate", _assertion_fail)

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
    pipeline = Pipeline(DEFAULT_CONFIG)
    result = pipeline.run(brief)
    assert isinstance(result, Episode)
    # restore for other tests that mock differently
    monkeypatch.setattr(grid_generator.ReferenceGridGenerator, "generate", original_generate)


def test_reference_grid_requires_double_opt_in(monkeypatch):
    """use_reference_grid=True alone must not call generate(); allow_live_reference_generation is also required."""
    from app.reference import grid_generator

    original_generate = grid_generator.ReferenceGridGenerator.generate

    def _assertion_fail(*args, **kwargs):
        raise AssertionError(
            "ReferenceGridGenerator.generate() was called with only single opt-in — "
            "double opt-in (allow_live_reference_generation=True) is required."
        )

    monkeypatch.setattr(grid_generator.ReferenceGridGenerator, "generate", _assertion_fail)

    config = PipelineConfig(
        lora_dir="F:\\ComfyUI\\models\\loras",
        voice_map={
            "tts_ru_01": {"engine": "coqui", "lang": "ru", "speed": 1.0, "pitch": 1.0},
            "tts_en_01": {"engine": "edge-tts", "lang": "en", "speed": 1.0, "pitch": 1.0},
        },
        fallback_voice_id="tts_en_01",
        use_reference_grid=True,
        allow_live_reference_generation=False,
    )

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
    pipeline = Pipeline(config)
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        result = pipeline.run(brief)
    assert isinstance(result, Episode)
    assert any("live reference generation disabled" in str(warning.message) for warning in w)
    monkeypatch.setattr(grid_generator.ReferenceGridGenerator, "generate", original_generate)
