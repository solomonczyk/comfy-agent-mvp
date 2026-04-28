"""MK-P3 — Voice resolver.

Resolves a voice_id string (from ResolvedCharacter) into TTS parameters
and instantiates the appropriate TTS backend.
Unknown or None voice_id returns the fallback voice with fallback_used=True.
"""
from __future__ import annotations

from pathlib import Path

from .models import ResolvedVoice


class VoiceResolver:
    def __init__(
        self,
        voice_map: dict[str, dict],
        fallback_voice_id: str,
    ) -> None:
        self._map = voice_map
        self._fallback_id = fallback_voice_id

    def resolve(self, voice_id: str | None) -> ResolvedVoice:
        if voice_id and voice_id in self._map:
            entry = self._map[voice_id]
            return ResolvedVoice(
                voice_id=voice_id,
                engine=entry["engine"],
                lang=entry["lang"],
                speaker=entry.get("speaker", ""),
                sample_rate=entry.get("sample_rate", 48000),
                speed=entry.get("speed", 1.0),
                pitch=entry.get("pitch", 1.0),
                fallback_used=False,
            )

        # fallback — look up fallback entry directly to avoid recursion
        entry = self._map.get(self._fallback_id, {})
        return ResolvedVoice(
            voice_id=self._fallback_id,
            engine=entry.get("engine", "silero"),
            lang=entry.get("lang", "ru"),
            speaker=entry.get("speaker", "aidar"),
            sample_rate=entry.get("sample_rate", 48000),
            speed=entry.get("speed", 1.0),
            pitch=entry.get("pitch", 1.0),
            fallback_used=True,
        )

    def synthesize(self, voice_id: str | None, text: str, output_path: Path) -> Path:
        """Resolve voice and synthesize text to output_path. Returns Path to wav."""
        from .tts import KokoroTTS, SileroTTS

        voice = self.resolve(voice_id)
        output_path = Path(output_path)

        if voice.engine == "silero":
            backend = SileroTTS(
                speaker=voice.speaker or "aidar",
                sample_rate=voice.sample_rate,
            )
        elif voice.engine == "kokoro":
            backend = KokoroTTS(
                speaker=voice.speaker or "af_heart",
                sample_rate=voice.sample_rate,
                lang=voice.lang,
            )
        else:
            raise ValueError(f"Unknown TTS engine '{voice.engine}'. Supported: silero, kokoro")

        return backend.synthesize(text, output_path)
