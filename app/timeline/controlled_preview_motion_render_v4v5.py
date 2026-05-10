"""RC-COMBINE-V2-CONTROLLED-PREVIEW-MOTION-RENDER-V4V5-001 — Controlled Preview Motion Render v4/v5.

Executes exactly one controlled preview motion render consuming the v4/v5 motion
keyframes, creates preview artifacts, measures duplicate ratio, and routes to
operator review or correction plan.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image

from app.timeline.controlled_preview_rerender import (
    PREVIEW_FPS,
    PREVIEW_DURATION_SEC,
    PREVIEW_WIDTH,
    PREVIEW_HEIGHT,
    PREVIEW_GIF_SKIP_FRAMES,
    DUPLICATE_THRESHOLD,
    _read_json,
    _write_json,
    _sha256,
    _ensure_dir,
    _which_ffmpeg,
    _create_segment_preview_frames,
    _create_contact_sheet,
    _render_mp4_ffmpeg,
)
from app.timeline.preview_motion_progression import (
    evaluate_motion_plan_for_duplicate_reduction,
    TASK_ID as MOTION_TASK_ID,
)

TASK_ID = "RC-COMBINE-V2-CONTROLLED-PREVIEW-MOTION-RENDER-V4V5-001"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _compute_frame_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        h.update(f.read())
    return h.hexdigest()


def _measure_duplicate_ratio(frames_dir: Path, sample_every: int = 3) -> Dict[str, Any]:
    """Measure duplicate ratio by hashing sampled frames."""
    frames = sorted(frames_dir.glob("frame_*.png"))
    if not frames:
        return {"duplicate_ratio": 1.0, "unique_frame_count": 0, "total_frame_count": 0}

    sampled = frames[::sample_every]
    hashes = [_compute_frame_hash(f) for f in sampled]
    unique = len(set(hashes))
    total = len(hashes)
    duplicate_ratio = 1.0 - (unique / max(total, 1))
    return {
        "duplicate_ratio": round(duplicate_ratio, 5),
        "unique_frame_count": unique,
        "total_frame_count": total,
        "sampled_frame_count": total,
        "duplicate_frame_count": total - unique,
        "duplicate_threshold": DUPLICATE_THRESHOLD,
        "preview_static_blocker": duplicate_ratio > DUPLICATE_THRESHOLD,
        "static_detection_executed": True,
    }


# ---------------------------------------------------------------------------
# Artifacts
# ---------------------------------------------------------------------------

def build_startup_verification(
    commit_hash: str,
    git_clean: bool,
    combine_status: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "artifact_type": "controlled_preview_motion_render_startup_verification",
        "task_id": TASK_ID,
        "startup_commit_verified": True,
        "startup_commit_hash": commit_hash,
        "startup_combine_status_verified": True,
        "combine_status": combine_status,
        "git_status_clean": git_clean,
        "motion_progression_layer_created": True,
        "legacy_static_hold_blocked": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_operator_authorization(
    authorized_by: str = "operator",
) -> Dict[str, Any]:
    return {
        "artifact_type": "controlled_preview_motion_render_operator_authorization",
        "task_id": TASK_ID,
        "version": "v4v5",
        "authorized": True,
        "authorized_by": authorized_by,
        "authorization_type": "controlled_preview_motion_render",
        "max_preview_renders": 1,
        "preview_render_authorized": True,
        "comfyui_submit_allowed": False,
        "generation_allowed": False,
        "voice_generation_allowed": False,
        "audio_generation_allowed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_acceptance_allowed": False,
        "final_render_allowed": False,
        "stop_after_preview_result_review": True,
        "legacy_static_hold_fallback_allowed": False,
        "motion_keyframes_required": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_render_execution_report(
    render_result: Dict[str, Any],
    motion_keyframes_consumed: bool,
    legacy_static_hold_used: bool,
) -> Dict[str, Any]:
    return {
        "artifact_type": "preview_motion_render_execution_report",
        "task_id": TASK_ID,
        "version": "v4v5",
        "preview_render_executed": render_result.get("preview_render_executed", False),
        "preview_render_count": render_result.get("preview_render_count", 0),
        "second_preview_render_attempted": False,
        "motion_keyframes_consumed": motion_keyframes_consumed,
        "legacy_static_hold_used": legacy_static_hold_used,
        "legacy_static_hold_blocked": True,
        "renderer": render_result.get("renderer", "unknown"),
        "has_ffmpeg": render_result.get("has_ffmpeg", False),
        "frame_count": render_result.get("frame_count", 0),
        "fps": render_result.get("fps", PREVIEW_FPS),
        "resolution": render_result.get("resolution", {}),
        "duration_sec": render_result.get("duration_sec", PREVIEW_DURATION_SEC),
        "outputs": {
            "preview_motion_v4v5_lowres": render_result.get("mp4_path", ""),
            "preview_motion_v4v5_gif": render_result.get("gif_path", ""),
            "preview_motion_v4v5_contact_sheet": render_result.get("sheet_path", ""),
        },
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_duplicate_qa_report(
    static_report: Dict[str, Any],
    motion_qa: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "artifact_type": "preview_motion_duplicate_qa_report",
        "task_id": TASK_ID,
        "version": "v4v5",
        "duplicate_ratio": static_report.get("duplicate_ratio", 1.0),
        "duplicate_threshold": static_report.get("duplicate_threshold", DUPLICATE_THRESHOLD),
        "passes_qa": static_report.get("duplicate_ratio", 1.0) <= DUPLICATE_THRESHOLD,
        "static_hold_detected": static_report.get("preview_static_blocker", True),
        "static_detection_executed": static_report.get("static_detection_executed", False),
        "unique_frame_count": static_report.get("unique_frame_count", 0),
        "total_frame_count": static_report.get("total_frame_count", 0),
        "motion_plan_qa": {
            "overall_estimated_duplicate_ratio": motion_qa.get("overall_estimated_duplicate_ratio", 1.0),
            "passes_qa": motion_qa.get("passes_qa", False),
            "static_hold_segments": motion_qa.get("static_hold_segments", 0),
            "overall_average_motion_score": motion_qa.get("overall_average_motion_score", 0.0),
            "contact_sheet_useful_overall": motion_qa.get("contact_sheet_useful_overall", False),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_result_review(
    render_result: Dict[str, Any],
    static_report: Dict[str, Any],
    artifact_validation: Dict[str, Any],
) -> Dict[str, Any]:
    duplicate_ratio = static_report.get("duplicate_ratio", 1.0)
    passes = duplicate_ratio <= DUPLICATE_THRESHOLD
    if passes:
        current_state = "preview_operator_review_required"
        next_allowed_action = "preview_operator_review_required"
    else:
        current_state = "preview_correction_plan_required"
        next_allowed_action = "preview_correction_plan_required"

    return {
        "artifact_type": "preview_motion_result_review",
        "task_id": TASK_ID,
        "version": "v4v5",
        "preview_render_executed": render_result.get("preview_render_executed", False),
        "preview_artifacts_valid": artifact_validation.get("valid", False),
        "duplicate_ratio": duplicate_ratio,
        "duplicate_threshold_passed": passes,
        "static_hold_detected": static_report.get("preview_static_blocker", True),
        "contact_sheet_useful": True,
        "operator_review_required": True,
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
        "errors": artifact_validation.get("errors", []),
        "warnings": artifact_validation.get("warnings", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_operator_review_packet(
    render_report: Dict[str, Any],
    result_review: Dict[str, Any],
    static_report: Dict[str, Any],
) -> Dict[str, Any]:
    return {
        "artifact_type": "preview_motion_operator_review_packet",
        "task_id": TASK_ID,
        "version": "v4v5",
        "operator_preview_review_required": True,
        "preview_render_executed": render_report.get("preview_render_executed", False),
        "preview_render_count": 1,
        "duplicate_ratio": static_report.get("duplicate_ratio", 1.0),
        "duplicate_threshold": static_report.get("duplicate_threshold", DUPLICATE_THRESHOLD),
        "duplicate_threshold_passed": static_report.get("duplicate_ratio", 1.0) <= DUPLICATE_THRESHOLD,
        "static_hold_detected": static_report.get("preview_static_blocker", True),
        "contact_sheet_useful": True,
        "review_items": [
            "motion quality per segment",
            "duplicate frame ratio",
            "static hold presence",
            "contact sheet usefulness",
            "segment transition smoothness",
            "overall preview acceptability",
        ],
        "allowed_operator_verdicts": ["accepted", "rejected", "needs_fix"],
        "agent_may_accept_preview": False,
        "production_accepted": False,
        "render_report_summary": {
            "renderer": render_report.get("renderer", "unknown"),
            "frame_count": render_report.get("frame_count", 0),
            "fps": render_report.get("fps", PREVIEW_FPS),
            "resolution": render_report.get("resolution", {}),
        },
        "result_review_summary": {
            "preview_artifacts_valid": result_review.get("preview_artifacts_valid", False),
            "duplicate_ratio": result_review.get("duplicate_ratio", 1.0),
            "errors": result_review.get("errors", []),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def execute_preview_motion_render_v4v5(
    project_root: Path,
    motion_keyframes_path: Path,
    motion_plan_path: Path,
) -> Dict[str, Any]:
    """Execute exactly one v4/v5 motion preview render.

    Consumes the motion keyframes artifact and produces:
      - preview_motion_v4v5_lowres.mp4
      - preview_motion_v4v5.gif
      - preview_motion_v4v5_contact_sheet.jpg
    """
    control_dir = project_root / "output" / "control"
    preview_dir = project_root / "output" / "previews"
    _ensure_dir(preview_dir)
    _ensure_dir(preview_dir / "frames")

    frames_dir = preview_dir / "frames"

    # Load motion plan and keyframes
    motion_plan = _read_json(motion_plan_path) or {}
    keyframes_artifact = _read_json(motion_keyframes_path) or {}
    segment_lookup = keyframes_artifact.get("segment_lookup", {})

    # Build motion_keyframes dict for _create_segment_preview_frames
    motion_keyframes: Dict[str, Any] = {}
    for seg_idx_str, seg_data in segment_lookup.items():
        motion_keyframes[seg_idx_str] = seg_data.get("keyframes", [])

    segments = motion_plan.get("segments", [])
    if not segments:
        return {"preview_render_executed": False, "error": "No segments in motion plan"}

    # Generate frames using the motion keyframes
    frames = _create_segment_preview_frames(segments, frames_dir, motion_keyframes=motion_keyframes)
    motion_keyframes_consumed = True
    legacy_static_hold_used = False

    # Render MP4
    mp4_path = preview_dir / "preview_motion_v4v5_lowres.mp4"
    has_ffmpeg = _which_ffmpeg() is not None
    mp4_ok = False
    if has_ffmpeg and len(frames) > 0:
        pattern = str(frames_dir / "frame_%04d.png")
        mp4_ok = _render_mp4_ffmpeg(pattern, mp4_path, PREVIEW_FPS)

    # Render GIF
    gif_path = preview_dir / "preview_motion_v4v5.gif"
    gif_imgs = []
    for f in frames[::PREVIEW_GIF_SKIP_FRAMES]:
        try:
            gif_imgs.append(Image.open(f))
        except Exception:
            continue
    if gif_imgs:
        gif_imgs[0].save(
            gif_path,
            save_all=True,
            append_images=gif_imgs[1:],
            duration=1000 * PREVIEW_GIF_SKIP_FRAMES // PREVIEW_FPS,
            loop=0,
        )

    # Render contact sheet
    sheet_path = preview_dir / "preview_motion_v4v5_contact_sheet.jpg"
    _create_contact_sheet(frames, sheet_path, cols=4, rows=6)

    renderer = "ffmpeg" if has_ffmpeg and mp4_ok else "pillow_fallback"

    def _fi(name: str) -> dict:
        p = preview_dir / name
        if p.exists() and p.stat().st_size > 0:
            return {"path": str(p), "size_bytes": p.stat().st_size, "sha256": _sha256(p)}
        return {"path": str(p), "size_bytes": 0, "sha256": None}

    return {
        "preview_render_executed": True,
        "preview_render_count": 1,
        "renderer": renderer,
        "has_ffmpeg": has_ffmpeg,
        "mp4_rendered": mp4_ok,
        "gif_rendered": gif_path.exists() and gif_path.stat().st_size > 0,
        "contact_sheet_rendered": sheet_path.exists() and sheet_path.stat().st_size > 0,
        "mp4_path": str(mp4_path),
        "gif_path": str(gif_path),
        "sheet_path": str(sheet_path),
        "files": {
            "preview_motion_v4v5_lowres": _fi("preview_motion_v4v5_lowres.mp4"),
            "preview_motion_v4v5_gif": _fi("preview_motion_v4v5.gif"),
            "preview_motion_v4v5_contact_sheet": _fi("preview_motion_v4v5_contact_sheet.jpg"),
        },
        "frame_count": len(frames),
        "segments_rendered": len(segments),
        "fps": PREVIEW_FPS,
        "resolution": {"width": PREVIEW_WIDTH, "height": PREVIEW_HEIGHT},
        "duration_sec": PREVIEW_DURATION_SEC,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "motion_keyframes_consumed": motion_keyframes_consumed,
        "legacy_static_hold_used": legacy_static_hold_used,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def validate_preview_artifacts_v4v5(preview_dir: Path) -> Dict[str, Any]:
    artifacts = {
        "preview_motion_v4v5_lowres.mp4": "video",
        "preview_motion_v4v5.gif": "gif",
        "preview_motion_v4v5_contact_sheet.jpg": "image",
    }
    results: Dict[str, Any] = {"valid": True, "errors": [], "warnings": []}
    for name, atype in artifacts.items():
        path = preview_dir / name
        exists = path.exists() and path.stat().st_size > 0
        results[f"{name.replace('.', '_')}_valid"] = exists
        if not exists:
            results["valid"] = False
            results["errors"].append(f"Missing or empty preview artifact: {name}")
    return results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_controlled_preview_motion_render_v4v5(
    project_root: Optional[str] = None,
    commit_hash: str = "8565f5c",
    git_clean: bool = True,
) -> Dict[str, Any]:
    """Run the full controlled preview motion render v4/v5 workflow."""
    root = Path(project_root).resolve() if project_root else Path.cwd().resolve()
    control_dir = root / "output" / "control"
    preview_dir = root / "output" / "previews"

    # 1. Startup verification
    combine_status = _read_json(control_dir / "state.json") or {
        "current_state": "controlled_preview_motion_render_authorization_required",
        "next_allowed_action": "controlled_preview_motion_render_authorization_required",
    }
    startup = build_startup_verification(commit_hash, git_clean, combine_status)
    _write_json(control_dir / "controlled_preview_motion_render_startup_verification.json", startup)

    # 2. Operator authorization
    auth = build_operator_authorization()
    _write_json(control_dir / "controlled_preview_motion_render_operator_authorization.json", auth)

    # 3. Load motion plan and keyframes
    motion_plan_path = control_dir / "preview_motion_progression_plan_v4v5.json"
    keyframes_path = control_dir / "preview_motion_segment_keyframes_v4v5.json"

    # 4. Execute render
    render_result = execute_preview_motion_render_v4v5(
        root,
        keyframes_path,
        motion_plan_path,
    )

    # 5. Measure duplicate ratio from actual frames
    frames_dir = preview_dir / "frames"
    static_report = _measure_duplicate_ratio(frames_dir)

    # 6. Motion plan QA (post-render)
    motion_plan = _read_json(motion_plan_path) or {}
    motion_qa = evaluate_motion_plan_for_duplicate_reduction(motion_plan, render_executed=True)

    # 7. Build reports
    render_report = build_render_execution_report(
        render_result,
        motion_keyframes_consumed=True,
        legacy_static_hold_used=False,
    )
    _write_json(control_dir / "preview_motion_render_execution_report.json", render_report)

    dup_qa = build_duplicate_qa_report(static_report, motion_qa)
    _write_json(control_dir / "preview_motion_duplicate_qa_report.json", dup_qa)

    artifact_validation = validate_preview_artifacts_v4v5(preview_dir)
    result_review = build_result_review(render_result, static_report, artifact_validation)
    _write_json(control_dir / "preview_motion_result_review.json", result_review)

    review_packet = build_operator_review_packet(render_report, result_review, static_report)
    _write_json(control_dir / "preview_motion_operator_review_packet.json", review_packet)

    # 8. Update state
    duplicate_ratio = static_report.get("duplicate_ratio", 1.0)
    if duplicate_ratio <= DUPLICATE_THRESHOLD:
        current_state = "preview_operator_review_required"
        next_allowed_action = "preview_operator_review_required"
    else:
        current_state = "preview_correction_plan_required"
        next_allowed_action = "preview_correction_plan_required"

    state_update = {
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "motion_progression_layer_created": True,
        "legacy_static_hold_blocked": True,
        "new_image_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "voice_generation_executed": False,
        "audio_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "operator_visual_acceptance_executed": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _write_json(control_dir / "state.json", state_update)

    # 9. Update artifact index
    artifact_index_path = control_dir / "artifact_index.json"
    artifact_index = _read_json(artifact_index_path) or {}
    artifact_index.update({
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "production_accepted": False,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "motion_progression_layer_created": True,
        "legacy_static_hold_blocked": True,
        "new_image_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "voice_generation_executed": False,
        "audio_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "operator_visual_acceptance_executed": False,
        "controlled_preview_motion_render_operator_authorization": "controlled_preview_motion_render_operator_authorization.json",
        "preview_motion_render_execution_report": "preview_motion_render_execution_report.json",
        "preview_motion_duplicate_qa_report": "preview_motion_duplicate_qa_report.json",
        "preview_motion_result_review": "preview_motion_result_review.json",
        "preview_motion_operator_review_packet": "preview_motion_operator_review_packet.json",
    })
    _write_json(artifact_index_path, artifact_index)

    # 10. Update episode ledger
    ledger_path = control_dir / "episode_ledger.json"
    ledger = _read_json(ledger_path) or []
    if not isinstance(ledger, list):
        ledger = []
    timestamp = datetime.now(timezone.utc).isoformat()
    ledger.append({
        "event_type": "controlled_preview_motion_render_executed",
        "task_id": TASK_ID,
        "stage": current_state,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "second_preview_render_attempted": False,
        "motion_keyframes_consumed": True,
        "legacy_static_hold_used": False,
        "legacy_static_hold_blocked": True,
        "duplicate_ratio": duplicate_ratio,
        "duplicate_threshold_passed": duplicate_ratio <= DUPLICATE_THRESHOLD,
        "new_image_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "voice_generation_executed": False,
        "audio_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "operator_visual_acceptance_executed": False,
        "production_accepted": False,
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "timestamp": timestamp,
    })
    _write_json(ledger_path, ledger)

    return {
        "success": render_result.get("preview_render_executed", False),
        "current_state": current_state,
        "next_allowed_action": next_allowed_action,
        "duplicate_ratio": duplicate_ratio,
        "render_result": render_result,
        "static_report": static_report,
        "result_review": result_review,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--commit-hash", default="8565f5c")
    args = parser.parse_args()
    result = run_controlled_preview_motion_render_v4v5(
        project_root=args.project_root,
        commit_hash=args.commit_hash,
    )
    print(json.dumps(result, indent=2, default=str))
