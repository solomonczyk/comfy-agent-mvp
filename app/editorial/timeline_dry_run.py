"""Timeline Dry-Run validator for Combine V2 editorial layer.

Checks that all editorial artifacts are valid and consistent
without performing any real rendering.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional


@dataclass
class DryRunReport:
    """Result of a timeline dry-run validation."""

    dry_run_status: str = "ready_for_operator_review"
    apply_performed: bool = False
    real_render_executed: bool = False
    final_render_allowed: bool = False
    operator_review_required: bool = True
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)


class TimelineDryRun:
    """Dry-run validator for the full editorial layer."""

    def __init__(self) -> None:
        self.report = DryRunReport()
        self._errors: List[str] = []
        self._warnings: List[str] = []

    def _error(self, msg: str) -> None:
        self._errors.append(msg)

    def _warn(self, msg: str) -> None:
        self._warnings.append(msg)

    def validate_timeline(self, timeline_dict: Dict[str, Any]) -> None:
        """Validate the timeline model dict."""
        # Check timeline JSON is valid
        if not timeline_dict:
            self._error("timeline dict is empty")
            return

        # Check tracks exist
        required_tracks = [
            "video_main",
            "video_overlay",
            "audio_voice",
            "audio_music",
            "subtitles",
            "effects",
        ]
        for track in required_tracks:
            if track not in timeline_dict.get("tracks", {}):
                self._error(f"missing track '{track}'")

        # Check scenes have valid duration
        for scene in timeline_dict.get("scenes", []):
            dur = scene.get("duration_sec", -1)
            if dur < 0:
                self._error(f"scene '{scene.get('scene_id')}' has negative duration")
            if dur == 0:
                self._warn(f"scene '{scene.get('scene_id')}' has zero duration")

        # Check final render is not allowed
        if timeline_dict.get("final_render_allowed", False):
            self._error("final_render_allowed must be False in planning layer")

        # Check operator_review_required
        if not timeline_dict.get("operator_review_required", False):
            self._error("operator_review_required must be True")

        # Check all operations have apply_performed=False
        for op in timeline_dict.get("operations", []):
            if op.get("apply_performed", False):
                self._error(
                    f"operation '{op.get('operation_id')}' has apply_performed=True"
                )
            if not op.get("requires_operator_review", False):
                self._error(
                    f"operation '{op.get('operation_id')}' missing operator_review"
                )

    def validate_markers(self, markers: List[Dict[str, Any]]) -> None:
        """Validate marker list."""
        seen_ids: set = set()
        for m in markers:
            mid = m.get("marker_id", "")
            if mid in seen_ids:
                self._error(f"duplicate marker_id '{mid}'")
            seen_ids.add(mid)

    def validate_subtitles(self, subtitles: List[Dict[str, Any]]) -> None:
        """Validate subtitle list."""
        for sub in subtitles:
            text = sub.get("text", "")
            if not text or not text.strip():
                self._error(f"subtitle '{sub.get('subtitle_id')}' has empty text")

    def validate_transition_policy(self, policy_dict: Dict[str, Any]) -> None:
        """Validate transition policy."""
        forbidden = set(policy_dict.get("forbidden_transitions", []))
        for key in [
            "default",
            "same_scene_continuation",
            "new_topic",
            "new_chapter",
            "educational_style",
            "cinematic_style",
        ]:
            val = policy_dict.get(key, "")
            if val in forbidden:
                self._error(
                    f"transition '{val}' for '{key}' is in the forbidden list"
                )

    def validate_voice_casting(self, contract_dict: Dict[str, Any]) -> None:
        """Validate voice casting contract."""
        if contract_dict.get("full_voiceover_generation_allowed", False):
            self._error("voiceover generation must not be allowed in planning layer")

    def validate_preview_contract(self, contract_dict: Dict[str, Any]) -> None:
        """Validate preview proof contract."""
        if contract_dict.get("final_render_allowed", False):
            self._error("final_render_allowed must be False in preview contract")
        if not contract_dict.get("operator_review_required", False):
            self._error("operator_review_required must be True in preview contract")

    def run(
        self,
        timeline_dict: Dict[str, Any],
        markers: List[Dict[str, Any]],
        subtitles: List[Dict[str, Any]],
        transition_policy: Dict[str, Any],
        voice_casting_contract: Dict[str, Any],
        preview_proof_contract: Dict[str, Any],
    ) -> DryRunReport:
        """Run all validations and produce a report."""
        self._errors = []
        self._warnings = []

        self.validate_timeline(timeline_dict)
        self.validate_markers(markers)
        self.validate_subtitles(subtitles)
        self.validate_transition_policy(transition_policy)
        self.validate_voice_casting(voice_casting_contract)
        self.validate_preview_contract(preview_proof_contract)

        if self._errors:
            dry_run_status = "blocked"
        elif self._warnings:
            dry_run_status = "ready_for_operator_review_with_warnings"
        else:
            dry_run_status = "ready_for_operator_review"

        self.report = DryRunReport(
            dry_run_status=dry_run_status,
            apply_performed=False,
            real_render_executed=False,
            final_render_allowed=False,
            operator_review_required=True,
            errors=self._errors,
            warnings=self._warnings,
        )
        return self.report
