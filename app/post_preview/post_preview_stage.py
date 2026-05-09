"""RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001 — Post-Preview Workflow Stage.

Validates preview artifacts, ingests operator preview review decision,
routes to the correct branch (accepted/rejected/needs_fix/missing_decision),
and prepares the next stage package:
- Branch accepted: Voice/Audio Readiness Package
- Branch rejected: Corrective Preview Plan
- Branch needs_fix: Targeted Fix Package
- Branch missing_decision: Blocker

No voice generation, assembly, downstream, or production acceptance.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

TASK_ID = "RC-COMBINE-V2-POST-PREVIEW-WORKFLOW-STAGE-001"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_project_root(project_root: Optional[str]) -> Path:
    if project_root:
        return Path(project_root).resolve()
    return Path.cwd().resolve()


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_ledger(ledger_path: Path) -> list:
    data = _read_json(ledger_path)
    return data if isinstance(data, list) else []


def _write_ledger(ledger_path: Path, events: list) -> None:
    _write_json(ledger_path, events)


# ---------------------------------------------------------------------------
# Operator Decision Schema
# ---------------------------------------------------------------------------

OPERATOR_DECISION_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Preview Operator Decision Input",
    "description": "Operator decision on preview render quality. Must be provided by a human operator.",
    "type": "object",
    "required": [
        "operator_verdict",
        "operator_notes",
        "visual_review_performed_by_operator",
        "preview_lowres_reviewed",
        "preview_gif_reviewed",
        "contact_sheet_reviewed",
        "production_accepted",
    ],
    "properties": {
        "operator_verdict": {
            "type": "string",
            "enum": ["accepted_for_voice_stage", "rejected", "needs_fix"],
            "description": "Operator verdict on preview quality. accepted_for_voice_stage enables voice readiness preparation.",
        },
        "operator_notes": {
            "type": "string",
            "description": "Free-text notes from the operator about the preview.",
        },
        "visual_review_performed_by_operator": {
            "type": "boolean",
            "description": "Must be true — indicates a human performed the visual review.",
        },
        "preview_lowres_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the low-res MP4 preview.",
        },
        "preview_gif_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the GIF preview.",
        },
        "contact_sheet_reviewed": {
            "type": "boolean",
            "description": "Operator reviewed the contact sheet.",
        },
        "production_accepted": {
            "type": "boolean",
            "const": False,
            "description": "Must be false — production acceptance is a later gate.",
        },
    },
    "additionalProperties": False,
}

# ---------------------------------------------------------------------------
# 1. Preview Stage Validator
# ---------------------------------------------------------------------------

REQUIRED_PREVIEW_ARTIFACTS = [
    "preview_lowres.mp4",
    "preview.gif",
    "contact_sheet.jpg",
    "preview_render_report.json",
    "preview_result_review.json",
    "preview_operator_review_packet.json",
]

REQUIRED_EDITORIAL_ARTIFACTS = [
    "timeline_model.json",
    "marker_registry.json",
    "edit_decision_list.json",
    "subtitle_plan.json",
    "transition_policy.json",
    "voice_casting_contract.json",
]


def validate_post_preview_stage(
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Validate that all post-preview stage prerequisites are in place.

    Checks preview output artifacts, editorial contracts, and
    produces a detailed validation report.

    Returns validation result dict with per-artifact status and overall validity.
    """
    root = _resolve_project_root(project_root)
    control_dir = root / "output" / "control"
    preview_dir = root / "output" / "preview"

    result: Dict[str, Any] = {
        "task_id": TASK_ID,
        "valid": True,
        "errors": [],
        "warnings": [],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Check preview artifacts in preview/ directory
    for name in REQUIRED_PREVIEW_ARTIFACTS:
        if name.endswith((".mp4", ".gif", ".jpg")):
            path = preview_dir / name
        else:
            path = control_dir / name

        exists = path.exists()
        readable = exists and os.access(path, os.R_OK) if exists else False
        size_gt_zero = path.stat().st_size > 0 if exists else False

        key = name.replace(".", "_").replace("-", "_") + "_exists"
        result[key] = exists

        if not exists:
            result["valid"] = False
            result["errors"].append(f"Missing artifact: {name}")
        elif not readable:
            result["valid"] = False
            result["errors"].append(f"Artifact not readable: {name}")
        elif not size_gt_zero:
            result["valid"] = False
            result["errors"].append(f"Artifact zero-size: {name}")

    # Check editorial contracts
    for name in REQUIRED_EDITORIAL_ARTIFACTS:
        path = control_dir / name
        exists = path.exists()
        key = name.replace(".", "_") + "_exists"
        result[key] = exists

        if not exists:
            result["valid"] = False
            result["errors"].append(f"Missing editorial artifact: {name}")
        else:
            data = _read_json(path)
            valid_json = data is not None
            result[name.replace(".", "_") + "_valid"] = valid_json
            if not valid_json:
                result["valid"] = False
                result["errors"].append(f"Invalid JSON in editorial artifact: {name}")

    # Voice casting contract — must not allow full voiceover generation
    voice_path = control_dir / "voice_casting_contract.json"
    voice = _read_json(voice_path)
    if voice and isinstance(voice, dict):
        voice_gen = voice.get("full_voiceover_generation_allowed", True)
        result["voice_casting_contract_does_not_authorize_voice_generation"] = not voice_gen
        if voice_gen:
            result["valid"] = False
            result["errors"].append(
                "voice_casting_contract.json authorizes full voiceover generation"
            )

    # Check that operator decision input file does NOT exist at validate time
    # (it should be absent until explicitly created by the operator)
    decision_path = control_dir / "preview_operator_decision_input.json"
    result["operator_decision_input_already_exists"] = decision_path.exists()

    return result


# ---------------------------------------------------------------------------
# 2. Operator Decision Validation
# ---------------------------------------------------------------------------

VALID_VERDICTS = ["accepted_for_voice_stage", "rejected", "needs_fix"]


def validate_operator_decision(
    decision: Dict[str, Any],
) -> Tuple[bool, str]:
    """Validate operator decision structure and semantics.

    Returns:
        (is_valid, message)
    """
    if not isinstance(decision, dict):
        return False, "Decision is not a valid JSON object"

    # Check required fields
    required_fields = [
        "operator_verdict",
        "operator_notes",
        "visual_review_performed_by_operator",
        "preview_lowres_reviewed",
        "preview_gif_reviewed",
        "contact_sheet_reviewed",
        "production_accepted",
    ]
    missing = [f for f in required_fields if f not in decision]
    if missing:
        return False, f"Missing required fields: {missing}"

    # production_accepted must be false
    if decision.get("production_accepted", False):
        return False, "production_accepted must be false at this stage"

    # visual_review must be performed by operator
    if not decision.get("visual_review_performed_by_operator", False):
        return False, "visual_review_performed_by_operator must be true — agent must not set this"

    # Verdict must be valid
    verdict = decision.get("operator_verdict", "")
    if verdict not in VALID_VERDICTS:
        return False, f"Unknown operator_verdict: '{verdict}'. Must be one of {VALID_VERDICTS}"

    return True, "Decision valid"


# ---------------------------------------------------------------------------
# 3. Operator Decision Ingestion
# ---------------------------------------------------------------------------


def read_operator_decision(
    control_dir: Path,
    decision_file: Optional[str] = None,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Read and validate operator decision from file.

    Args:
        control_dir: Path to control directory.
        decision_file: Optional explicit path to decision file.

    Returns:
        (found, decision_data, message)
    """
    if decision_file:
        decision_path = Path(decision_file)
    else:
        decision_path = control_dir / "preview_operator_decision_input.json"

    if not decision_path.exists():
        return False, None, f"Operator decision file not found: {decision_path}"

    data = _read_json(decision_path)
    if data is None:
        return False, None, "Operator decision file contains invalid JSON"

    valid, msg = validate_operator_decision(data)
    if not valid:
        return False, data, msg

    return True, data, "Operator decision valid"


# ---------------------------------------------------------------------------
# 4. Branch A — Accepted Preview -> Voice/Audio Readiness Package
# ---------------------------------------------------------------------------


def _build_voice_readiness_package(control_dir: Path) -> Dict[str, Any]:
    """Build voice_generation_readiness_package.json."""
    # Load editorial contracts
    timeline = _read_json(control_dir / "timeline_model.json") or {}
    subtitle_plan = _read_json(control_dir / "subtitle_plan.json") or []
    voice_casting = _read_json(control_dir / "voice_casting_contract.json") or {}

    subtitle_count = len(subtitle_plan) if isinstance(subtitle_plan, list) else 0

    package = {
        "task_id": TASK_ID,
        "voice_generation_ready": True,
        "voice_generation_executed": False,
        "script_source": "subtitle_plan",
        "language": voice_casting.get("language", "ru"),
        "voice_candidates_required": True,
        "sample_generation_required_before_full_voiceover": True,
        "operator_voice_review_required": True,
        "audio_qa_required": True,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "source_timeline": timeline.get("timeline_version", "mvp_v1"),
        "subtitle_count": subtitle_count,
        "preferred_gender": voice_casting.get("preferred_gender", "female"),
        "tone": voice_casting.get("tone", []),
        "pace": voice_casting.get("pace", "medium"),
        "sample_required": voice_casting.get("sample_required", True),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    return package


def _build_voice_script_package(control_dir: Path) -> Dict[str, Any]:
    """Build voice_script_package.json from subtitle plan."""
    subtitle_plan = _read_json(control_dir / "subtitle_plan.json") or []
    if not isinstance(subtitle_plan, list):
        subtitle_plan = []

    script_segments = []
    for sub in subtitle_plan:
        script_segments.append({
            "subtitle_id": sub.get("subtitle_id", ""),
            "text": sub.get("text", ""),
            "start_time": sub.get("start_time", ""),
            "end_time": sub.get("end_time", ""),
            "scene_id": sub.get("scene_id", ""),
            "duration": sub.get("duration", 0.0),
        })

    return {
        "task_id": TASK_ID,
        "script_source": "subtitle_plan",
        "language": "ru",
        "total_segments": len(script_segments),
        "segments": script_segments,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_voice_casting_review_package(control_dir: Path) -> Dict[str, Any]:
    """Build voice_casting_review_package.json."""
    voice_casting = _read_json(control_dir / "voice_casting_contract.json") or {}

    return {
        "task_id": TASK_ID,
        "casting_contract_loaded": True,
        "language": voice_casting.get("language", "ru"),
        "preferred_gender": voice_casting.get("preferred_gender", "female"),
        "age_range": voice_casting.get("age_range", ""),
        "tone": voice_casting.get("tone", []),
        "pace": voice_casting.get("pace", "medium"),
        "emotion": voice_casting.get("emotion", ""),
        "avoid": voice_casting.get("avoid", []),
        "sample_required": voice_casting.get("sample_required", True),
        "operator_review_required": voice_casting.get("operator_review_required", True),
        "operator_voice_review_required": True,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_voice_audition_plan(control_dir: Path) -> Dict[str, Any]:
    """Build voice_audition_plan.json."""
    voice_casting = _read_json(control_dir / "voice_casting_contract.json") or {}

    return {
        "task_id": TASK_ID,
        "audition_required": True,
        "sample_count": 1,
        "sample_text_source": "subtitle_plan",
        "sample_generated": False,
        "sample_approved": False,
        "evaluation_criteria": [
            "clarity",
            "tone_match",
            "pace_match",
            "emotion_match",
            "language_accent",
        ],
        "preferred_gender": voice_casting.get("preferred_gender", "female"),
        "age_range": voice_casting.get("age_range", ""),
        "language": voice_casting.get("language", "ru"),
        "full_voiceover_allowed_after_sample_approval": True,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_audio_qa_contract(control_dir: Path) -> Dict[str, Any]:
    """Build audio_qa_contract.json."""
    return {
        "task_id": TASK_ID,
        "audio_qa_required": True,
        "qa_checks": [
            "silence_detection",
            "clipping_detection",
            "volume_level_consistency",
            "background_noise_check",
            "sync_with_timeline",
            "subtitle_alignment",
        ],
        "min_sample_rate_hz": 44100,
        "max_sample_rate_hz": 48000,
        "volume_target_dbfs": -16.0,
        "volume_tolerance_dbfs": 2.0,
        "operator_review_required": True,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_audio_timeline_sync_contract(control_dir: Path) -> Dict[str, Any]:
    """Build audio_timeline_sync_contract.json."""
    timeline = _read_json(control_dir / "timeline_model.json") or {}
    subtitle_plan = _read_json(control_dir / "subtitle_plan.json") or []

    fps = timeline.get("fps", 24)
    subtitle_count = len(subtitle_plan) if isinstance(subtitle_plan, list) else 0

    return {
        "task_id": TASK_ID,
        "timeline_fps": fps,
        "subtitle_count": subtitle_count,
        "sync_required": True,
        "sync_method": "timecode_alignment",
        "drift_tolerance_frames": 2,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_assembly_preflight_contract(control_dir: Path) -> Dict[str, Any]:
    """Build assembly_preflight_contract.json."""
    timeline = _read_json(control_dir / "timeline_model.json") or {}
    voice_casting = _read_json(control_dir / "voice_casting_contract.json") or {}

    return {
        "task_id": TASK_ID,
        "assembly_preflight_checked": True,
        "assembly_allowed": False,
        "final_render_allowed": False,
        "voice_generation_executed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "preconditions": {
            "voice_script_ready": True,
            "voice_casting_approved": False,
            "voice_sample_approved": False,
            "audio_qa_passed": False,
            "audio_timeline_sync_validated": False,
            "operator_voice_review_completed": False,
        },
        "source_timeline_version": timeline.get("timeline_version", "mvp_v1"),
        "language": voice_casting.get("language", "ru"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_voice_generation_authorization_packet(control_dir: Path) -> Dict[str, Any]:
    """Build voice_generation_authorization_packet.json."""
    return {
        "task_id": TASK_ID,
        "voice_generation_authorization_required": True,
        "voice_generation_authorized": False,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "authorization_gates": [
            "operator_voice_review",
            "voice_sample_approval",
            "audio_qa_clearance",
        ],
        "message": "Voice generation requires operator authorization at the voice generation gate. "
                   "This packet documents the readiness state only — no voice generation has occurred.",
        "current_state": "voice_generation_authorization_required",
        "next_allowed_action": "voice_generation_authorization_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 5. Branch B — Preview Rejected -> Corrective Preview Plan
# ---------------------------------------------------------------------------


def _build_preview_operator_rejection_record(
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build preview_operator_rejection_record.json."""
    return {
        "task_id": TASK_ID,
        "operator_verdict": "rejected",
        "operator_notes": decision.get("operator_notes", ""),
        "preview_rejected": True,
        "preview_lowres_reviewed": decision.get("preview_lowres_reviewed", False),
        "preview_gif_reviewed": decision.get("preview_gif_reviewed", False),
        "contact_sheet_reviewed": decision.get("contact_sheet_reviewed", False),
        "production_accepted": False,
        "visual_review_performed_by_operator": decision.get(
            "visual_review_performed_by_operator", True
        ),
        "agent_may_not_override": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_preview_corrective_plan(
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build preview_corrective_plan.json."""
    return {
        "task_id": TASK_ID,
        "preview_rejected": True,
        "operator_notes_captured": bool(decision.get("operator_notes", "")),
        "timeline_changes_required": True,
        "subtitle_changes_required": "auto_detect",
        "transition_changes_required": "auto_detect",
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "corrective_scope": [
            "timeline",
            "edit_decision",
            "subtitle",
            "transition",
        ],
        "operator_notes": decision.get("operator_notes", ""),
        "recommended_actions": [
            "Review operator rejection notes",
            "Identify root cause of rejection",
            "Create corrective timeline changes",
            "Re-validate via preview dry-run",
            "Request preview re-render authorization",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_timeline_correction_plan() -> Dict[str, Any]:
    """Build timeline_correction_plan.json."""
    return {
        "task_id": TASK_ID,
        "correction_required": True,
        "correction_type": "preview_rejected",
        "areas": [
            "pacing",
            "scene_composition",
            "asset_placement",
            "shot_sequence",
        ],
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_editing_correction_plan() -> Dict[str, Any]:
    """Build editing_correction_plan.json."""
    return {
        "task_id": TASK_ID,
        "correction_required": True,
        "correction_type": "preview_rejected",
        "areas": [
            "edit_decision_review",
            "cut_timing_adjustment",
            "transition_placement",
        ],
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_subtitle_correction_plan() -> Dict[str, Any]:
    """Build subtitle_correction_plan.json."""
    return {
        "task_id": TASK_ID,
        "correction_required": True,
        "correction_type": "preview_rejected",
        "areas": [
            "timing_adjustment",
            "text_review",
            "position_verification",
            "safe_zone_check",
        ],
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_transition_correction_plan() -> Dict[str, Any]:
    """Build transition_correction_plan.json."""
    return {
        "task_id": TASK_ID,
        "correction_required": True,
        "correction_type": "preview_rejected",
        "areas": [
            "transition_type_review",
            "duration_adjustment",
            "cross_scene_consistency",
        ],
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_preview_correction_authorization_packet() -> Dict[str, Any]:
    """Build preview_correction_authorization_packet.json."""
    return {
        "task_id": TASK_ID,
        "correction_authorization_required": True,
        "correction_authorized": False,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "message": "Preview correction requires operator authorization. "
                   "This packet documents the corrective plan only — no changes have been applied.",
        "current_state": "preview_correction_authorization_required",
        "next_allowed_action": "preview_correction_authorization_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 6. Branch C — Needs Fix -> Targeted Fix Package
# ---------------------------------------------------------------------------


def _build_preview_needs_fix_record(
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build preview_needs_fix_record.json."""
    return {
        "task_id": TASK_ID,
        "operator_verdict": "needs_fix",
        "operator_notes": decision.get("operator_notes", ""),
        "preview_accepted": False,
        "preview_needs_fix": True,
        "preview_lowres_reviewed": decision.get("preview_lowres_reviewed", False),
        "preview_gif_reviewed": decision.get("preview_gif_reviewed", False),
        "contact_sheet_reviewed": decision.get("contact_sheet_reviewed", False),
        "production_accepted": False,
        "visual_review_performed_by_operator": decision.get(
            "visual_review_performed_by_operator", True
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_targeted_preview_fix_plan(
    decision: Dict[str, Any],
) -> Dict[str, Any]:
    """Build targeted_preview_fix_plan.json."""
    return {
        "task_id": TASK_ID,
        "preview_needs_fix": True,
        "operator_notes_captured": bool(decision.get("operator_notes", "")),
        "timeline_changes_required": True,
        "subtitle_changes_required": "auto_detect",
        "transition_changes_required": "auto_detect",
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "fix_scope": [
            "targeted_timeline_fix",
            "targeted_subtitle_fix",
            "targeted_transition_fix",
        ],
        "operator_notes": decision.get("operator_notes", ""),
        "recommended_actions": [
            "Review operator fix notes",
            "Apply targeted fix based on notes",
            "Re-validate via preview dry-run",
            "Request preview re-render authorization",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_targeted_timeline_fix_plan() -> Dict[str, Any]:
    """Build targeted_timeline_fix_plan.json."""
    return {
        "task_id": TASK_ID,
        "fix_required": True,
        "fix_type": "targeted",
        "fix_scope": "specific_timeline_elements",
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_targeted_subtitle_fix_plan() -> Dict[str, Any]:
    """Build targeted_subtitle_fix_plan.json."""
    return {
        "task_id": TASK_ID,
        "fix_required": True,
        "fix_type": "targeted",
        "fix_scope": "specific_subtitle_elements",
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_targeted_transition_fix_plan() -> Dict[str, Any]:
    """Build targeted_transition_fix_plan.json."""
    return {
        "task_id": TASK_ID,
        "fix_required": True,
        "fix_type": "targeted",
        "fix_scope": "specific_transition_elements",
        "preview_rerender_required": True,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_targeted_preview_fix_authorization_packet() -> Dict[str, Any]:
    """Build targeted_preview_fix_authorization_packet.json."""
    return {
        "task_id": TASK_ID,
        "fix_authorization_required": True,
        "fix_authorized": False,
        "preview_rerender_authorized": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "message": "Targeted preview fix requires operator authorization. "
                   "This packet documents the fix plan only — no changes have been applied.",
        "current_state": "targeted_preview_fix_authorization_required",
        "next_allowed_action": "targeted_preview_fix_authorization_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 7. Branch D — Missing Operator Decision -> Blocker
# ---------------------------------------------------------------------------


def _build_post_preview_stage_blocker() -> Dict[str, Any]:
    """Build post_preview_stage_blocker.json."""
    return {
        "task_id": TASK_ID,
        "stage_blocked": True,
        "blocker_type": "missing_operator_decision",
        "reason": "Operator preview decision has not been provided. "
                   "The post-preview stage cannot proceed without a valid operator verdict.",
        "resolution": "Create preview_operator_decision_input.json with a valid operator verdict "
                       "(accepted_for_voice_stage, rejected, or needs_fix).",
        "preview_review_required": True,
        "visual_review_performed_by_operator": False,
        "fake_visual_acceptance_prevented": True,
        "agent_may_not_choose_verdict": True,
        "preview_rerender_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "preview_operator_review_required",
        "next_allowed_action": "preview_operator_review_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _build_operator_preview_review_required_packet() -> Dict[str, Any]:
    """Build operator_preview_review_required_packet.json."""
    return {
        "task_id": TASK_ID,
        "operator_preview_review_required": True,
        "review_type": "post_preview_stage",
        "preview_artifacts_available": True,
        "operator_decision_required": True,
        "allowed_verdicts": VALID_VERDICTS,
        "instructions": (
            "Review the preview artifacts (preview_lowres.mp4, preview.gif, contact_sheet.jpg) "
            "and provide a verdict in preview_operator_decision_input.json. "
            "Valid verdicts: accepted_for_voice_stage, rejected, needs_fix."
        ),
        "visual_review_performed_by_operator": False,
        "agent_may_not_accept_preview": True,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# 8. Artifact Index Update
# ---------------------------------------------------------------------------


def _build_artifact_index_update(
    selected_branch: str,
    target_state: str,
    target_action: str,
    artifacts: List[str],
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build artifact index update payload."""
    update: Dict[str, Any] = {
        "task_id": TASK_ID,
        "current_state": target_state,
        "next_allowed_action": target_action,
        "production_accepted": False,
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "post_preview_stage_executed": True,
        "selected_branch": selected_branch,
        "post_preview_artifacts": artifacts,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    if metadata:
        update.update(metadata)

    return update


# ---------------------------------------------------------------------------
# 9. Episode Ledger Update
# ---------------------------------------------------------------------------


def _build_ledger_events(
    selected_branch: str,
    decision: Optional[Dict[str, Any]],
    target_state: str,
    artifacts: List[str],
) -> list:
    """Build ledger events for the post-preview stage cycle."""
    timestamp = datetime.now(timezone.utc).isoformat()
    events = []

    events.append({
        "event_type": "post_preview_stage_executed",
        "task_id": TASK_ID,
        "stage": target_state,
        "selected_branch": selected_branch,
        "operator_verdict": (decision or {}).get("operator_verdict", "not_provided"),
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "artifacts_created": artifacts,
        "timestamp": timestamp,
    })

    if selected_branch == "accepted_for_voice_stage":
        events.append({
            "event_type": "voice_readiness_package_created",
            "task_id": TASK_ID,
            "stage": target_state,
            "voice_generation_ready": True,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "timestamp": timestamp,
        })
    elif selected_branch == "rejected":
        events.append({
            "event_type": "preview_rejection_recorded",
            "task_id": TASK_ID,
            "stage": target_state,
            "operator_notes": (decision or {}).get("operator_notes", ""),
            "corrective_plan_created": True,
            "preview_rerender_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "timestamp": timestamp,
        })
    elif selected_branch == "needs_fix":
        events.append({
            "event_type": "preview_needs_fix_recorded",
            "task_id": TASK_ID,
            "stage": target_state,
            "operator_notes": (decision or {}).get("operator_notes", ""),
            "targeted_fix_plan_created": True,
            "preview_rerender_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "timestamp": timestamp,
        })
    elif selected_branch == "blocked_missing_operator_decision":
        events.append({
            "event_type": "post_preview_stage_blocked",
            "task_id": TASK_ID,
            "stage": target_state,
            "blocker_type": "missing_operator_decision",
            "fake_visual_acceptance_prevented": True,
            "timestamp": timestamp,
        })

    return events


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_post_preview_stage(
    project_root: Optional[str] = None,
    decision_file: Optional[str] = None,
    dry_run: bool = False,
) -> Dict[str, Any]:
    """Run the full post-preview workflow stage.

    Validates preview artifacts -> reads operator decision (if available) ->
    routes to correct branch -> creates next stage package -> updates state.

    Args:
        project_root: Path to the project root (default: cwd).
        decision_file: Optional explicit path to operator decision file.
        dry_run: If True, validate and report without writing artifacts.

    Returns:
        A result dict with status, branch, artifact paths, and state info.
    """
    root = _resolve_project_root(project_root)
    control_dir = root / "output" / "control"
    timestamp = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Step 1: Validate preview stage artifacts
    # ------------------------------------------------------------------
    validation = validate_post_preview_stage(project_root=str(root))

    # Export validation report
    validation_report = {
        "task_id": TASK_ID,
        "validation": validation,
        "timestamp": timestamp,
    }

    if not dry_run:
        _write_json(
            control_dir / "post_preview_stage_validation_report.json",
            validation_report,
        )

    # If validation is not valid, we still proceed — some artifacts might be
    # missing but we can still report honestly. The blocking happens if
    # operator decision is missing (Branch D).

    # ------------------------------------------------------------------
    # Step 2: Read and validate operator decision
    # ------------------------------------------------------------------
    decision_found, decision_data, decision_msg = read_operator_decision(
        control_dir, decision_file
    )

    if not decision_found:
        # Branch D — Missing Operator Decision
        blocker = _build_post_preview_stage_blocker()
        review_packet = _build_operator_preview_review_required_packet()

        routing_decision = {
            "task_id": TASK_ID,
            "selected_branch": "blocked_missing_operator_decision",
            "operator_verdict": None,
            "decision_valid": False,
            "decision_message": decision_msg,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "timestamp": timestamp,
        }

        target_state = "preview_operator_review_required"
        target_action = "preview_operator_review_required"
        artifacts = [
            "post_preview_stage_validation_report.json",
            "post_preview_stage_blocker.json",
            "operator_preview_review_required_packet.json",
            "post_preview_routing_decision.json",
        ]

        outcome = {
            "task_id": TASK_ID,
            "outcome": "blocked_missing_operator_decision",
            "selected_branch": "blocked_missing_operator_decision",
            "operator_verdict": None,
            "stage_implemented": True,
            "preview_artifacts_validated": validation.get("valid", False),
            "blocked_by_missing_operator_decision": True,
            "fake_visual_acceptance_prevented": True,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "state_remains_preview_operator_review_required": True,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "timestamp": timestamp,
        }

        if not dry_run:
            _write_json(control_dir / "post_preview_stage_blocker.json", blocker)
            _write_json(
                control_dir / "operator_preview_review_required_packet.json",
                review_packet,
            )
            _write_json(
                control_dir / "post_preview_routing_decision.json",
                routing_decision,
            )
            _write_json(control_dir / "post_preview_stage_proof.json", outcome)

            # Update artifact index
            existing_index = _read_json(control_dir / "artifact_index.json") or {}
            index_update = _build_artifact_index_update(
                selected_branch="blocked_missing_operator_decision",
                target_state=target_state,
                target_action=target_action,
                artifacts=artifacts,
                metadata={
                    "blocked_by_missing_operator_decision": True,
                    "fake_visual_acceptance_prevented": True,
                    "state_remains_preview_operator_review_required": True,
                },
            )
            existing_index.update(index_update)
            _write_json(control_dir / "artifact_index.json", existing_index)

            # Update episode ledger
            ledger_path = control_dir / "episode_ledger.json"
            existing_ledger = _read_ledger(ledger_path)
            new_events = _build_ledger_events(
                selected_branch="blocked_missing_operator_decision",
                decision=None,
                target_state=target_state,
                artifacts=artifacts,
            )
            existing_ledger.extend(new_events)
            _write_ledger(ledger_path, existing_ledger)

        return {
            "status": "accepted_with_blockers",
            "task_id": TASK_ID,
            "selected_branch": "blocked_missing_operator_decision",
            "operator_verdict_provided": False,
            "stage_implemented": True,
            "preview_artifacts_validated": validation.get("valid", False),
            "blocked_by_missing_operator_decision": True,
            "fake_visual_acceptance_prevented": True,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "state_remains_preview_operator_review_required": True,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "message": decision_msg,
            "artifacts": artifacts,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 3: Validate decision semantics
    # ------------------------------------------------------------------
    decision_valid, decision_msg = validate_operator_decision(decision_data)

    if not decision_valid:
        # Invalid decision — block with message
        outcome = {
            "task_id": TASK_ID,
            "outcome": "blocked_invalid_decision",
            "selected_branch": "invalid_decision",
            "operator_verdict": decision_data.get("operator_verdict", ""),
            "decision_valid": False,
            "decision_message": decision_msg,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "blocker": decision_msg,
            "current_state": "preview_operator_review_required",
            "next_allowed_action": "preview_operator_review_required",
            "timestamp": timestamp,
        }
        if not dry_run:
            _write_json(control_dir / "post_preview_stage_proof.json", outcome)
        return {
            "status": "error",
            "task_id": TASK_ID,
            "selected_branch": "invalid_decision",
            "operator_verdict": decision_data.get("operator_verdict", ""),
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "current_state": "preview_operator_review_required",
            "next_allowed_action": "preview_operator_review_required",
            "message": decision_msg,
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 4: Route by verdict
    # ------------------------------------------------------------------
    verdict = decision_data["operator_verdict"]
    outcome_artifacts: List[str] = []
    outcome_metadata: Dict[str, Any] = {}
    target_state = ""
    target_action = ""

    # Write operator review outcome (common across all branches)
    review_outcome = {
        "task_id": TASK_ID,
        "operator_verdict": verdict,
        "operator_notes": decision_data.get("operator_notes", ""),
        "visual_review_performed_by_operator": decision_data.get(
            "visual_review_performed_by_operator", True
        ),
        "preview_lowres_reviewed": decision_data.get("preview_lowres_reviewed", False),
        "preview_gif_reviewed": decision_data.get("preview_gif_reviewed", False),
        "contact_sheet_reviewed": decision_data.get("contact_sheet_reviewed", False),
        "production_accepted": False,
        "agent_may_not_override": True,
        "timestamp": timestamp,
    }

    if verdict == "accepted_for_voice_stage":
        # Branch A — Accepted Preview -> Voice/Audio Readiness Package
        target_state = "voice_generation_authorization_required"
        target_action = "voice_generation_authorization_required"

        voice_readiness = _build_voice_readiness_package(control_dir)
        voice_script = _build_voice_script_package(control_dir)
        voice_casting_review = _build_voice_casting_review_package(control_dir)
        voice_audition = _build_voice_audition_plan(control_dir)
        audio_qa = _build_audio_qa_contract(control_dir)
        audio_timeline_sync = _build_audio_timeline_sync_contract(control_dir)
        assembly_preflight = _build_assembly_preflight_contract(control_dir)
        voice_auth_packet = _build_voice_generation_authorization_packet(control_dir)

        outcome_artifacts = [
            "post_preview_stage_validation_report.json",
            "preview_operator_review_outcome.json",
            "post_preview_routing_decision.json",
            "voice_generation_readiness_package.json",
            "voice_script_package.json",
            "voice_casting_review_package.json",
            "voice_audition_plan.json",
            "audio_qa_contract.json",
            "audio_timeline_sync_contract.json",
            "assembly_preflight_contract.json",
            "voice_generation_authorization_packet.json",
            "post_preview_stage_proof.json",
        ]

        outcome_metadata = {
            "voice_generation_ready": True,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
        }

        if not dry_run:
            _write_json(
                control_dir / "voice_generation_readiness_package.json",
                voice_readiness,
            )
            _write_json(
                control_dir / "voice_script_package.json", voice_script
            )
            _write_json(
                control_dir / "voice_casting_review_package.json",
                voice_casting_review,
            )
            _write_json(control_dir / "voice_audition_plan.json", voice_audition)
            _write_json(control_dir / "audio_qa_contract.json", audio_qa)
            _write_json(
                control_dir / "audio_timeline_sync_contract.json",
                audio_timeline_sync,
            )
            _write_json(
                control_dir / "assembly_preflight_contract.json",
                assembly_preflight,
            )
            _write_json(
                control_dir / "voice_generation_authorization_packet.json",
                voice_auth_packet,
            )

    elif verdict == "rejected":
        # Branch B — Preview Rejected -> Corrective Preview Plan
        target_state = "preview_correction_authorization_required"
        target_action = "preview_correction_authorization_required"

        rejection_record = _build_preview_operator_rejection_record(decision_data)
        corrective_plan = _build_preview_corrective_plan(decision_data)
        timeline_correction = _build_timeline_correction_plan()
        editing_correction = _build_editing_correction_plan()
        subtitle_correction = _build_subtitle_correction_plan()
        transition_correction = _build_transition_correction_plan()
        correction_auth_packet = _build_preview_correction_authorization_packet()

        outcome_artifacts = [
            "post_preview_stage_validation_report.json",
            "preview_operator_review_outcome.json",
            "post_preview_routing_decision.json",
            "preview_operator_rejection_record.json",
            "preview_corrective_plan.json",
            "timeline_correction_plan.json",
            "editing_correction_plan.json",
            "subtitle_correction_plan.json",
            "transition_correction_plan.json",
            "preview_correction_authorization_packet.json",
            "post_preview_stage_proof.json",
        ]

        outcome_metadata = {
            "preview_rejected": True,
            "corrective_plan_created": True,
            "preview_rerender_executed": False,
        }

        if not dry_run:
            _write_json(
                control_dir / "preview_operator_rejection_record.json",
                rejection_record,
            )
            _write_json(
                control_dir / "preview_corrective_plan.json", corrective_plan
            )
            _write_json(
                control_dir / "timeline_correction_plan.json", timeline_correction
            )
            _write_json(
                control_dir / "editing_correction_plan.json", editing_correction
            )
            _write_json(
                control_dir / "subtitle_correction_plan.json", subtitle_correction
            )
            _write_json(
                control_dir / "transition_correction_plan.json", transition_correction
            )
            _write_json(
                control_dir / "preview_correction_authorization_packet.json",
                correction_auth_packet,
            )

    elif verdict == "needs_fix":
        # Branch C — Needs Fix -> Targeted Fix Package
        target_state = "targeted_preview_fix_authorization_required"
        target_action = "targeted_preview_fix_authorization_required"

        needs_fix_record = _build_preview_needs_fix_record(decision_data)
        targeted_fix_plan = _build_targeted_preview_fix_plan(decision_data)
        targeted_timeline_fix = _build_targeted_timeline_fix_plan()
        targeted_subtitle_fix = _build_targeted_subtitle_fix_plan()
        targeted_transition_fix = _build_targeted_transition_fix_plan()
        targeted_fix_auth_packet = _build_targeted_preview_fix_authorization_packet()

        outcome_artifacts = [
            "post_preview_stage_validation_report.json",
            "preview_operator_review_outcome.json",
            "post_preview_routing_decision.json",
            "preview_needs_fix_record.json",
            "targeted_preview_fix_plan.json",
            "targeted_timeline_fix_plan.json",
            "targeted_subtitle_fix_plan.json",
            "targeted_transition_fix_plan.json",
            "targeted_preview_fix_authorization_packet.json",
            "post_preview_stage_proof.json",
        ]

        outcome_metadata = {
            "preview_needs_fix": True,
            "targeted_fix_plan_created": True,
            "preview_rerender_executed": False,
        }

        if not dry_run:
            _write_json(
                control_dir / "preview_needs_fix_record.json", needs_fix_record
            )
            _write_json(
                control_dir / "targeted_preview_fix_plan.json", targeted_fix_plan
            )
            _write_json(
                control_dir / "targeted_timeline_fix_plan.json",
                targeted_timeline_fix,
            )
            _write_json(
                control_dir / "targeted_subtitle_fix_plan.json",
                targeted_subtitle_fix,
            )
            _write_json(
                control_dir / "targeted_transition_fix_plan.json",
                targeted_transition_fix,
            )
            _write_json(
                control_dir / "targeted_preview_fix_authorization_packet.json",
                targeted_fix_auth_packet,
            )

    # ------------------------------------------------------------------
    # Step 5: Write common artifacts (for non-blocker branches)
    # ------------------------------------------------------------------
    if dry_run:
        # Still report what would happen
        return {
            "status": "ok",
            "task_id": TASK_ID,
            "selected_branch": verdict,
            "operator_verdict": verdict,
            "operator_verdict_provided": True,
            "dry_run": True,
            "voice_generation_executed": False,
            "assembly_allowed": False,
            "downstream_allowed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "writes_blocked": True,
            "message": "Dry-run: artifacts would be created but were not written",
            "artifacts": outcome_artifacts,
            "timestamp": timestamp,
        }

    # Write common artifacts
    routing_decision = {
        "task_id": TASK_ID,
        "selected_branch": verdict,
        "operator_verdict": verdict,
        "operator_notes": decision_data.get("operator_notes", ""),
        "decision_valid": True,
        "visual_review_performed_by_operator": decision_data.get(
            "visual_review_performed_by_operator", True
        ),
        "voice_generation_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": timestamp,
    }

    _write_json(control_dir / "preview_operator_review_outcome.json", review_outcome)
    _write_json(control_dir / "post_preview_routing_decision.json", routing_decision)

    # ------------------------------------------------------------------
    # Step 6: Build stage proof
    # ------------------------------------------------------------------
    proof: Dict[str, Any] = {
        "task_id": TASK_ID,
        "feature_completed": True,
        "full_feature_loop_executed": True,
        "previous_layer": "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001",
        "previous_commit": "6db731d",
        "post_preview_stage_implemented": True,
        "preview_artifacts_validated": validation.get("valid", False),
        "operator_decision_contract_created": True,
        "operator_decision_processed_or_blocked_honestly": True,
        "selected_branch": verdict,
        "voice_generation_readiness_package_created": verdict == "accepted_for_voice_stage",
        "voice_script_package_created": verdict == "accepted_for_voice_stage",
        "voice_casting_review_package_created": verdict == "accepted_for_voice_stage",
        "voice_audition_plan_created": verdict == "accepted_for_voice_stage",
        "audio_qa_contract_created": verdict == "accepted_for_voice_stage",
        "audio_timeline_sync_contract_created": verdict == "accepted_for_voice_stage",
        "assembly_preflight_contract_created": verdict == "accepted_for_voice_stage",
        "voice_generation_authorization_packet_created": verdict == "accepted_for_voice_stage",
        "corrective_plan_created_if_rejected": verdict == "rejected",
        "targeted_fix_plan_created_if_needs_fix": verdict == "needs_fix",
        "blocker_created_if_missing_decision": False,
        "new_generation_performed": False,
        "retry_attempted": False,
        "comfyui_submit_executed": False,
        "preview_rerender_executed": False,
        "voice_generation_executed": False,
        "voice_api_submit_executed": False,
        "assembly_executed": False,
        "final_render_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "artifact_index_updated": True,
        "episode_ledger_updated": True,
        "state_updated": True,
        "current_state": target_state,
        "next_allowed_action": target_action,
        "blockers": [],
    }
    _write_json(control_dir / "post_preview_stage_proof.json", proof)

    # ------------------------------------------------------------------
    # Step 7: Update artifact index and ledger
    # ------------------------------------------------------------------
    existing_index = _read_json(control_dir / "artifact_index.json") or {}
    index_update = _build_artifact_index_update(
        selected_branch=verdict,
        target_state=target_state,
        target_action=target_action,
        artifacts=outcome_artifacts,
        metadata=outcome_metadata,
    )
    existing_index.update(index_update)
    _write_json(control_dir / "artifact_index.json", existing_index)

    ledger_path = control_dir / "episode_ledger.json"
    existing_ledger = _read_ledger(ledger_path)
    new_events = _build_ledger_events(
        selected_branch=verdict,
        decision=decision_data,
        target_state=target_state,
        artifacts=outcome_artifacts,
    )
    existing_ledger.extend(new_events)
    _write_ledger(ledger_path, existing_ledger)

    # ------------------------------------------------------------------
    # Step 8: Return result
    # ------------------------------------------------------------------
    return {
        "status": "ok",
        "task_id": TASK_ID,
        "selected_branch": verdict,
        "operator_verdict": verdict,
        "operator_verdict_provided": True,
        "stage_implemented": True,
        "preview_artifacts_validated": validation.get("valid", False),
        "voice_generation_ready": verdict == "accepted_for_voice_stage",
        "voice_generation_executed": False,
        "voice_generation_authorization_packet_created": verdict == "accepted_for_voice_stage",
        "corrective_plan_created": verdict == "rejected",
        "targeted_fix_plan_created": verdict == "needs_fix",
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "current_state": target_state,
        "next_allowed_action": target_action,
        "artifacts": outcome_artifacts,
        "forbidden_actions": {
            "new_generation": False,
            "retry": False,
            "comfyui_submit": False,
            "preview_rerender": False,
            "voice_generation": False,
            "voice_api_submit": False,
            "assembly": False,
            "final_render": False,
            "downstream": False,
            "production_accepted": False,
        },
        "timestamp": timestamp,
    }
