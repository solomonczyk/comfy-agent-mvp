"""Contracts, data structures, and type definitions for film crew agents.

Defines the role contract schema, permission boundaries, and output types
for the Script Supervisor / Continuity Guard and future film crew agents.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Agent Role Contract
# ---------------------------------------------------------------------------

@dataclass
class AgentRoleContract:
    """Canonical contract defining an agent's role, scope, and boundaries."""
    agent_id: str
    role: str
    responsibilities: List[str]
    allowed_tools: List[str]
    forbidden_actions: List[str]
    may_block_pipeline: bool = False
    may_accept_preview: bool = False
    may_accept_voice: bool = False
    may_set_production_accepted: bool = False
    required_inputs: List[str] = field(default_factory=list)
    required_outputs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "responsibilities": self.responsibilities,
            "allowed_tools": self.allowed_tools,
            "forbidden_actions": self.forbidden_actions,
            "may_block_pipeline": self.may_block_pipeline,
            "may_accept_preview": self.may_accept_preview,
            "may_accept_voice": self.may_accept_voice,
            "may_set_production_accepted": self.may_set_production_accepted,
            "required_inputs": self.required_inputs,
            "required_outputs": self.required_outputs,
        }


# ---------------------------------------------------------------------------
# Preview Audit Report
# ---------------------------------------------------------------------------

@dataclass
class PreviewAuditReport:
    """Result of a preview continuity audit."""
    preview_found: bool = False
    preview_path: Optional[str] = None
    preview_gif_found: bool = False
    preview_gif_path: Optional[str] = None
    contact_sheet_found: bool = False
    contact_sheet_path: Optional[str] = None
    frames_dir_found: bool = False
    frames_dir_path: Optional[str] = None
    total_frame_count: int = 0
    unique_frame_count: int = 0
    duplicate_frame_count: int = 0
    duplicate_static_ratio: float = 0.0
    preview_duplicate_static_frames_detected: bool = False
    preview_continuity_passed: bool = False
    contact_sheet_useful: bool = False
    timeline_progression_proven: bool = False
    preview_path_mismatch_detected: bool = False
    expected_preview_path: str = ""
    actual_preview_path: str = ""
    blocker_required: bool = False
    audit_timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "preview_found": self.preview_found,
            "preview_path": self.preview_path,
            "preview_gif_found": self.preview_gif_found,
            "preview_gif_path": self.preview_gif_path,
            "contact_sheet_found": self.contact_sheet_found,
            "contact_sheet_path": self.contact_sheet_path,
            "frames_dir_found": self.frames_dir_found,
            "frames_dir_path": self.frames_dir_path,
            "total_frame_count": self.total_frame_count,
            "unique_frame_count": self.unique_frame_count,
            "duplicate_frame_count": self.duplicate_frame_count,
            "duplicate_static_ratio": self.duplicate_static_ratio,
            "preview_duplicate_static_frames_detected": self.preview_duplicate_static_frames_detected,
            "preview_continuity_passed": self.preview_continuity_passed,
            "contact_sheet_useful": self.contact_sheet_useful,
            "timeline_progression_proven": self.timeline_progression_proven,
            "preview_path_mismatch_detected": self.preview_path_mismatch_detected,
            "expected_preview_path": self.expected_preview_path,
            "actual_preview_path": self.actual_preview_path,
            "blocker_required": self.blocker_required,
            "audit_timestamp": self.audit_timestamp or datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Voice Rejection Record
# ---------------------------------------------------------------------------

@dataclass
class VoiceRejectionRecord:
    """Canonical record of voice rejection status."""
    voice_status: str = "operator_rejected"
    voice_generation_ready: bool = False
    voice_generation_allowed: bool = False
    voice_stage_allowed: bool = False
    audio_stage_allowed: bool = False
    assembly_allowed: bool = False
    downstream_allowed: bool = False
    production_accepted: bool = False
    operator_decision_verified: bool = False
    operator_decision_source: Optional[str] = None
    rejection_timestamp: str = ""
    blocking_artifacts: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "voice_status": self.voice_status,
            "voice_generation_ready": self.voice_generation_ready,
            "voice_generation_allowed": self.voice_generation_allowed,
            "voice_stage_allowed": self.voice_stage_allowed,
            "audio_stage_allowed": self.audio_stage_allowed,
            "assembly_allowed": self.assembly_allowed,
            "downstream_allowed": self.downstream_allowed,
            "production_accepted": self.production_accepted,
            "operator_decision_verified": self.operator_decision_verified,
            "operator_decision_source": self.operator_decision_source,
            "rejection_timestamp": self.rejection_timestamp or datetime.now(timezone.utc).isoformat(),
            "blocking_artifacts": self.blocking_artifacts,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# Post-Preview Reconciliation Report
