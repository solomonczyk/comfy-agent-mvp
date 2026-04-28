"""Tests for MK-P1 — BriefParser and BriefModel.

Coverage:
  - happy path: markdown brief (Russian + English fields)
  - happy path: JSON/dict brief
  - missing required field: meta.title
  - missing required field: no characters
  - missing required field: no scenes
  - malformed JSON string
  - scene_id auto-format validator
  - character_by_name helper
  - to_dict serialisation round-trip
"""
from __future__ import annotations

import json

import pytest

from app.brief.models import BriefModel, CharacterDef, ProjectMeta, SceneDef
from app.brief.parser import BriefParseError, BriefParser


# ── fixtures ────────────────────────────────────────────────────────────────

MARKDOWN_BRIEF = """\
## Meta
title: Кот и луна
duration: 12
fps: 8
aspect_ratio: 4:3
style: anime flat
mood: calm, mysterious

## Characters
- name: Кот
  visual: grey tabby cat, big yellow eyes, sitting pose, anime style
  voice_id: tts_ru_01
  lora: cat_anime_v2.safetensors

- name: Луна
  visual: full moon, soft glow, watercolor background element

## Scenes
- id: s01
  location: крыша дома, ночь
  characters: Кот
  action: Кот смотрит на луну, хвост медленно качается
  duration: 3.0
  keyframes: кот сидит | взгляд вверх | лунный свет на шерсти

- id: s02
  location: та же крыша
  characters: Кот
  action: Кот поднимает лапу, тянется к луне
  duration: 2.5
  dialogue: мяу
"""

DICT_BRIEF = {
    "meta": {
        "title": "Test Project",
        "aspect_ratio": "16:9",
        "fps": 24,
        "target_duration_sec": 60.0,
    },
    "characters": [
        {
            "name": "Hero",
            "visual_description": "tall man in a red coat, dramatic lighting",
            "voice_id": "en_us_01",
        }
    ],
    "scenes": [
        {
            "scene_id": "s01",
            "characters_in_scene": ["Hero"],
            "action": "Hero walks through a dark alley",
            "duration_hint_sec": 4.0,
        }
    ],
}


@pytest.fixture
def parser() -> BriefParser:
    return BriefParser()


# ── happy path: markdown ─────────────────────────────────────────────────────

