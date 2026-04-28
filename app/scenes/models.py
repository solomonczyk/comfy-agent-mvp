"""MK-P5 — Built scene data model."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BuiltScene:
    scene_id: str
    positive_prompt: str       # merged from all characters_in_scene
    negative_prompt: str       # merged (deduplicated)
    lora_stack: list[dict]     # combined to_comfy_lora_stack() from all chars
    voice_ids: list[str]       # non-None voice_ids from chars in scene
    total_frames: int          # from SceneKeyframePlan
    duration_sec: float
    fps: int
    aspect_ratio: str = "4:3"  # from brief.meta.aspect_ratio
    keyframe_hints: list[str] = field(default_factory=list)  # hint strings from SceneKeyframePlan.keyframes
    location: str | None = None
    dialogue: str | None = None
