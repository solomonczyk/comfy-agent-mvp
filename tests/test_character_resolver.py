"""Tests for MK-P2 — CharacterResolver.

Coverage:
  - happy path: returns list[ResolvedCharacter]
  - positive prompt composition (visual + style_hint + mood)
  - no trailing comma when no style/mood
  - voice_id passthrough
  - custom/default negative prompt
  - multi-character ordering
  - idempotency
  - LoRA found → injected with correct strength
  - LoRA missing → CharacterResolveWarning, no raise, empty injections
  - to_comfy_lora_stack() format
"""
from __future__ import annotations

import warnings

import pytest

from app.brief.models import BriefModel, CharacterDef, ProjectMeta, SceneDef
from app.characters.models import ResolvedCharacter
from app.characters.resolver import CharacterResolver, CharacterResolveWarning


# ── helpers ───────────────────────────────────────────────────────────────────

def _make_brief(chars, style=None, mood=None):
    return BriefModel(
        meta=ProjectMeta(title="Test", target_duration_sec=5, style_hint=style, mood=mood),
        characters=chars,
        scenes=[SceneDef(scene_id="s01", characters_in_scene=[], action="test")],
    )


def _char(name="Hero", visual="tall warrior", voice=None, lora=None):
    return CharacterDef(name=name, visual_description=visual, voice_id=voice, lora_ref=lora)


# ── happy path ────────────────────────────────────────────────────────────────

def test_resolve_returns_list():
    brief = _make_brief([_char()])
    result = CharacterResolver().resolve(brief)
    assert isinstance(result, list)
    assert len(result) == 1
    assert isinstance(result[0], ResolvedCharacter)


def test_positive_prompt_contains_visual():
    brief = _make_brief([_char(visual="red cloak")])
    r = CharacterResolver().resolve(brief)[0]
    assert "red cloak" in r.positive_prompt


def test_style_hint_appended():
    brief = _make_brief([_char()], style="oil painting")
    r = CharacterResolver().resolve(brief)[0]
    assert "oil painting" in r.positive_prompt


def test_mood_appended():
    brief = _make_brief([_char()], mood="dark")
    r = CharacterResolver().resolve(brief)[0]
    assert "dark" in r.positive_prompt


def test_no_style_no_trailing_comma():
    brief = _make_brief([_char(visual="warrior")])
    r = CharacterResolver().resolve(brief)[0]
    assert not r.positive_prompt.endswith(",")


def test_voice_id_passed_through():
    brief = _make_brief([_char(voice="tts_ru_01")])
    r = CharacterResolver().resolve(brief)[0]
    assert r.voice_id == "tts_ru_01"


def test_no_voice_is_none():
    brief = _make_brief([_char()])
    r = CharacterResolver().resolve(brief)[0]
    assert r.voice_id is None


def test_negative_prompt_default_not_empty():
    brief = _make_brief([_char()])
    r = CharacterResolver().resolve(brief)[0]
    assert len(r.negative_prompt) > 0


def test_custom_negative_prompt():
    brief = _make_brief([_char()])
    r = CharacterResolver(default_negative="ugly").resolve(brief)[0]
    assert r.negative_prompt == "ugly"


def test_multi_character_count():
    brief = _make_brief([_char("A"), _char("B"), _char("C")])
    result = CharacterResolver().resolve(brief)
    assert len(result) == 3


def test_multi_character_names():
    brief = _make_brief([_char("Alice"), _char("Bob")])
    names = [r.name for r in CharacterResolver().resolve(brief)]
    assert names == ["Alice", "Bob"]


def test_idempotent():
    brief = _make_brief([_char(visual="knight")])
    r = CharacterResolver()
    assert r.resolve(brief)[0].positive_prompt == r.resolve(brief)[0].positive_prompt


# ── lora ──────────────────────────────────────────────────────────────────────

def test_no_lora_ref_empty_stack(tmp_path):
    brief = _make_brief([_char(lora=None)])
    r = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0]
    assert r.lora_injections == []
    assert r.to_comfy_lora_stack() == []


def test_lora_found(tmp_path):
    (tmp_path / "hero.safetensors").touch()
    brief = _make_brief([_char(lora="hero.safetensors")])
    r = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0]
    assert len(r.lora_injections) == 1
    assert r.lora_injections[0].filename == "hero.safetensors"


def test_lora_strength_default(tmp_path):
    (tmp_path / "hero.safetensors").touch()
    brief = _make_brief([_char(lora="hero.safetensors")])
    r = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0]
    assert r.lora_injections[0].strength_model == 0.8
    assert r.lora_injections[0].strength_clip == 0.8


def test_lora_custom_strength(tmp_path):
    (tmp_path / "hero.safetensors").touch()
    brief = _make_brief([_char(lora="hero.safetensors")])
    r = CharacterResolver(lora_dir=tmp_path, lora_strength=0.6).resolve(brief)[0]
    assert r.lora_injections[0].strength_model == 0.6


def test_lora_missing_warns_not_raises(tmp_path):
    brief = _make_brief([_char(lora="missing.safetensors")])
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        r = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0]
    assert any(issubclass(x.category, CharacterResolveWarning) for x in w)
    assert r.lora_injections == []


def test_lora_missing_prompt_still_built(tmp_path):
    brief = _make_brief([_char(visual="dark mage", lora="ghost.safetensors")])
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        r = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0]
    assert "dark mage" in r.positive_prompt


def test_comfy_lora_stack_format(tmp_path):
    (tmp_path / "a.safetensors").touch()
    brief = _make_brief([_char(lora="a.safetensors")])
    stack = CharacterResolver(lora_dir=tmp_path).resolve(brief)[0].to_comfy_lora_stack()
    assert stack == [{"lora_name": "a.safetensors", "strength_model": 0.8, "strength_clip": 0.8}]