def test_markdown_happy_path_meta(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    assert brief.meta.title == "Кот и луна"
    assert brief.meta.fps == 8
    assert brief.meta.target_duration_sec == 12.0
    assert brief.meta.aspect_ratio == "4:3"
    assert brief.meta.style_hint == "anime flat"
    assert brief.meta.mood == "calm, mysterious"


def test_markdown_happy_path_characters(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    assert len(brief.characters) == 2

    cat = brief.characters[0]
    assert cat.name == "Кот"
    assert "tabby" in cat.visual_description
    assert cat.voice_id == "tts_ru_01"
    assert cat.lora_ref == "cat_anime_v2.safetensors"

    moon = brief.characters[1]
    assert moon.name == "Луна"
    assert moon.voice_id is None
    assert moon.lora_ref is None


def test_markdown_happy_path_scenes(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    assert len(brief.scenes) == 2

    s1 = brief.scenes[0]
    assert s1.scene_id == "s01"
    assert s1.characters_in_scene == ["Кот"]
    assert s1.duration_hint_sec == 3.0
    assert len(s1.keyframe_hints) == 3
    assert s1.dialogue is None

    s2 = brief.scenes[1]
    assert s2.scene_id == "s02"
    assert s2.duration_hint_sec == 2.5
    assert s2.dialogue == "мяу"


# ── happy path: dict ─────────────────────────────────────────────────────────

def test_dict_happy_path(parser):
    brief = parser.parse(DICT_BRIEF)
    assert brief.meta.title == "Test Project"
    assert brief.meta.fps == 24
    assert brief.characters[0].name == "Hero"
    assert brief.scenes[0].scene_id == "s01"


def test_json_string_happy_path(parser):
    brief = parser.parse(json.dumps(DICT_BRIEF))
    assert brief.meta.title == "Test Project"
    assert len(brief.characters) == 1
    assert len(brief.scenes) == 1


# ── missing required fields ──────────────────────────────────────────────────

def test_missing_title_raises(parser):
    md = """\
## Meta
duration: 10

## Characters
- name: Hero
  visual: tall man in red coat

## Scenes
- action: hero walks
"""
    with pytest.raises(BriefParseError) as exc_info:
        parser.parse(md)
    assert exc_info.value.field == "meta.title"
    assert "title" in str(exc_info.value).lower()


def test_missing_characters_raises(parser):
    md = """\
## Meta
title: Empty Project
duration: 5

## Characters

## Scenes
- action: something happens
"""
    with pytest.raises(BriefParseError) as exc_info:
        parser.parse(md)
    assert exc_info.value.field == "characters"


def test_missing_scenes_raises(parser):
    md = """\
## Meta
title: Empty Scenes Project
duration: 5

## Characters
- name: Alice
  visual: young woman with curly hair

## Scenes
"""
    with pytest.raises(BriefParseError) as exc_info:
        parser.parse(md)
    assert exc_info.value.field == "scenes"


def test_dict_missing_title_raises(parser):
    d = {
        "meta": {"aspect_ratio": "4:3", "fps": 8, "target_duration_sec": 10.0},
        "characters": [{"name": "A", "visual_description": "desc"}],
        "scenes": [{"scene_id": "s01", "characters_in_scene": [], "action": "run"}],
    }
    with pytest.raises(BriefParseError):
        parser.parse(d)


def test_dict_empty_characters_list_raises(parser):
    d = {
        "meta": {"title": "X", "target_duration_sec": 5.0},
        "characters": [],
        "scenes": [{"scene_id": "s01", "characters_in_scene": [], "action": "run"}],
    }
    with pytest.raises(BriefParseError):
        parser.parse(d)


def test_dict_empty_scenes_list_raises(parser):
    d = {
        "meta": {"title": "X", "target_duration_sec": 5.0},
        "characters": [{"name": "A", "visual_description": "desc"}],
        "scenes": [],
    }
    with pytest.raises(BriefParseError):
        parser.parse(d)


# ── malformed input ───────────────────────────────────────────────────────────

def test_malformed_json_raises(parser):
    with pytest.raises(BriefParseError) as exc_info:
        parser.parse("{invalid json}")
    assert exc_info.value.field == "root"


# ── model validators ─────────────────────────────────────────────────────────

def test_scene_id_auto_prefix():
    scene = SceneDef(
        scene_id="01",
        characters_in_scene=[],
        action="test",
    )
    assert scene.scene_id == "s01"


def test_scene_id_already_prefixed():
    scene = SceneDef(
        scene_id="s03",
        characters_in_scene=[],
        action="test",
    )
    assert scene.scene_id == "s03"


# ── BriefModel helpers ────────────────────────────────────────────────────────

def test_character_by_name_found(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    char = brief.character_by_name("Кот")
    assert char.name == "Кот"


def test_character_by_name_case_insensitive(parser):
    brief = parser.parse(DICT_BRIEF)
    char = brief.character_by_name("hero")
    assert char.name == "Hero"


def test_character_by_name_not_found(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    with pytest.raises(KeyError):
        brief.character_by_name("Дракон")


# ── serialisation ─────────────────────────────────────────────────────────────

def test_to_dict_round_trip(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    d = brief.to_dict()
    assert isinstance(d, dict)

    brief2 = BriefModel.model_validate(d)
    assert brief2.meta.title == brief.meta.title
    assert len(brief2.characters) == len(brief.characters)
    assert len(brief2.scenes) == len(brief.scenes)


def test_to_dict_json_serialisable(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    d = brief.to_dict()
    serialised = json.dumps(d, ensure_ascii=False)
    assert "Кот и луна" in serialised
    assert "tts_ru_01" in serialised


def test_to_dict_no_loss(parser):
    brief = parser.parse(MARKDOWN_BRIEF)
    d = brief.to_dict()

    assert d["meta"]["title"] == "Кот и луна"
    assert d["meta"]["fps"] == 8
    assert d["characters"][0]["name"] == "Кот"
    assert d["characters"][0]["lora_ref"] == "cat_anime_v2.safetensors"
    assert d["scenes"][0]["keyframe_hints"] == [
        "кот сидит", "взгляд вверх", "лунный свет на шерсти"
    ]
