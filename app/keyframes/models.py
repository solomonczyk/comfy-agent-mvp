"""MK-P4 — Keyframe planner data models."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Keyframe:
    index: int            # 0-based position within the scene
    timestamp_sec: float  # absolute time from scene start
    hint: str             # from SceneDef.keyframe_hints or auto-generated


@dataclass
class SceneKeyframePlan:
    scene_id: str
    duration_sec: float
    fps: int
    total_frames: int     # round(duration_sec * fps)
    keyframes: list[Keyframe] = field(default_factory=list)