# ---------------------------------------------------------------------------

@dataclass
class PostPreviewReconciliationReport:
    """Aggregated post-preview state reconciliation."""
    preview_valid: bool = False
    preview_reason: str = "duplicate_static_frames_detected"
    contact_sheet_useful: bool = False
    contact_sheet_reason: str = "static_or_identical_frames"
    preview_path_mismatched: bool = False
    preview_path_mismatch_detail: str = ""
    fake_operator_decision_detected: bool = False
    fake_operator_decision_invalidated: bool = False
    operator_decision_source: Optional[str] = None
    voice_rejected: bool = False
    voice_rejection_recorded: bool = False
    voice_generation_allowed: bool = False
    voice_generation_ready: bool = False
    assembly_allowed: bool = False
    downstream_allowed: bool = False
    production_accepted: bool = False
    next_safe_action: str = "preview_correction_plan_required"
    blocker_detected: bool = True
    blocker_type: str = "invalid_static_preview_and_rejected_voice"
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reconciliation_type": "post_preview_state_reconciliation",
            "preview_valid": self.preview_valid,
            "preview_reason": self.preview_reason,
            "contact_sheet_useful": self.contact_sheet_useful,
            "contact_sheet_reason": self.contact_sheet_reason,
            "preview_path_mismatched": self.preview_path_mismatched,
            "preview_path_mismatch_detail": self.preview_path_mismatch_detail,
            "fake_operator_decision_detected": self.fake_operator_decision_detected,
            "fake_operator_decision_invalidated": self.fake_operator_decision_invalidated,
            "operator_decision_source": self.operator_decision_source,
            "voice_rejected": self.voice_rejected,
            "voice_rejection_recorded": self.voice_rejection_recorded,
            "voice_generation_allowed": self.voice_generation_allowed,
            "voice_generation_ready": self.voice_generation_ready,
            "assembly_allowed": self.assembly_allowed,
            "downstream_allowed": self.downstream_allowed,
            "production_accepted": self.production_accepted,
            "next_safe_action": self.next_safe_action,
            "blocker_detected": self.blocker_detected,
            "blocker_type": self.blocker_type,
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
        }


# ---------------------------------------------------------------------------
# Blocker Report
# ---------------------------------------------------------------------------

@dataclass
class BlockerReport:
    """Canonical script supervisor blocker report."""
    blocker_detected: bool = True
    blocker_type: str = "invalid_static_preview_and_rejected_voice"
    preview_valid: bool = False
    preview_reason: str = "duplicate_static_frames_detected"
    contact_sheet_useful: bool = False
    voice_status: str = "operator_rejected"
    fake_operator_decision_valid: bool = False
    voice_generation_allowed: bool = False
    assembly_allowed: bool = False
    downstream_allowed: bool = False
    production_accepted: bool = False
    fake_success_prevented: bool = True
    recommended_next_allowed_action: str = "preview_correction_plan_required"
    blocking_details: List[str] = field(default_factory=list)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "blocker_detected": self.blocker_detected,
            "blocker_type": self.blocker_type,
            "preview_valid": self.preview_valid,
            "preview_reason": self.preview_reason,
            "contact_sheet_useful": self.contact_sheet_useful,
            "voice_status": self.voice_status,
            "fake_operator_decision_valid": self.fake_operator_decision_valid,
            "voice_generation_allowed": self.voice_generation_allowed,
            "assembly_allowed": self.assembly_allowed,
            "downstream_allowed": self.downstream_allowed,
            "production_accepted": self.production_accepted,
            "fake_success_prevented": self.fake_success_prevented,
            "recommended_next_allowed_action": self.recommended_next_allowed_action,
            "blocking_details": self.blocking_details,
            "timestamp": self.timestamp or datetime.now(timezone.utc).isoformat(),
        }
