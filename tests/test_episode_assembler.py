"""Tests for MK-P6 — EpisodeAssembler.

Coverage:
  - returns Episode
  - total_duration_sec equals sum of scene durations
  - total_frames equals sum of scene frames
  - fps and aspect_ratio from brief meta
  - scene order preserved
  - to_dict() is JSON-serializable
  - single scene episode works
  - idempotent
"""
from __future__ import annotations

import json

import pytest

from app.brief.models import BriefModel, CharacterDef, ProjectMeta, SceneDef
from app.episode.assembler import EpisodeAssembler
from app.episode.models import Episode
from app.scenes.models import BuiltScene


# ── helpers ───────────────────────────────────────────────────────────────────

def _built_scene(
    scene_id: str = "s01",
    duration: float = 3.0,
    frames: int = 24,
) -> BuiltScene:
    return BuiltScene(
        scene_id=scene_id,
        positive_prompt="test prompt",
        negative_prompt="blurry",
        lora_stack=[],
        voice_ids=[],
        total_frames=frames,
        duration_sec=duration,
        fps=8,
        keyframe_hints=["a", "b"],
        location="forest",
        dialogue=None,
    )


def _brief(title: str = "Test", fps: int = 8, ar: str = "4:3") -> BriefModel:
    return BriefModel(
        meta=ProjectMeta(title=title, target_duration_sec=10.0, fps=fps, aspect_ratio=ar),
        characters=[CharacterDef(name="A", visual_description="desc")],
        scenes=[SceneDef(scene_id="s01", characters_in_scene=[], action="test")],
    )


# ── return type ───────────────────────────────────────────────────────────────

def test_returns_episode():
    brief = _brief()
    scenes = [_built_scene()]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert isinstance(result, Episode)


# ── aggregations ───────────────────────────────────────────────────────────────

def test_total_duration_sec_sum_of_scenes():
    brief = _brief()
    scenes = [_built_scene(duration=3.0), _built_scene(duration=2.5)]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert result.total_duration_sec == 5.5


def test_total_frames_sum_of_scenes():
    brief = _brief()
    scenes = [_built_scene(frames=24), _built_scene(frames=16)]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert result.total_frames == 40


def test_fps_from_brief_meta():
    brief = _brief(fps=24)
    scenes = [_built_scene()]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert result.fps == 24


def test_aspect_ratio_from_brief_meta():
    brief = _brief(ar="16:9")
    scenes = [_built_scene()]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert result.aspect_ratio == "16:9"


# ── scene order ───────────────────────────────────────────────────────────────

def test_scene_order_preserved():
    brief = _brief()
    scenes = [
        _built_scene("s01"),
        _built_scene("s02"),
        _built_scene("s03"),
    ]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert [s.scene_id for s in result.scenes] == ["s01", "s02", "s03"]


# ── serialization ─────────────────────────────────────────────────────────────

def test_to_dict_json_serializable():
    brief = _brief()
    scenes = [_built_scene()]
    episode = EpisodeAssembler().assemble(brief, scenes)
    d = episode.to_dict()
    serialised = json.dumps(d)
    assert len(serialised) > 0


def test_to_dict_contains_all_fields():
    brief = _brief(title="My Episode")
    scenes = [_built_scene("s01")]
    episode = EpisodeAssembler().assemble(brief, scenes)
    d = episode.to_dict()
    assert d["title"] == "My Episode"
    assert d["fps"] == 8
    assert d["aspect_ratio"] == "4:3"
    assert len(d["scenes"]) == 1
    assert d["scenes"][0]["scene_id"] == "s01"


# ── single scene ────────────────────────────────────────────────────────────

def test_single_scene_episode():
    brief = _brief()
    scenes = [_built_scene()]
    result = EpisodeAssembler().assemble(brief, scenes)
    assert len(result.scenes) == 1
    assert result.total_duration_sec == scenes[0].duration_sec
    assert result.total_frames == scenes[0].total_frames


# ── idempotency ───────────────────────────────────────────────────────────────

def test_idempotent():
    brief = _brief()
    scenes = [_built_scene("s01"), _built_scene("s02")]
    assembler = EpisodeAssembler()
    e1 = assembler.assemble(brief, scenes)
    e2 = assembler.assemble(brief, scenes)
    assert e1.title == e2.title
    assert e1.total_duration_sec == e2.total_duration_sec
    assert e1.total_frames == e2.total_frames
    assert [s.scene_id for s in e1.scenes] == [s.scene_id for s in e2.scenes]
