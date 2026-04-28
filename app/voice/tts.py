"""MK-P3 — TTS backends.

Provides SileroTTS (Russian) and KokoroTTS (English) synthesis backends.
Each backend exposes a single `synthesize(text, output_path) -> Path` method.
"""
from __future__ import annotations

import logging
from pathlib import Path

log = logging.getLogger(__name__)

_SILERO_SPEAKERS = ("aidar", "baya", "kseniya", "xenia", "eugene")
_SILERO_MODEL_CACHE: dict[str, object] = {}


class SileroTTS:
    """Russian TTS via Silero v4."""

    def __init__(self, speaker: str = "aidar", sample_rate: int = 48000) -> None:
        if speaker not in _SILERO_SPEAKERS:
            raise ValueError(f"Unknown Silero speaker '{speaker}'. Choose from {_SILERO_SPEAKERS}")
        self.speaker = speaker
        self.sample_rate = sample_rate
        self._model = self._load_model()

    def _load_model(self):
        cache_key = f"ru_v4_{self.sample_rate}"
        if cache_key not in _SILERO_MODEL_CACHE:
            import torch
            log.info("[SILERO] Loading silero_tts model (ru / v4_ru)...")
            model, _ = torch.hub.load(
                repo_or_dir="snakers4/silero-models",
                model="silero_tts",
                language="ru",
                speaker="v4_ru",
            )
            _SILERO_MODEL_CACHE[cache_key] = model
            log.info("[SILERO] Model loaded.")
        return _SILERO_MODEL_CACHE[cache_key]

    def synthesize(self, text: str, output_path: Path) -> Path:
        import soundfile as sf

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        log.info(f"[SILERO] Synthesizing {len(text)} chars → {output_path}")
        audio = self._model.apply_tts(
            text=text,
            speaker=self.speaker,
            sample_rate=self.sample_rate,
        )
        sf.write(str(output_path), audio.numpy(), self.sample_rate)
        dur = len(audio) / self.sample_rate
        log.info(f"[SILERO] Done — {dur:.2f}s saved to {output_path}")
        return output_path


class KokoroTTS:
    """English TTS via Kokoro."""

    _LANG_CODES = {"en": "a", "en-gb": "b", "es": "e", "fr": "f",
                   "hi": "h", "it": "i", "pt": "p", "ja": "j", "zh": "z"}

    def __init__(self, speaker: str = "af_heart", sample_rate: int = 24000, lang: str = "en") -> None:
        self.speaker = speaker
        self.sample_rate = sample_rate
        self.lang = lang

    def synthesize(self, text: str, output_path: Path) -> Path:
        import soundfile as sf
        from kokoro import KPipeline

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        lang_code = self._LANG_CODES.get(self.lang.lower(), "a")
        log.info(f"[KOKORO] Synthesizing {len(text)} chars → {output_path}")
        pipeline = KPipeline(lang_code=lang_code)
        generator = pipeline(text, voice=self.speaker, speed=1.0)

        import numpy as np
        chunks = [chunk.numpy() if hasattr(chunk, "numpy") else chunk
                  for _, _, chunk in generator]
        if not chunks:
            raise RuntimeError("KokoroTTS produced no audio")
        audio = np.concatenate(chunks)
        sf.write(str(output_path), audio, self.sample_rate)
        dur = len(audio) / self.sample_rate
        log.info(f"[KOKORO] Done — {dur:.2f}s saved to {output_path}")
        return output_path
