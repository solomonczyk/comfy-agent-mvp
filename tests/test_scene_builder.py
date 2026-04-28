"""Tests for MK-P5 — SceneBuilder.

Coverage:
  - returns BuiltScene instance
  - scene_id preserved
  - only characters listed in characters_in_scene are included
  - character not in scene excluded from prompt and loras
  - positive prompt contains visual description of included character
  - duplicate positive prompt fragments are deduplicated
  - negative prompts are merged and deduplicated by token
  - lora stacks are merged correctly
  - duplicate loras deduplicated by lora_name
  - voice_ids contains only non-None values
  - total_frames, duration_sec, fps match the plan
  - keyframe_hints matches hint strings from plan
  - location and dialogue passed through from SceneDef
  - empty characters_in_scene → empty positive prompt, empty lora stack
  - build() is idempotent
"""
from __future__ import annotations

import pytest

from app.brief.models import SceneDef
from app.characters.models import LoraInjection, ResolvedCharacter
from app.keyframes.models import Keyframe, SceneKeyframePlan
from app.scenes.builder import SceneBuilder
from app.scenes.models import BuiltScene


# ── helpers ───────────────────────────────────────────────────────────────────

def _char(
    name: str,
    positive: str = "warrior",
    negative: str = "blurry, low quality",
    loras: list[LoraInjection] | None = None,
    voice_id: str | None = None,
) -> ResolvedCharacter:
    return ResolvedCharacter(
        name=name,
        positive_prompt=positive,
        negative_prompt=negative,
        lora_injections=loras or [],
        voice_id=voice_id,
    )


def _plan(
    scene_id: str = "s01",
    duration: float = 3.0,
    fps: int = 8,
    hints: list[str] | None = None,
) -> SceneKeyframePlan:
    hints = hints or ["frame_0", "frame_1"]
    keyframes = [
        Keyframe(index=i, timestamp_sec=round(duration * i / (len(hints) - 1), 6) if len(hints) > 1 else 0.0, hint=h)
        for i, h in enumerate(hints)
    ]
    if keyframes:
        keyframes[-1].timestamp_sec = duration
    return SceneKeyframePlan(
        scene_id=scene_id,
        duration_sec=duration,
        fps=fps,
        total_frames=round(duration * fps),
        keyframes=keyframes,
    )


def _scene(
    scene_id: str = "s01",
    chars: list[str] | None = None,
    location: str | None = "forest",
    dialogue: str | None = None,
    duration: float = 3.0,
) -> SceneDef:
    return SceneDef(
        scene_id=scene_id,
        characters_in_scene=chars or [],
        action="test action",
        location=location,
        dialogue=dialogue,
        duration_hint_sec=duration,
    )


# ── return type and basic fields ──────────────────────────────────────────────

def test_returns_built_scene():
    scene = _scene(chars=["Hero"])
    plan = _plan()
    chars = [_char("Hero")]
    result = SceneBuilder().build(scene, plan, chars)
    assert isinstance(result, BuiltScene)


def test_scene_id_preserved():
    scene = _scene(scene_id="s07", chars=["Hero"])
    result = SceneBuilder().build(scene, _plan(scene_id="s07"), [_char("Hero")])
    assert result.scene_id == "s07"


# ── character filtering ───────────────────────────────────────────────────────

def test_only_included_chars_in_prompt():
    scene = _scene(chars=["Alice"])
    chars = [_char("Alice", positive="elf princess"), _char("Bob", positive="dark knight")]
    result = SceneBuilder().build(scene, _plan(), chars)
    assert "elf princess" in result.positive_prompt
    assert "dark knight" not in result.positive_prompt


def test_excluded_char_loras_not_in_stack():
    lora = LoraInjection(filename="bob.safetensors")
    scene = _scene(chars=["Alice"])
    chars = [_char("Alice"), _char("Bob", loras=[lora])]
    result = SceneBuilder().build(scene, _plan(), chars)
    lora_names = [e["lora_name"] for e in result.lora_stack]
    assert "bob.safetensors" not in lora_names


def test_positive_prompt_contains_visual():
    scene = _scene(chars=["Hero"])
    chars = [_char("Hero", positive="armoured knight")]
    result = SceneBuilder().build(scene, _plan(), chars)
    assert "armoured knight" in result.positive_prompt


# ── deduplication ─────────────────────────────────────────────────────────────

def test_duplicate_positive_fragments_deduplicated():
    scene = _scene(chars=["A", "B"])
    chars = [
        _char("A", positive="tall warrior"),
        _char("B", positive="tall warrior"),
    ]
    result = SceneBuilder().build(scene, _plan(), chars)
    assert result.positive_prompt.count("tall warrior") == 1


