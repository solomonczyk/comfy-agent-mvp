"""MK-P4 — Keyframe planner.

Takes SceneDef list from a BriefModel and produces a timed keyframe plan for
each scene.

Rules:
- First keyframe always at timestamp_sec = 0.0
- Last keyframe always at timestamp_sec = duration_hint_sec
- Keyframes distributed evenly across duration
- If scene.keyframe_hints provided → use them as hint values (one per keyframe)
- If scene.keyframe_hints empty → auto-generate hints "frame_0", "frame_1", …
- Always at least min_keyframes keyframes per scene
- total_frames = round(duration_sec * fps)
"""
from __future__ import annotations

import math

from app.brief.models import BriefModel, SceneDef

from .models import Keyframe, SceneKeyframePlan


class KeyframePlanner:
    def __init__(self, fps: int = 8, min_keyframes: int = 2, max_scene_duration_sec: float = 5.0) -> None:
        self.fps = fps
        self.min_keyframes = min_keyframes
        self.max_scene_duration_sec = max_scene_duration_sec

    def plan(self, brief: BriefModel) -> list[SceneKeyframePlan]:
        return [plan for _, plan in self.plan_with_scenes(brief)]

    def plan_with_scenes(self, brief: BriefModel) -> list[tuple[SceneDef, SceneKeyframePlan]]:
        fps = brief.meta.fps if brief.meta.fps else self.fps
        result: list[tuple[SceneDef, SceneKeyframePlan]] = []
        for scene in brief.scenes:
            result.extend(self._plan_scene_split(scene, fps))
        return result

    def _plan_scene_split(self, scene: SceneDef, fps: int) -> list[tuple[SceneDef, SceneKeyframePlan]]:
        """Split scene into sub-scenes if duration exceeds max_scene_duration_sec."""
        if scene.duration_hint_sec <= self.max_scene_duration_sec:
            return [(scene, self._plan_scene(scene, fps))]

        n_parts = math.ceil(scene.duration_hint_sec / self.max_scene_duration_sec)
        sub_duration = scene.duration_hint_sec / n_parts
        hints = scene.keyframe_hints
        hints_per_part = math.ceil(len(hints) / n_parts) if hints else 0

        pairs: list[tuple[SceneDef, SceneKeyframePlan]] = []
        for i in range(n_parts):
            suffix = chr(ord("a") + i)
            sub_id = f"{scene.scene_id}{suffix}"
            if hints and hints_per_part > 0:
                start = i * hints_per_part
                sub_hints = hints[start: start + hints_per_part]
            else:
                sub_hints = []
            sub_scene = SceneDef(
                scene_id=sub_id,
                characters_in_scene=list(scene.characters_in_scene),
                location=scene.location,
                action=scene.action,
                dialogue=scene.dialogue,
                duration_hint_sec=sub_duration,
                keyframe_hints=sub_hints,
            )
            pairs.append((sub_scene, self._plan_scene(sub_scene, fps)))
        return pairs

    def _plan_scene(self, scene: SceneDef, fps: int) -> SceneKeyframePlan:  # noqa: D401
        duration = scene.duration_hint_sec
        total_frames = round(duration * fps)

        hints = scene.keyframe_hints
        n = max(len(hints), self.min_keyframes) if hints else self.min_keyframes

        keyframes = self._distribute(n, duration, hints)

        return SceneKeyframePlan(
            scene_id=scene.scene_id,
            duration_sec=duration,
            fps=fps,
            total_frames=total_frames,
            keyframes=keyframes,
        )

    def _distribute(
        self,
        n: int,
        duration: float,
        hints: list[str],
    ) -> list[Keyframe]:
        if n == 1:
            hint = hints[0] if hints else "frame_0"
            return [Keyframe(index=0, timestamp_sec=0.0, hint=hint)]

        keyframes: list[Keyframe] = []
        for i in range(n):
            if n == 1:
                ts = 0.0
            else:
                ts = round(duration * i / (n - 1), 6)
            # clamp last to exact duration to avoid float drift
            if i == n - 1:
                ts = duration
            hint = hints[i] if i < len(hints) else f"frame_{i}"
            keyframes.append(Keyframe(index=i, timestamp_sec=ts, hint=hint))

        return keyframes
