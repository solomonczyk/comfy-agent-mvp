"""Preview and operator decision audit logic for the Script Supervisor agent.

Provides safe read-only audit functions that:
  - Detect duplicate/static frames in preview outputs
  - Validate contact sheet usefulness
  - Check path consistency (output/preview vs output/previews)
  - Verify operator decision authenticity
  - Record voice rejection state
  - Produce blocker reports
"""

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from app.agents.film_crew.contracts import (
    PreviewAuditReport,
    VoiceRejectionRecord,
    PostPreviewReconciliationReport,
    BlockerReport,
)


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _control_path(project_root: str) -> str:
    return os.path.join(project_root, "output", "control")


def _preview_path(project_root: str) -> str:
    return os.path.join(project_root, "output", "preview")


def _previews_path(project_root: str) -> str:
    return os.path.join(project_root, "output", "previews")


# ---------------------------------------------------------------------------
# Preview Audit
# ---------------------------------------------------------------------------

def audit_preview_frames(project_root: str, max_sample: Optional[int] = None) -> PreviewAuditReport:
    """Audit preview frames for duplicate/static content.

    Safely reads frame files and computes SHA256 hashes to detect duplicates.
    Never modifies any files.
    """
    report = PreviewAuditReport()
    report.audit_timestamp = datetime.now(timezone.utc).isoformat()

    preview_dir = _preview_path(project_root)
    report.expected_preview_path = "output/preview"
    report.actual_preview_path = "output/preview"

    # Check if output/previews path exists (path mismatch detection)
    alt_preview_dir = _previews_path(project_root)
    if os.path.isdir(alt_preview_dir):
        # Both paths exist — but preview render report says output/preview
        report.preview_path_mismatch_detected = True
        report.actual_preview_path = "output/preview and output/previews (both exist)"

    # Check main artifacts
    preview_mp4 = os.path.join(preview_dir, "preview_lowres.mp4")
    preview_gif = os.path.join(preview_dir, "preview.gif")
    contact_sheet = os.path.join(preview_dir, "contact_sheet.jpg")
    frames_dir = os.path.join(preview_dir, "frames")

    report.preview_found = os.path.isfile(preview_mp4)
    report.preview_path = preview_mp4 if report.preview_found else None
    report.preview_gif_found = os.path.isfile(preview_gif)
    report.preview_gif_path = preview_gif if report.preview_gif_found else None
    report.contact_sheet_found = os.path.isfile(contact_sheet)
    report.contact_sheet_path = contact_sheet if report.contact_sheet_found else None
    report.frames_dir_found = os.path.isdir(frames_dir)
    report.frames_dir_path = frames_dir if report.frames_dir_found else None

    if not report.frames_dir_found:
        report.blocker_required = True
        return report

    # Get sorted frame files
    frame_files = sorted(
        [f for f in os.listdir(frames_dir) if f.endswith(".png")],
        key=lambda x: int(''.join(c for c in x if c.isdigit()) or 0),
    )
    report.total_frame_count = len(frame_files)

    # If there are no frames, note that
    if report.total_frame_count == 0:
        report.blocker_required = True
        return report

    # Sample or full scan for duplicate detection
    files_to_check = frame_files
    if max_sample and len(frame_files) > max_sample:
        # Strategic sampling: first frame + evenly spaced
        step = max(1, len(frame_files) // max_sample)
        files_to_check = [frame_files[0]] + frame_files[1:-1:step] + [frame_files[-1]]
        files_to_check = sorted(set(files_to_check), key=frame_files.index)

    # Compute hashes
    frame_hashes: Dict[str, List[str]] = {}
    for fname in files_to_check:
        fpath = os.path.join(frames_dir, fname)
        try:
            with open(fpath, "rb") as fh:
                h = hashlib.sha256(fh.read()).hexdigest()
            frame_hashes.setdefault(h, []).append(fname)
        except (IOError, OSError):
            continue

    # If we sampled, estimate total duplicates
    if max_sample and len(frame_files) > max_sample:
        # Use hash ratio from sample
        unique_in_sample = len(frame_hashes)
        sampled_count = len(files_to_check)
        if sampled_count > 0:
            estimated_unique = int(unique_in_sample / sampled_count * report.total_frame_count)
            report.unique_frame_count = max(1, min(estimated_unique, report.total_frame_count))
            report.duplicate_frame_count = report.total_frame_count - report.unique_frame_count
    else:
        report.unique_frame_count = len(frame_hashes)
        report.duplicate_frame_count = report.total_frame_count - report.unique_frame_count

    report.duplicate_static_ratio = (
        report.duplicate_frame_count / report.total_frame_count
        if report.total_frame_count > 0 else 0.0
    )

    # Determine if this is a static / duplicate preview
    DUP_THRESHOLD = 0.5  # 50% duplicate = suspicious
    STATIC_THRESHOLD = 0.9  # 90% duplicate = effectively static

    if report.duplicate_static_ratio >= STATIC_THRESHOLD:
        report.preview_duplicate_static_frames_detected = True
        report.preview_continuity_passed = False
        report.blocker_required = True
    elif report.duplicate_static_ratio >= DUP_THRESHOLD:
        report.preview_duplicate_static_frames_detected = True
        report.preview_continuity_passed = False
        report.blocker_required = True
    else:
        report.preview_duplicate_static_frames_detected = False
        report.preview_continuity_passed = True
        report.blocker_required = False

    # Contact sheet usefulness: if duplicate ratio is high, contact sheet
    # does not prove timeline progression even if the file exists
    if report.contact_sheet_found and report.duplicate_static_ratio >= DUP_THRESHOLD:
        report.contact_sheet_useful = False
        report.timeline_progression_proven = False
    elif report.contact_sheet_found and report.duplicate_static_ratio < DUP_THRESHOLD:
        report.contact_sheet_useful = True
        report.timeline_progression_proven = True
    else:
        report.contact_sheet_useful = False
        report.timeline_progression_proven = False

    return report


# ---------------------------------------------------------------------------
# Operator Decision Guard
# ---------------------------------------------------------------------------

def check_operator_decision_authenticity(project_root: str) -> Dict[str, Any]:
    """Verify that no operator decision was faked by agent/CLI/test.

    Checks existing operator decision artifacts and reports authenticity.
    Never modifies any files.
    """
    ctrl = _control_path(project_root)
    result = {
        "fake_operator_decision_detected": False,
        "operator_decision_valid": False,
        "accepted_for_voice_stage_blocked": True,
        "human_operator_decision_found": False,
        "agent_generated_decision_found": False,
        "invalidation_verified": False,
        "artifacts_checked": [],
        "details": [],
    }

    # Check post_preview_routing_decision.json
    routing_decision_path = os.path.join(ctrl, "post_preview_routing_decision.json")
    if os.path.isfile(routing_decision_path):
        result["artifacts_checked"].append("post_preview_routing_decision.json")
        try:
            with open(routing_decision_path, "r", encoding="utf-8") as f:
                rd = json.load(f)
            decision_valid = rd.get("decision_valid", False)
            op_review = rd.get("visual_review_performed_by_operator", False)
            selected = rd.get("selected_branch", "")

            if not decision_valid and not op_review:
                result["fake_operator_decision_detected"] = True
                result["agent_generated_decision_found"] = True
                result["invalidation_verified"] = True
                result["details"].append(
                    "post_preview_routing_decision.json: decision_valid=false, "
                    "visual_review_performed_by_operator=false. Invalidation confirmed."
                )
            elif selected == "invalid_agent_generated_decision":
                result["fake_operator_decision_detected"] = True
                result["agent_generated_decision_found"] = True
                result["invalidation_verified"] = True
                result["details"].append(
                    "post_preview_routing_decision.json: branch=invalid_agent_generated_decision. "
                    "Fake decision already invalidated."
                )
            else:
                result["details"].append(
                    f"post_preview_routing_decision.json: decision_valid={decision_valid}, "
                    f"visual_review_performed_by_operator={op_review}"
                )
        except (json.JSONDecodeError, IOError) as e:
            result["details"].append(f"Could not read post_preview_routing_decision.json: {e}")

    # Check reconciliation artifact
    reconciliation_path = os.path.join(ctrl, "post_preview_operator_decision_reconciliation.json")
    if os.path.isfile(reconciliation_path):
        result["artifacts_checked"].append("post_preview_operator_decision_reconciliation.json")
        try:
            with open(reconciliation_path, "r", encoding="utf-8") as f:
                rec = json.load(f)
            if rec.get("detection", {}).get("agent_may_not_choose_verdict_violation"):
                result["fake_operator_decision_detected"] = True
                result["agent_generated_decision_found"] = True
                result["invalidation_verified"] = True
                result["details"].append(
                    "Reconciliation confirms agent_may_not_choose_verdict_violation. "
                    "Fake operator decision properly invalidated."
                )
        except (json.JSONDecodeError, IOError) as e:
            result["details"].append(f"Could not read reconciliation artifact: {e}")

    # Check preview operator decision input - if not present, no real decision
    decision_input_path = os.path.join(ctrl, "preview_operator_decision_input.json")
    if os.path.isfile(decision_input_path):
        result["artifacts_checked"].append("preview_operator_decision_input.json")
        try:
            with open(decision_input_path, "r", encoding="utf-8") as f:
                di = json.load(f)
            source = di.get("operator_id") or di.get("source", "")
            if source and source != "agent" and source != "cli_verification":
                result["human_operator_decision_found"] = True
                result["operator_decision_valid"] = True
                result["accepted_for_voice_stage_blocked"] = False
            else:
                result["details"].append("Operator decision input exists but source is agent/CLI.")
        except (json.JSONDecodeError, IOError) as e:
            result["details"].append(f"Could not read decision input: {e}")
    else:
        result["details"].append("No preview_operator_decision_input.json found. "
                                 "No human operator decision was provided.")

    # Final determination
    result["operator_decision_valid"] = result["human_operator_decision_found"]
    result["accepted_for_voice_stage_blocked"] = not result["human_operator_decision_found"]

    return result


# ---------------------------------------------------------------------------
# Voice Rejection Record Builder
# ---------------------------------------------------------------------------

def build_voice_rejection_record(project_root: str) -> VoiceRejectionRecord:
    """Build a voice rejection record from existing artifacts."""
    ctrl = _control_path(project_root)
    record = VoiceRejectionRecord()
    record.rejection_timestamp = datetime.now(timezone.utc).isoformat()
    record.operator_decision_source = "no_real_operator_decision"

    # Collect blocking artifacts
    for art_name in [
        "post_preview_routing_decision.json",
        "post_preview_operator_decision_reconciliation.json",
        "post_preview_stage_blocker.json",
        "post_preview_stage_proof.json",
    ]:
        art_path = os.path.join(ctrl, art_name)
        if os.path.isfile(art_path):
            record.blocking_artifacts.append(art_name)

    # Check for real operator decision artifact
    decision_input_path = os.path.join(ctrl, "preview_operator_decision_input.json")
    if os.path.isfile(decision_input_path):
        try:
            with open(decision_input_path, "r", encoding="utf-8") as f:
                di = json.load(f)
            source = di.get("operator_id") or di.get("source", "")
            if source and source != "agent" and source != "cli_verification":
                record.operator_decision_verified = True
                record.operator_decision_source = source
        except (json.JSONDecodeError, IOError):
            pass

    # Voice rejection notes
    record.notes = [
        "Voice generation is blocked: no valid human operator decision exists",
        "accepted_for_voice_stage was agent-generated and has been invalidated",
        "voice_generation_ready flag remains false",
        "All downstream voice/audio/assembly steps are blocked until a real operator decision is recorded",
    ]

    return record


# ---------------------------------------------------------------------------
# Post-Preview Reconciliation
# ---------------------------------------------------------------------------

def build_post_preview_reconciliation(
    project_root: str,
    preview_audit: PreviewAuditReport,
    operator_decision_check: Dict[str, Any],
) -> PostPreviewReconciliationReport:
    """Combine all findings into a single reconciliation report."""
    report = PostPreviewReconciliationReport()
    report.timestamp = datetime.now(timezone.utc).isoformat()

    # Preview validity
    report.preview_valid = preview_audit.preview_continuity_passed
    report.preview_reason = (
        "duplicate_static_frames_detected"
        if preview_audit.preview_duplicate_static_frames_detected
        else "preview_continuity_passed"
    )

    # Contact sheet
    report.contact_sheet_useful = preview_audit.contact_sheet_useful
    report.contact_sheet_reason = (
        "static_or_identical_frames" if not preview_audit.contact_sheet_useful
        else "contact_sheet_shows_progression"
    )

    # Path mismatch
    report.preview_path_mismatched = preview_audit.preview_path_mismatch_detected
    report.preview_path_mismatch_detail = (
        f"Expected output/preview, got {preview_audit.actual_preview_path}"
        if preview_audit.preview_path_mismatch_detected
        else "no mismatch"
    )

    # Fake operator decision
    report.fake_operator_decision_detected = operator_decision_check.get(
        "fake_operator_decision_detected", False
    )
    report.fake_operator_decision_invalidated = operator_decision_check.get(
        "invalidation_verified", False
    )

    # Voice rejection
    report.voice_rejected = True
    report.voice_rejection_recorded = False  # Will be recorded by this task
    report.voice_generation_allowed = False
    report.voice_generation_ready = False
    report.assembly_allowed = False
    report.downstream_allowed = False
    report.production_accepted = False

    return report


# ---------------------------------------------------------------------------
# Blocker Report Builder
# ---------------------------------------------------------------------------

def build_blocker_report(
    preview_audit: PreviewAuditReport,
    operator_decision_check: Dict[str, Any],
    reconciliation: PostPreviewReconciliationReport,
) -> BlockerReport:
    """Build the canonical blocker report from all audit findings."""
    report = BlockerReport()
    report.timestamp = datetime.now(timezone.utc).isoformat()

    report.blocker_detected = True
    report.blocker_type = "invalid_static_preview_and_rejected_voice"
    report.preview_valid = preview_audit.preview_continuity_passed
    report.preview_reason = (
        "duplicate_static_frames_detected"
        if preview_audit.preview_duplicate_static_frames_detected
        else "preview_continuity_passed"
    )
    report.contact_sheet_useful = preview_audit.contact_sheet_useful
    report.voice_status = "operator_rejected"
    report.fake_operator_decision_valid = not operator_decision_check.get(
        "fake_operator_decision_detected", True
    )
    report.voice_generation_allowed = reconciliation.voice_generation_allowed
    report.assembly_allowed = reconciliation.assembly_allowed
    report.downstream_allowed = reconciliation.downstream_allowed
    report.production_accepted = reconciliation.production_accepted
    report.fake_success_prevented = True

    # Build blocking details
    details = []
    if not report.preview_valid:
        details.append(
            f"Preview contains {preview_audit.duplicate_frame_count} duplicate/static frames "
            f"({preview_audit.duplicate_static_ratio:.1%} duplication rate)"
        )
    if not report.contact_sheet_useful:
        details.append("Contact sheet does not prove timeline progression (duplicate frames)")
    if preview_audit.preview_path_mismatch_detected:
        details.append(f"Preview path inconsistency detected")
    if not report.fake_operator_decision_valid:
        details.append("Agent-generated operator decision has been invalidated")
    if report.voice_status == "operator_rejected":
        details.append("Voice stage was rejected by operator context; no re-authorization")
    details.append("All voice/assembly/downstream steps are blocked")
    report.blocking_details = details

    return report


# ---------------------------------------------------------------------------
# Full Pipeline Audit
# ---------------------------------------------------------------------------

def run_full_continuity_audit(project_root: str) -> Dict[str, Any]:
    """Execute the complete script supervisor audit pipeline.

    This is the main entry point that runs all checks and produces all reports.
    Safe: never generates, renders, submits, or modifies production artifacts.
    """
    # Step 1: Preview frame audit
    preview_audit = audit_preview_frames(project_root)

    # Step 2: Operator decision authenticity check
    operator_check = check_operator_decision_authenticity(project_root)

    # Step 3: Build voice rejection record
    voice_record = build_voice_rejection_record(project_root)

    # Step 4: Build reconciliation report
    reconciliation = build_post_preview_reconciliation(
        project_root, preview_audit, operator_check
    )
    # Mark voice rejection as recorded since we just created it
    reconciliation.voice_rejection_recorded = True

    # Step 5: Build blocker report
    blocker = build_blocker_report(preview_audit, operator_check, reconciliation)

    return {
        "audit_timestamp": datetime.now(timezone.utc).isoformat(),
        "preview_audit": preview_audit.to_dict(),
        "operator_decision_check": operator_check,
        "voice_rejection_record": voice_record.to_dict(),
        "reconciliation": reconciliation.to_dict(),
        "blocker": blocker.to_dict(),
    }
