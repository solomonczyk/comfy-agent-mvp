"""Subtitle Planner for Combine V2 editorial layer.

Produces a subtitle plan contract with timecode, anchor, and overlap validation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional, Set

VALID_POSITIONS = {"bottom_center", "top_center", "left", "right", "custom"}
VALID_STYLES = {"clean_white", "yellow_on_black", "custom"}
VALID_ANCHOR_TYPES = {
    "timecode",
    "scene_offset",
    "marker_anchor",
    "transcript_phrase_anchor",
}


@dataclass
class SubtitleEntry:
    """A single subtitle entry in the plan."""

    subtitle_id: str = ""
    text: str = ""
    anchor_type: str = ""
    start_time: str = ""
    end_time: str = ""
    scene_id: str = ""
    start_offset: Optional[float] = None
    duration: Optional[float] = None
    position: str = "bottom_center"
    style: str = "clean_white"
    safe_zone_required: bool = True

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.subtitle_id:
            errors.append("subtitle_id must be non-empty")
        if not self.text or not self.text.strip():
            errors.append("text must be non-empty")
        if self.anchor_type and self.anchor_type not in VALID_ANCHOR_TYPES:
            errors.append(
                f"anchor_type must be one of {VALID_ANCHOR_TYPES}, "
                f"got '{self.anchor_type}'"
            )
        if not self.anchor_type:
            errors.append("anchor_type is required")
        if self.duration is not None and self.duration < 0:
            errors.append(f"duration must be >= 0, got {self.duration}")
        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                errors.append(
                    f"end_time '{self.end_time}' is before start_time '{self.start_time}'"
                )
        if self.start_offset is not None and self.start_offset < 0:
            errors.append(f"start_offset must be >= 0, got {self.start_offset}")
        if self.position not in VALID_POSITIONS:
            errors.append(
                f"position must be one of {VALID_POSITIONS}, got '{self.position}'"
            )
        return errors


class SubtitlePlanner:
    """Planner for subtitle contracts with overlap detection."""

    def __init__(self) -> None:
        self._entries: Dict[str, SubtitleEntry] = {}

    def add_entry(self, entry: SubtitleEntry) -> List[str]:
        errors = entry.validate()
        if errors:
            return errors
        if entry.subtitle_id in self._entries:
            return [f"duplicate subtitle_id '{entry.subtitle_id}'"]
        # Check overlap with existing entries that share track (same scene_id)
        for existing in self._entries.values():
            if existing.scene_id != entry.scene_id:
                continue
            if entry.start_time and existing.start_time and entry.end_time and existing.end_time:
                if _intervals_overlap(
                    entry.start_time, entry.end_time,
                    existing.start_time, existing.end_time,
                ):
                    errors.append(
                        f"subtitle '{entry.subtitle_id}' overlaps with "
                        f"'{existing.subtitle_id}' at time range "
                        f"[{entry.start_time}, {entry.end_time}]"
                    )
        if errors:
            return errors
        self._entries[entry.subtitle_id] = entry
        return []

    def list_entries(self) -> List[SubtitleEntry]:
        return list(self._entries.values())

    def to_dict_list(self) -> List[Dict[str, Any]]:
        return [asdict(e) for e in self._entries.values()]

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict_list(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict_list(cls, items: List[Dict[str, Any]]) -> "SubtitlePlanner":
        planner = cls()
        for item in items:
            planner._entries[item["subtitle_id"]] = SubtitleEntry(**item)
        return planner


def _intervals_overlap(
    start_a: str, end_a: str, start_b: str, end_b: str
) -> bool:
    """Crude timecode string overlap check; assumes lexicographic ordering."""
    return start_a < end_b and start_b < end_a
