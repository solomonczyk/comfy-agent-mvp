"""Operator Review Gate for Combine V2 editorial layer.

Produces an operator review packet with all editorial layer summaries
and leaves operator decision fields null.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class OperatorReviewPacket:
    """Operator review packet for the editorial layer.

    All operator decision fields start as null.
    """

    operator_review_required: bool = True
    operator_decision: Optional[str] = None
    allowed_operator_decisions: List[str] = field(
        default_factory=lambda: [
            "approved_for_preview_render",
            "needs_changes",
            "rejected",
        ]
    )
    preview_render_allowed: bool = False
    final_render_allowed: bool = False
    production_accepted: bool = False

    # Summaries
    timeline_summary: Optional[dict] = None
    scenes_count: int = 0
    operations_count: int = 0
    subtitles_count: int = 0
    transition_policy_summary: Optional[dict] = None
    voice_casting_summary: Optional[dict] = None
    preview_requirements: Optional[dict] = None
    dry_run_result: Optional[dict] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class OperatorReviewGate:
    """Builds operator review packets for the editorial layer."""

    def build_packet(
        self,
        timeline_dict: Dict[str, Any],
        operation_count: int,
        subtitle_count: int,
        transition_policy_dict: Dict[str, Any],
        voice_casting_dict: Dict[str, Any],
        preview_contract_dict: Dict[str, Any],
        dry_run_dict: Dict[str, Any],
    ) -> OperatorReviewPacket:
        """Build a complete operator review packet."""
        scenes = timeline_dict.get("scenes", [])
        packet = OperatorReviewPacket(
            operator_review_required=True,
            operator_decision=None,
            preview_render_allowed=False,
            final_render_allowed=False,
            production_accepted=False,
            timeline_summary={
                "project_id": timeline_dict.get("project_id", ""),
                "timeline_version": timeline_dict.get("timeline_version", ""),
                "fps": timeline_dict.get("fps", 24),
                "resolution": timeline_dict.get("resolution", {}),
                "track_count": len(timeline_dict.get("tracks", {})),
            },
            scenes_count=len(scenes),
            operations_count=operation_count,
            subtitles_count=subtitle_count,
            transition_policy_summary={
                "default": transition_policy_dict.get("default", ""),
                "forbidden_transitions": transition_policy_dict.get(
                    "forbidden_transitions", []
                ),
                "max_total_fade_ratio": transition_policy_dict.get(
                    "max_total_fade_ratio", 0.35
                ),
            },
            voice_casting_summary={
                "language": voice_casting_dict.get("language", ""),
                "preferred_gender": voice_casting_dict.get("preferred_gender", ""),
                "sample_required": voice_casting_dict.get("sample_required", True),
                "operator_review_required": voice_casting_dict.get(
                    "operator_review_required", True
                ),
            },
            preview_requirements={
                "preview_lowres_required": preview_contract_dict.get(
                    "preview_lowres_required", True
                ),
                "preview_gif_required": preview_contract_dict.get(
                    "preview_gif_required", True
                ),
                "subtitle_burnin_preview_required": preview_contract_dict.get(
                    "subtitle_burnin_preview_required", True
                ),
                "transition_qa_required": preview_contract_dict.get(
                    "transition_qa_required", True
                ),
            },
            dry_run_result={
                "dry_run_status": dry_run_dict.get(
                    "dry_run_status", "unknown"
                ),
                "error_count": len(dry_run_dict.get("errors", [])),
                "warning_count": len(dry_run_dict.get("warnings", [])),
            },
        )
        return packet
