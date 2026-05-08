"""Voice Casting Policy for Combine V2 editorial layer.

Defines a voice casting contract only — no real voice generation.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class VoiceCastingContract:
    """Contract specifying voice casting requirements.

    No real voice generation is performed at this layer.
    """

    language: str = "ru"
    preferred_gender: str = "female"
    age_range: str = "30-45"
    tone: List[str] = field(
        default_factory=lambda: ["calm", "clear", "expert", "friendly"]
    )
    pace: str = "medium"
    emotion: str = "confident_warm"
    avoid: List[str] = field(
        default_factory=lambda: [
            "robotic",
            "too_fast",
            "overdramatic",
            "aggressive_sales_tone",
        ]
    )
    sample_required: bool = True
    operator_review_required: bool = True
    full_voiceover_generation_allowed: bool = False

    def validate(self) -> List[str]:
        errors: List[str] = []
        if not self.language:
            errors.append("language must be non-empty")
        if not self.tone:
            errors.append("tone must have at least one entry")
        if self.full_voiceover_generation_allowed:
            errors.append(
                "full_voiceover_generation_allowed must be False in planning layer"
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "VoiceCastingContract":
        return cls(**data)