def test_negative_tokens_deduplicated():
    scene = _scene(chars=["A", "B"])
    chars = [
        _char("A", negative="blurry, low quality"),
        _char("B", negative="blurry, watermark"),
    ]
    result = SceneBuilder().build(scene, _plan(), chars)
    tokens = [t.strip() for t in result.negative_prompt.split(",")]
    assert tokens.count("blurry") == 1


def test_lora_deduplication_by_name():
    lora = LoraInjection(filename="shared.safetensors")
    scene = _scene(chars=["A", "B"])
    chars = [
        _char("A", loras=[lora]),
        _char("B", loras=[LoraInjection(filename="shared.safetensors")]),
    ]
    result = SceneBuilder().build(scene, _plan(), chars)
    lora_names = [e["lora_name"] for e in result.lora_stack]
    assert lora_names.count("shared.safetensors") == 1


def test_lora_stack_merged_from_multiple_chars():
    scene = _scene(chars=["A", "B"])
    chars = [
        _char("A", loras=[LoraInjection(filename="a.safetensors")]),
        _char("B", loras=[LoraInjection(filename="b.safetensors")]),
    ]
    result = SceneBuilder().build(scene, _plan(), chars)
    names = {e["lora_name"] for e in result.lora_stack}
    assert "a.safetensors" in names
    assert "b.safetensors" in names


# ── voice_ids ─────────────────────────────────────────────────────────────────

def test_voice_ids_only_non_none():
    scene = _scene(chars=["A", "B"])
    chars = [
        _char("A", voice_id="tts_ru_01"),
        _char("B", voice_id=None),
    ]
    result = SceneBuilder().build(scene, _plan(), chars)
    assert result.voice_ids == ["tts_ru_01"]


def test_voice_ids_all_none_gives_empty_list():
    scene = _scene(chars=["A"])
    chars = [_char("A", voice_id=None)]
    result = SceneBuilder().build(scene, _plan(), chars)
    assert result.voice_ids == []


# ── plan fields ───────────────────────────────────────────────────────────────

def test_total_frames_from_plan():
    plan = _plan(duration=3.0, fps=8)
    result = SceneBuilder().build(_scene(chars=[]), plan, [])
    assert result.total_frames == round(3.0 * 8)


def test_duration_sec_from_plan():
    plan = _plan(duration=2.5)
    result = SceneBuilder().build(_scene(chars=[]), plan, [])
    assert result.duration_sec == 2.5


def test_fps_from_plan():
    plan = _plan(fps=24)
    result = SceneBuilder().build(_scene(chars=[]), plan, [])
    assert result.fps == 24


def test_keyframe_hints_from_plan():
    hints = ["кот сидит", "взгляд вверх"]
    plan = _plan(hints=hints)
    result = SceneBuilder().build(_scene(chars=[]), plan, [])
    assert result.keyframe_hints == hints


# ── scene passthrough ─────────────────────────────────────────────────────────

def test_location_passed_through():
    scene = _scene(chars=[], location="rooftop at night")
    result = SceneBuilder().build(scene, _plan(), [])
    assert result.location == "rooftop at night"


def test_dialogue_passed_through():
    scene = _scene(chars=[], dialogue="мяу")
    result = SceneBuilder().build(scene, _plan(), [])
    assert result.dialogue == "мяу"


def test_none_location_preserved():
    scene = _scene(chars=[], location=None)
    result = SceneBuilder().build(scene, _plan(), [])
    assert result.location is None


# ── empty scene ───────────────────────────────────────────────────────────────

def test_empty_characters_in_scene_empty_positive():
    scene = _scene(chars=[])
    result = SceneBuilder().build(scene, _plan(), [_char("Hero")])
    assert result.positive_prompt == ""


def test_empty_characters_in_scene_empty_lora_stack():
    scene = _scene(chars=[])
    result = SceneBuilder().build(scene, _plan(), [_char("Hero")])
    assert result.lora_stack == []


# ── idempotency ───────────────────────────────────────────────────────────────

def test_idempotent():
    scene = _scene(chars=["Hero"])
    plan = _plan(hints=["a", "b"])
    chars = [_char("Hero", positive="knight", voice_id="tts_en_01")]
    builder = SceneBuilder()
    r1 = builder.build(scene, plan, chars)
    r2 = builder.build(scene, plan, chars)
    assert r1.positive_prompt == r2.positive_prompt
    assert r1.lora_stack == r2.lora_stack
    assert r1.voice_ids == r2.voice_ids
    assert r1.keyframe_hints == r2.keyframe_hints
