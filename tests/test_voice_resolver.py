"""Tests for MK-P3 — VoiceResolver.

Coverage:
  - known voice_id → correct ResolvedVoice, fallback_used=False
  - unknown voice_id → fallback, fallback_used=True
  - None → fallback, fallback_used=True
  - engine and lang non-empty in any result
  - speed and pitch default to 1.0 when absent from voice_map
  - resolve() is idempotent
  - fallback itself resolves correctly (no recursion)
"""
from __future__ import annotations

import pytest

from app.voice.models import ResolvedVoice
from app.voice.resolver import VoiceResolver


# ── shared fixture ────────────────────────────────────────────────────────────

VOICE_MAP = {
    "tts_ru_01": {"engine": "coqui", "lang": "ru", "speed": 1.0, "pitch": 1.0},
    "tts_en_01": {"engine": "edge-tts", "lang": "en", "speed": 1.2, "pitch": 0.9},
    "tts_no_defaults": {"engine": "elevenlabs", "lang": "es"},  # speed/pitch absent
}

FALLBACK_ID = "tts_en_01"


@pytest.fixture
def resolver() -> VoiceResolver:
    return VoiceResolver(voice_map=VOICE_MAP, fallback_voice_id=FALLBACK_ID)


# ── known voice_id ────────────────────────────────────────────────────────────

def test_known_voice_returns_resolved_voice(resolver):
    result = resolver.resolve("tts_ru_01")
    assert isinstance(result, ResolvedVoice)


def test_known_voice_correct_engine(resolver):
    result = resolver.resolve("tts_ru_01")
    assert result.engine == "coqui"


def test_known_voice_correct_lang(resolver):
    result = resolver.resolve("tts_ru_01")
    assert result.lang == "ru"


def test_known_voice_fallback_used_false(resolver):
    result = resolver.resolve("tts_ru_01")
    assert result.fallback_used is False


def test_known_voice_id_preserved(resolver):
    result = resolver.resolve("tts_ru_01")
    assert result.voice_id == "tts_ru_01"


def test_known_voice_speed(resolver):
    result = resolver.resolve("tts_en_01")
    assert result.speed == 1.2


def test_known_voice_pitch(resolver):
    result = resolver.resolve("tts_en_01")
    assert result.pitch == 0.9


# ── unknown / None ────────────────────────────────────────────────────────────

def test_unknown_voice_returns_fallback(resolver):
    result = resolver.resolve("does_not_exist")
    assert result.fallback_used is True
    assert result.voice_id == FALLBACK_ID


def test_none_voice_returns_fallback(resolver):
    result = resolver.resolve(None)
    assert result.fallback_used is True
    assert result.voice_id == FALLBACK_ID


def test_unknown_voice_engine_not_empty(resolver):
    result = resolver.resolve("ghost_voice")
    assert result.engine != ""


def test_unknown_voice_lang_not_empty(resolver):
    result = resolver.resolve("ghost_voice")
    assert result.lang != ""


# ── defaults ──────────────────────────────────────────────────────────────────

def test_speed_defaults_to_1_when_absent():
    r = VoiceResolver(
        voice_map={"v": {"engine": "coqui", "lang": "ru"}},
        fallback_voice_id="v",
    )
    assert r.resolve("v").speed == 1.0


def test_pitch_defaults_to_1_when_absent():
    r = VoiceResolver(
        voice_map={"v": {"engine": "coqui", "lang": "ru"}},
        fallback_voice_id="v",
    )
    assert r.resolve("v").pitch == 1.0


def test_no_defaults_key_in_map(resolver):
    result = resolver.resolve("tts_no_defaults")
    assert result.speed == 1.0
    assert result.pitch == 1.0
    assert result.engine == "elevenlabs"


# ── idempotency ───────────────────────────────────────────────────────────────

def test_idempotent_known(resolver):
    assert resolver.resolve("tts_ru_01") == resolver.resolve("tts_ru_01")


def test_idempotent_fallback(resolver):
    assert resolver.resolve(None) == resolver.resolve(None)


# ── fallback correctness (no infinite recursion) ──────────────────────────────

def test_fallback_voice_id_is_itself_resolvable(resolver):
    result = resolver.resolve(FALLBACK_ID)
    assert result.fallback_used is False
    assert result.engine == "edge-tts"


def test_fallback_when_fallback_id_not_in_map():
    r = VoiceResolver(
        voice_map={"known": {"engine": "coqui", "lang": "ru"}},
        fallback_voice_id="missing_fallback",
    )
    result = r.resolve("unknown")
    assert result.fallback_used is True
    assert result.engine == "silero"   # hardcoded safe default
    assert result.lang == "ru"
