"""MK-P2 — Characters resolver.

Takes CharacterDef entries from a BriefModel and produces a
ComfyUI-compatible package for each character:
  - positive_prompt  (visual_description + style_hint + mood from meta)
  - negative_prompt  (default or override)
  - lora_injections  (empty list if lora_ref is None or file not found)
  - voice_id         (passed through from CharacterDef)

Missing LoRA files emit CharacterResolveWarning and do not raise.
"""
from __future__ import annotations

import os
import warnings
from pathlib import Path

from app.brief.models import BriefModel, CharacterDef

from .models import LoraInjection, ResolvedCharacter

_DEFAULT_NEGATIVE = (
    "blurry, deformed, bad anatomy, extra limbs, "
    "watermark, signature, text, low quality"
)

_DEFAULT_LORA_DIR = Path(
    os.environ.get("COMFY_LORA_DIR", "models/loras")
)


class CharacterResolveWarning(UserWarning):
    pass


class CharacterResolver:
    def __init__(
        self,
        lora_dir: Path | str = _DEFAULT_LORA_DIR,
        default_negative: str = _DEFAULT_NEGATIVE,
        lora_strength: float = 0.8,
    ) -> None:
        self.lora_dir = Path(lora_dir)
        self.default_negative = default_negative
        self.lora_strength = lora_strength

    def resolve(self, brief: BriefModel) -> list[ResolvedCharacter]:
        style = brief.meta.style_hint or ""
        mood = brief.meta.mood or ""
        return [
            self._resolve_one(char, style_hint=style, mood=mood)
            for char in brief.characters
        ]

    def _resolve_one(
        self,
        char: CharacterDef,
        style_hint: str,
        mood: str,
    ) -> ResolvedCharacter:
        positive = self._build_positive(char.visual_description, style_hint, mood)
        loras = self._resolve_loras(char)
        return ResolvedCharacter(
            name=char.name,
            positive_prompt=positive,
            negative_prompt=self.default_negative,
            lora_injections=loras,
            voice_id=char.voice_id,
        )

    def _build_positive(self, visual: str, style_hint: str, mood: str) -> str:
        parts = [p.strip() for p in [visual, style_hint, mood] if p.strip()]
        return ", ".join(parts)

    def _resolve_loras(self, char: CharacterDef) -> list[LoraInjection]:
        if not char.lora_ref:
            return []

        lora_path = self.lora_dir / char.lora_ref
        if not lora_path.exists():
            warnings.warn(
                f"LoRA file not found for '{char.name}': {lora_path}. "
                f"Continuing without LoRA injection.",
                CharacterResolveWarning,
                stacklevel=3,
            )
            return []

        return [
            LoraInjection(
                filename=char.lora_ref,
                strength_model=self.lora_strength,
                strength_clip=self.lora_strength,
            )
        ]
