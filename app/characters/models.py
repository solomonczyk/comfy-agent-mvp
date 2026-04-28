"""MK-P2 — Resolved character data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class LoraInjection:
    filename: str
    strength_model: float = 0.8
    strength_clip: float = 0.8


@dataclass
class ResolvedCharacter:
    name: str
    positive_prompt: str
    negative_prompt: str
    lora_injections: list[LoraInjection] = field(default_factory=list)
    voice_id: Optional[str] = None

    def to_comfy_lora_stack(self) -> list[dict]:
        """Format for ComfyUI LoRA Stacker node."""
        return [
            {
                "lora_name": l.filename,
                "strength_model": l.strength_model,
                "strength_clip": l.strength_clip,
            }
            for l in self.lora_injections
        ]
