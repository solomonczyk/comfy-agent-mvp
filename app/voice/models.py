"""MK-P3 — Resolved voice data model."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ResolvedVoice:
    voice_id: str
    engine: str           # "silero" | "kokoro" | "edge-tts" etc.
    lang: str             # "ru" | "en" etc.
    speaker: str = ""     # engine-specific speaker name
    sample_rate: int = 48000
    speed: float = 1.0
    pitch: float = 1.0
    fallback_used: bool = False
