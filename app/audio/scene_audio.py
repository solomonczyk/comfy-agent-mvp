"""Scene audio synthesis layer.

Synthesizes per-scene WAV audio from BuiltScene.dialogue using the existing
voice stack (SileroTTS for Russian, KokoroTTS for English).

Rules:
- If scene.dialogue is None or empty -> return None (no audio, no error)
- If scene.voice_ids is empty -> return None (no audio, no error)
- Use first voice_id in scene.voice_ids
- Voice resolution and TTS routing via VoiceResolver
- Output: output_dir/{scene_id}.wav
"""
from __future__ import annotations

import json
import logging
from pathlib import Path

from app.scenes.models import BuiltScene
from app.voice.resolver import VoiceResolver

log = logging.getLogger(__name__)

_DEFAULT_VOICE_MAP_PATH = Path("data/voice_map.json")
_DEFAULT_FALLBACK_VOICE_ID = "tts_ru_01"


class SceneAudioBuilder:
    """Synthesizes per-scene voiceover WAV from BuiltScene dialogue."""

    def __init__(
        self,
        voice_map: dict | None = None,
        fallback_voice_id: str = _DEFAULT_FALLBACK_VOICE_ID,
    ) -> None:
        if voice_map is None:
            with open(_DEFAULT_VOICE_MAP_PATH, encoding="utf-8") as f:
                voice_map = json.load(f)
        self._resolver = VoiceResolver(
            voice_map=voice_map,
            fallback_voice_id=fallback_voice_id,
        )

    def synthesize_scene(self, scene: BuiltScene, output_dir: Path) -> Path | None:
        """Synthesize scene dialogue to WAV.

        Args:
            scene: Built scene containing dialogue and voice_ids.
            output_dir: Directory where the WAV file will be written.

        Returns:
            Path to the WAV file, or None if no audio should be generated.

        Raises:
            RuntimeError: If TTS synthesis fails.
        """
        if not scene.dialogue or not scene.dialogue.strip():
            log.info(f"[audio] scene {scene.scene_id} -> skipped (no dialogue)")
            return None

        if not scene.voice_ids:
            log.info(f"[audio] scene {scene.scene_id} -> skipped (no voice_ids)")
            return None

        voice_id = scene.voice_ids[0]
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        wav_path = output_dir / f"{scene.scene_id}.wav"

        log.info(f"[audio] scene {scene.scene_id} -> synthesizing via voice_id={voice_id!r}")
        try:
            result = self._resolver.synthesize(
                voice_id=voice_id,
                text=scene.dialogue.strip(),
                output_path=wav_path,
            )
        except Exception as exc:
            raise RuntimeError(
                f"TTS synthesis failed for scene '{scene.scene_id}' "
                f"(voice_id={voice_id!r}): {exc}"
            ) from exc

        log.info(f"[audio] scene {scene.scene_id} -> synthesized -> {result}")
        return result
