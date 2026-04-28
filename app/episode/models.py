"""MK-P6 — Episode data model."""
from __future__ import annotations

from dataclasses import dataclass, field

from app.scenes.models import BuiltScene


@dataclass
class Episode:
    title: str
    total_duration_sec: float   # sum of all scene duration_sec
    total_frames: int           # sum of all scene total_frames
    fps: int
    aspect_ratio: str
    scenes: list[BuiltScene]    # ordered

    def to_dict(self) -> dict:
        """Full serialization, JSON-safe."""
        return {
            "title": self.title,
            "total_duration_sec": self.total_duration_sec,
            "total_frames": self.total_frames,
            "fps": self.fps,
            "aspect_ratio": self.aspect_ratio,
            "scenes": [
                {
                    "scene_id": s.scene_id,
                    "positive_prompt": s.positive_prompt,
                    "negative_prompt": s.negative_prompt,
                    "lora_stack": s.lora_stack,
                    "voice_ids": s.voice_ids,
                    "total_frames": s.total_frames,
                    "duration_sec": s.duration_sec,
                    "fps": s.fps,
                    "aspect_ratio": s.aspect_ratio,
                    "keyframe_hints": s.keyframe_hints,
                    "location": s.location,
                    "dialogue": s.dialogue,
                }
                for s in self.scenes
            ],
        }
