"""Timeline model for Combine V2 editorial layer.

JSON-serializable timeline with scenes, shots, tracks, and asset placement.
No real rendering — planning and validation only.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


VALID_FIT_POLICIES = {"contain", "cover", "contain_or_cover"}
VALID_SCENE_STATUSES = {"planned", "locked", "rendered", "failed"}
VALID_TRACK_NAMES = [
    "video_main",
    "video_overlay",
    "audio_voice",
    "audio_music",
    "subtitles",
    "effects",
]


@dataclass
class ShotContract:
    """A single shot within a scene."""

    shot_id: str
    candidate_asset: str = ""
    asset_type: str = "image_or_video"
    duration_sec: float = 0.0
    fit_policy: str = "contain_or_cover"
    safe_area_required: bool = True

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.shot_id:
            errors.append("shot_id must be non-empty")
        if self.duration_sec < 0:
            errors.append(f"duration_sec must be >= 0, got {self.duration_sec}")
        if self.fit_policy not in VALID_FIT_POLICIES:
            errors.append(
                f"fit_policy must be one of {VALID_FIT_POLICIES}, got '{self.fit_policy}'"
            )
        if self.asset_type not in ("image", "video", "image_or_video"):
            errors.append(f"unsupported asset_type '{self.asset_type}'")
        return errors


@dataclass
class SceneContract:
    """A scene containing one or more shots."""

    scene_id: str
    duration_sec: float = 0.0
    shot_ids: List[str] = field(default_factory=list)
    asset_refs: List[str] = field(default_factory=list)
    start_time: str = ""
    end_time: str = ""
    status: str = "planned"

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.scene_id:
            errors.append("scene_id must be non-empty")
        if self.duration_sec < 0:
            errors.append(f"duration_sec must be >= 0, got {self.duration_sec}")
        if self.status not in VALID_SCENE_STATUSES:
            errors.append(
                f"status must be one of {VALID_SCENE_STATUSES}, got '{self.status}'"
            )
        return errors


@dataclass
class AssetPlacement:
    """A placed asset reference within the timeline."""

    asset_ref: str = ""
    track: str = "video_main"
    start_time: str = ""
    end_time: str = ""
    duration_sec: float = 0.0
    fit_policy: str = "contain_or_cover"


@dataclass
class TimelineModel:
    """Top-level timeline model for an episode/project."""

    project_id: str = "rc2_multishot1_ep01"
    timeline_version: str = "mvp_v1"
    fps: int = 24
    resolution: dict = field(default_factory=lambda: {"width": 1344, "height": 768})
    tracks: dict = field(
        default_factory=lambda: {
            "video_main": [],
            "video_overlay": [],
            "audio_voice": [],
            "audio_music": [],
            "subtitles": [],
            "effects": [],
        }
    )
    scenes: List[SceneContract] = field(default_factory=list)
    markers: List[dict] = field(default_factory=list)
    operations: List[dict] = field(default_factory=list)
    operator_review_required: bool = True
    final_render_allowed: bool = False

    def add_scene(self, scene: SceneContract) -> None:
        self.scenes.append(scene)

    def get_scene(self, scene_id: str) -> Optional[SceneContract]:
        for s in self.scenes:
            if s.scene_id == scene_id:
                return s
        return None

    def to_dict(self) -> Dict[str, Any]:
        raw = asdict(self)
        return raw

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TimelineModel":
        scenes = [SceneContract(**s) for s in data.pop("scenes", [])]
        model = cls(**data)
        model.scenes = scenes
        return model

    @classmethod
    def from_json(cls, text: str) -> "TimelineModel":
        return cls.from_dict(json.loads(text))

    def validate_tracks(self) -> List[str]:
        errors: List[str] = []
        for name in VALID_TRACK_NAMES:
            if name not in self.tracks:
                errors.append(f"missing required track '{name}'")
        # Check for unknown tracks
        for name in self.tracks:
            if name not in VALID_TRACK_NAMES:
                errors.append(f"unknown track '{name}'")
        # Check FPS
        if self.fps <= 0:
            errors.append(f"fps must be positive, got {self.fps}")
        return errors

    def validate(self) -> List[str]:
        errors: List[str] = []
        errors.extend(self.validate_tracks())
        seen_scene_ids: set = set()
        for scene in self.scenes:
            errs = scene.validate()
            for e in errs:
                errors.append(f"scene '{scene.scene_id}': {e}")
            if scene.scene_id in seen_scene_ids:
                errors.append(f"duplicate scene_id '{scene.scene_id}'")
            seen_scene_ids.add(scene.scene_id)
        return errors
