"""Marker registry for Combine V2 editorial layer.

Supports markers anchored by scene_id, shot_id, timecode,
transcript_phrase, or frame_number.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set

VALID_ANCHOR_TYPES = {
    "scene_id",
    "shot_id",
    "timecode",
    "transcript_phrase",
    "frame_number",
}

# Basic timecode pattern: HH:MM:SS or HH:MM:SS.mmm
TIMECODE_RE = re.compile(r"^\d{1,2}:\d{2}:\d{2}(\.\d+)?$")


@dataclass
class Marker:
    """A single marker on the timeline."""

    marker_id: str = ""
    scene_id: str = ""
    shot_id: str = ""
    timecode: str = ""
    description: str = ""
    anchor_type: str = "scene_id"

    def validate(self, known_scene_ids: Set[str]) -> List[str]:
        errors: List[str] = []
        if not self.marker_id:
            errors.append("marker_id must be non-empty")
        if self.anchor_type not in VALID_ANCHOR_TYPES:
            errors.append(
                f"anchor_type must be one of {VALID_ANCHOR_TYPES}, "
                f"got '{self.anchor_type}'"
            )
        if self.scene_id:
            if self.scene_id not in known_scene_ids:
                errors.append(
                    f"scene_id '{self.scene_id}' not found in known scenes"
                )
        if self.timecode and not TIMECODE_RE.match(self.timecode):
            errors.append(f"invalid timecode format '{self.timecode}'")
        return errors


class MarkerRegistry:
    """Registry for timeline markers with duplicate and anchor validation."""

    def __init__(self) -> None:
        self._markers: Dict[str, Marker] = {}
        self._known_scene_ids: Set[str] = set()

    def set_known_scene_ids(self, scene_ids: Set[str]) -> None:
        self._known_scene_ids = scene_ids

    def register(self, marker: Marker) -> List[str]:
        errors: List[str] = []
        if marker.marker_id in self._markers:
            errors.append(f"duplicate marker_id '{marker.marker_id}'")
            return errors
        errs = marker.validate(self._known_scene_ids)
        errors.extend(errs)
        if not errors:
            self._markers[marker.marker_id] = marker
        return errors

    def get(self, marker_id: str) -> Optional[Marker]:
        return self._markers.get(marker_id)

    def list_markers(self) -> List[Marker]:
        return list(self._markers.values())

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [asdict(m) for m in self._markers.values()]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict_list(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict_list(
        cls, items: List[Dict[str, Any]], known_scene_ids: Optional[Set[str]] = None
    ) -> "MarkerRegistry":
        registry = cls()
        if known_scene_ids is not None:
            registry.set_known_scene_ids(known_scene_ids)
        for item in items:
            marker = Marker(**item)
            registry._markers[marker.marker_id] = marker
        return registry

    @classmethod
    def from_json(
        cls, text: str, known_scene_ids: Optional[Set[str]] = None
    ) -> "MarkerRegistry":
        return cls.from_dict_list(json.loads(text), known_scene_ids)
