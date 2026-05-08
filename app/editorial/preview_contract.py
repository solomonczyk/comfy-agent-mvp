"""Preview Proof Contract for Combine V2 editorial layer.

Defines required future preview artifacts without performing any preview render.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List


@dataclass
class PreviewProofContract:
    """Contract specifying required preview artifacts.

    No actual preview rendering is performed at this layer.
    """

    preview_lowres_required: bool = True
    preview_gif_required: bool = True
    contact_sheet_required: bool = True
    subtitle_burnin_preview_required: bool = True
    timeline_report_required: bool = True
    transition_qa_required: bool = True
    subtitle_qa_required: bool = True
    audio_qa_required: bool = True
    operator_review_required: bool = True
    final_render_allowed: bool = False

    def validate(self) -> List[str]:
        errors: List[str] = []
        if self.final_render_allowed:
            errors.append("final_render_allowed must be False in planning layer")
        if not self.operator_review_required:
            errors.append(
                "operator_review_required must be True for preview contract"
            )
        return errors

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PreviewProofContract":
        return cls(**data)
