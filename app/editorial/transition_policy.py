"""Transition Policy for Combine V2 editorial layer.

Defines default transitions, forbidden transitions, and validates
fade ratio constraints.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

FORBIDDEN_TRANSITIONS = {"random_wipe", "spin", "excessive_glitch"}

DEFAULT_POLICY = {
    "default": "hard_cut",
    "same_scene_continuation": "hard_cut",
    "new_topic": "crossfade",
    "new_chapter": "fade_to_black",
    "educational_style": "clean_cut",
    "cinematic_style": "fade_or_dissolve",
    "forbidden_transitions": list(FORBIDDEN_TRANSITIONS),
    "max_total_fade_ratio": 0.35,
}


@dataclass
class TransitionPolicy:
    """Transition policy for timeline editing."""

    default: str = "hard_cut"
    same_scene_continuation: str = "hard_cut"
    new_topic: str = "crossfade"
    new_chapter: str = "fade_to_black"
    educational_style: str = "clean_cut"
    cinematic_style: str = "fade_or_dissolve"
    forbidden_transitions: List[str] = field(
        default_factory=lambda: list(FORBIDDEN_TRANSITIONS)
    )
    max_total_fade_ratio: float = 0.35

    def validate(self) -> List[str]:
        errors: List[str] = []
        self._check_forbidden(errors)
        if not (0 <= self.max_total_fade_ratio <= 1):
            errors.append(
                f"max_total_fade_ratio must be in [0, 1], got {self.max_total_fade_ratio}"
            )
        return errors

    def _check_forbidden(self, errors: List[str]) -> None:
        for key in [
            "default",
            "same_scene_continuation",
            "new_topic",
            "new_chapter",
            "educational_style",
            "cinematic_style",
        ]:
            val = getattr(self, key, "")
            if val in self.forbidden_transitions:
                errors.append(
                    f"transition '{val}' for '{key}' is in the forbidden list"
                )

    def is_transition_allowed(self, transition_name: str) -> bool:
        return transition_name not in self.forbidden_transitions

    def to_dict(self) -> Dict[str, Any]:
        raw = asdict(self)
        return raw

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TransitionPolicy":
        return cls(**data)

    @classmethod
    def from_json(cls, text: str) -> "TransitionPolicy":
        return cls.from_dict(json.loads(text))

    @classmethod
    def default_policy(cls) -> "TransitionPolicy":
        return cls(**DEFAULT_POLICY)
