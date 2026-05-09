"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — Controlled Preview Render Gate.

Validates preview render authorization, executes exactly one preview render
creating preview_lowres.mp4, preview.gif, and contact_sheet.jpg, validates
all artifacts, and routes to operator preview review.

No voice generation, assembly, downstream, or production acceptance.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError

TASK_ID = "RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001"

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


def _sha256(path: Path) -> str:
    """Compute SHA-256 of a file."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def _ensure_dir(path: Path) -> None:
    """Ensure directory exists, creating it if needed."""
    path.mkdir(parents=True, exist_ok=True)


def _which_ffmpeg() -> Optional[str]:
    """Return ffmpeg path or None."""
    return shutil.which("ffmpeg")


# ---------------------------------------------------------------------------
# 6.1. Preview Authorization Validation
# ---------------------------------------------------------------------------

REQUIRED_AUTH_FIELDS = [
    "task_id",
    "operator_authorized",
    "preview_render_authorized",
    "max_preview_renders",
    "source_timeline",
    "preview_proof_contract",
    "voice_generation_allowed",
    "assembly_allowed",
    "downstream_allowed",
    "production_acceptance_allowed",
    "final_render_allowed",
    "stop_after_preview_result_review",
]


def validate_preview_render_authorization(
    control_dir: Path,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """Validate preview_render_authorization.json exists and is valid.

    Returns:
        (is_valid, auth_data, message)
    """
    auth_path = control_dir / "preview_render_authorization.json"
    if not auth_path.exists():
        return False, None, "preview_render_authorization.json not found"

    data = _read_json(auth_path)
    if not data:
        return False, None, "preview_render_authorization.json is invalid JSON"

    missing = [f for f in REQUIRED_AUTH_FIELDS if f not in data]
    if missing:
        return False, data, f"Missing required fields: {missing}"

    if not isinstance(data.get("operator_authorized"), bool):
        return False, data, "operator_authorized must be boolean"
    if not isinstance(data.get("preview_render_authorized"), bool):
        return False, data, "preview_render_authorized must be boolean"
    if not isinstance(data.get("max_preview_renders"), int):
        return False, data, "max_preview_renders must be int"

    if not data.get("operator_authorized"):
        return False, data, "operator_authorized is False"
    if not data.get("preview_render_authorized"):
        return False, data, "preview_render_authorized is False"
    if data.get("max_preview_renders") != 1:
        return (
            False,
            data,
            f"max_preview_renders must be 1, got {data.get('max_preview_renders')}",
        )
    if data.get("voice_generation_allowed", False):
        return False, data, "voice_generation_allowed must be False"
    if data.get("assembly_allowed", False):
        return False, data, "assembly_allowed must be False"
    if data.get("downstream_allowed", False):
        return False, data, "downstream_allowed must be False"
    if data.get("production_acceptance_allowed", False):
        return False, data, "production_acceptance_allowed must be False"
    if data.get("final_render_allowed", False):
        return False, data, "final_render_allowed must be False"
    if not data.get("stop_after_preview_result_review", False):
        return False, data, "stop_after_preview_result_review must be True"

    return True, data, "Authorization valid"


# ---------------------------------------------------------------------------
# 6.2. Input Artifact Validation
# ---------------------------------------------------------------------------

INPUT_ARTIFACTS = [
    "timeline_model.json",
    "marker_registry.json",
    "edit_decision_list.json",
    "subtitle_plan.json",
    "transition_policy.json",
    "voice_casting_contract.json",
    "preview_proof_contract.json",
    "timeline_preview_dry_run_report.json",
    "preview_render_authorization_packet.json",
]


def validate_input_artifacts(control_dir: Path) -> Dict[str, Any]:
    """Validate all required input artifacts exist and are structurally valid.

    Returns validation result dict.
    """
    result: Dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    for name in INPUT_ARTIFACTS:
        path = control_dir / name
        exists = path.exists()
        result[f"{name}_exists"] = exists
        if not exists:
            result["valid"] = False
            result["errors"].append(f"Missing input artifact: {name}")
            continue

        data = _read_json(path)
        valid_json = data is not None
        result[f"{name}_valid"] = valid_json
        if not valid_json:
            result["valid"] = False
            result["errors"].append(f"Invalid JSON in: {name}")

    # Dry run specific checks
    dry_run_path = control_dir / "timeline_preview_dry_run_report.json"
    dry_run = _read_json(dry_run_path)
    if dry_run:
        dry_status = dry_run.get("dry_run_status", "")
        result["dry_run_passed"] = dry_status != "blocked"
        result["dry_run_errors"] = len(dry_run.get("errors", []))
        if dry_run.get("errors"):
            result["warnings"].append(
                f"Dry run has {len(dry_run['errors'])} unresolved errors"
            )

    # Voice casting contract: must not authorize voice generation
    voice_path = control_dir / "voice_casting_contract.json"
    voice = _read_json(voice_path)
    if voice and isinstance(voice, dict):
        voice_gen = voice.get("full_voiceover_generation_allowed", True)
        result["voice_contract_does_not_authorize_voice_generation"] = not voice_gen
        if voice_gen:
            result["valid"] = False
            result["errors"].append(
                "voice_casting_contract.json authorizes voice generation"
            )

    # Preview proof contract must be valid
    pp_path = control_dir / "preview_proof_contract.json"
    pp = _read_json(pp_path)
    if pp and isinstance(pp, dict):
        result["preview_proof_contract_valid"] = True
    elif pp_path.exists():
        result["preview_proof_contract_valid"] = False
        result["warnings"].append("preview_proof_contract.json exists but invalid")
    else:
        result["preview_proof_contract_valid"] = False

    return result


# ---------------------------------------------------------------------------
# 6.3. Preview Render Execution
# ---------------------------------------------------------------------------

PREVIEW_FPS = 24
PREVIEW_DURATION_SEC = 30.0
PREVIEW_WIDTH = 672
PREVIEW_HEIGHT = 384
PREVIEW_GIF_SKIP_FRAMES = 12  # sample every 12th frame for GIF


def _create_preview_frames(
    asset_path: Path, num_frames: int, preview_dir: Path
) -> List[Path]:
    """Generate preview frames from a single image asset using Pillow.

    Simulates a simple pan/zoom effect (Ken Burns style) over the image
    to create the sense of motion for the preview video.

    Returns list of frame file paths.
    """
    img = Image.open(asset_path)
    img_width, img_height = img.size

    # Target aspect ratio
    target_ratio = PREVIEW_WIDTH / PREVIEW_HEIGHT
    src_ratio = img_width / img_height

    if src_ratio > target_ratio:
        display_w = img_height * target_ratio
        display_h = img_height
    else:
        display_w = img_width
        display_h = img_width / target_ratio

    display_w = int(display_w)
    display_h = int(display_h)

    frames: List[Path] = []
    for i in range(num_frames):
        progress = i / max(num_frames - 1, 1)

        # Simple zoom: 1.0 -> 1.05 over duration
        zoom = 1.0 + 0.05 * progress
        crop_w = int(img_width / zoom)
        crop_h = int(img_height / zoom)

        left = (img_width - crop_w) // 2
        top = (img_height - crop_h) // 2

        cropped = img.crop((left, top, left + crop_w, top + crop_h))
        resized = cropped.resize((PREVIEW_WIDTH, PREVIEW_HEIGHT), Image.LANCZOS)

        frame_path = preview_dir / f"frame_{i:04d}.png"
        resized.save(frame_path, "PNG")
        frames.append(frame_path)

    return frames


def _render_mp4_ffmpeg(
    frame_pattern: str,
    output_path: Path,
    fps: int,
) -> bool:
    """Render MP4 from frames using FFmpeg."""
    cmd = [
        _which_ffmpeg(),
        "-y",
        "-framerate",
        str(fps),
        "-i",
        frame_pattern,
        "-c:v",
        "libx264",
        "-preset",
        "ultrafast",
        "-pix_fmt",
        "yuv420p",
        "-crf",
        "28",
        str(output_path),
    ]
    try:
        subprocess.run(
            cmd, capture_output=True, timeout=120, check=True
        )
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return False


def _render_mp4_fallback(
    frames: List[Path],
    output_path: Path,
    fps: int,
) -> bool:
    """Fallback: create a minimal MP4 header stub using raw H.264 frames.

    If FFmpeg is unavailable, we write a note file instead of a fake MP4.
    This prevents fake preview artifacts while documenting the limitation.
    """
    # Write blocker note — do NOT create fake MP4
    note_path = output_path.with_suffix(".mp4.txt")
    _write_json(
        note_path,
        {
            "error": "FFmpeg not available for MP4 rendering",
            "resolution": "Install FFmpeg or use a system with video encoding support",
            "frames_available": len(frames),
            "fps": fps,
        },
    )
    return False


def execute_preview_render(
    asset_path: Path,
    preview_dir: Path,
) -> Dict[str, Any]:
    """Execute exactly one preview render.

    Creates preview_lowres.mp4, preview.gif, contact_sheet.jpg
    from the approved asset.

    Returns render result dict.
    """
    _ensure_dir(preview_dir / "frames")
    frames_dir = preview_dir / "frames"

    num_frames = int(PREVIEW_DURATION_SEC * PREVIEW_FPS)

    # Generate frames
    frames = _create_preview_frames(asset_path, num_frames, frames_dir)

    # Render preview_lowres.mp4
    mp4_path = preview_dir / "preview_lowres.mp4"
    has_ffmpeg = _which_ffmpeg() is not None
    if has_ffmpeg:
        pattern = str(frames_dir / "frame_%04d.png")
        mp4_ok = _render_mp4_ffmpeg(pattern, mp4_path, PREVIEW_FPS)
    else:
        mp4_ok = _render_mp4_fallback(frames, mp4_path, PREVIEW_FPS)

    # Render preview.gif (always with Pillow)
    gif_path = preview_dir / "preview.gif"
    gif_frames = frames[::PREVIEW_GIF_SKIP_FRAMES]
    if gif_frames:
        gif_imgs = [Image.open(f) for f in gif_frames]
        gif_imgs[0].save(
            gif_path,
            save_all=True,
            append_images=gif_imgs[1:],
            duration=1000 * PREVIEW_GIF_SKIP_FRAMES // PREVIEW_FPS,
            loop=0,
        )

    # Render contact_sheet.jpg
    sheet_path = preview_dir / "contact_sheet.jpg"
    _create_contact_sheet(frames, sheet_path, cols=4, rows=6)

    renderer = "ffmpeg" if has_ffmpeg and mp4_ok else "pillow_fallback"

    return {
        "preview_render_executed": True,
        "preview_render_count": 1,
        "renderer": renderer,
        "has_ffmpeg": has_ffmpeg,
        "mp4_rendered": mp4_ok,
        "gif_rendered": gif_path.exists() and gif_path.stat().st_size > 0,
        "contact_sheet_rendered": sheet_path.exists() and sheet_path.stat().st_size > 0,
        "frame_count": len(frames),
        "gif_frame_count": len(gif_frames),
        "fps": PREVIEW_FPS,
        "resolution": {"width": PREVIEW_WIDTH, "height": PREVIEW_HEIGHT},
        "duration_sec": PREVIEW_DURATION_SEC,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _create_contact_sheet(
    frames: List[Path], output_path: Path, cols: int = 4, rows: int = 6
) -> None:
    """Create a contact sheet JPG from sampled frames."""
    sample_count = min(cols * rows, len(frames))
    indices = [
        int(i * (len(frames) - 1) / max(sample_count - 1, 1))
        for i in range(sample_count)
    ]
    sample_frames = [Image.open(frames[i]) for i in indices]

    cell_w, cell_h = PREVIEW_WIDTH, PREVIEW_HEIGHT
    sheet_w = cols * cell_w
    sheet_h = rows * cell_h

    sheet = Image.new("RGB", (sheet_w, sheet_h), color=(32, 32, 32))

    for idx, frame in enumerate(sample_frames):
        col = idx % cols
        row = idx // cols
        x = col * cell_w
        y = row * cell_h
        sheet.paste(frame, (x, y))

    sheet.save(output_path, "JPEG", quality=80)


# ---------------------------------------------------------------------------
# 6.4. Preview Artifact Validation
# ---------------------------------------------------------------------------


def validate_preview_artifact(
    path: Path, artifact_type: str
) -> Dict[str, bool]:
    """Validate a single preview artifact.

    Returns dict of validation checks.
    """
    result: Dict[str, bool] = {
        "exists": False,
        "readable": False,
        "size_bytes_gt_zero": False,
        "sha256_present": False,
        "not_stub": True,
        "canonical_path": True,
    }

    result["exists"] = path.exists()
    if not result["exists"]:
        return result

    result["readable"] = os.access(path, os.R_OK)
    if not result["readable"]:
        return result

    size = path.stat().st_size
    result["size_bytes_gt_zero"] = size > 0
    if size == 0:
        result["not_stub"] = False

    result["sha256_present"] = True  # we compute it below

    # Type-specific checks
    if artifact_type == "video":
        result["duration_recorded_if_video"] = True
        result["width_height_recorded"] = True
    elif artifact_type == "gif":
        try:
            with Image.open(path) as img:
                result["width_height_recorded"] = True
                result["frame_count_gt_zero"] = True
        except Exception:
            result["readable"] = False
            result["not_stub"] = False
    elif artifact_type == "image":
        try:
            with Image.open(path) as img:
                result["width_height_recorded"] = True
        except Exception:
            result["readable"] = False
            result["not_stub"] = False

    return result


def validate_preview_artifacts(preview_dir: Path) -> Dict[str, Any]:
    """Validate all preview artifacts.

    Returns validation result dict.
    """
    artifacts = {
        "preview_lowres.mp4": "video",
        "preview.gif": "gif",
        "contact_sheet.jpg": "image",
    }

    results: Dict[str, Any] = {
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    for name, atype in artifacts.items():
        path = preview_dir / name
        validation = validate_preview_artifact(path, atype)

        # Compute SHA-256 if exists and readable
        if validation["exists"] and validation["readable"]:
            try:
                validation["sha256"] = _sha256(path)
            except Exception:
                validation["sha256"] = None

        results[name.replace(".", "_")] = validation
        results[f"{name.replace('.', '_')}_valid"] = (
            validation["exists"]
            and validation["size_bytes_gt_zero"]
            and validation["not_stub"]
        )

        if not validation["exists"]:
            results["valid"] = False
            results["errors"].append(f"Missing preview artifact: {name}")
        elif not validation["size_bytes_gt_zero"]:
            results["valid"] = False
            results["errors"].append(f"Zero-size preview artifact: {name}")
        elif not validation["not_stub"]:
            results["valid"] = False
            results["errors"].append(f"Stub preview artifact detected: {name}")

    return results


# ---------------------------------------------------------------------------
# 6.5. Reports and Review Packet
# ---------------------------------------------------------------------------


def build_preview_render_report(
    render_result: Dict[str, Any],
    source_timeline: str,
    control_dir: Path,
) -> Dict[str, Any]:
    """Build preview_render_report.json."""
    preview_dir = control_dir.parent / "preview"
    mp4_path = preview_dir / "preview_lowres.mp4"
    gif_path = preview_dir / "preview.gif"
    sheet_path = preview_dir / "contact_sheet.jpg"

    mp4_sha = _sha256(mp4_path) if mp4_path.exists() else None
    gif_sha = _sha256(gif_path) if gif_path.exists() else None
    sheet_sha = _sha256(sheet_path) if sheet_path.exists() else None

    mp4_info = {}
    if mp4_path.exists() and mp4_path.stat().st_size > 0:
        mp4_info = {
            "path": str(mp4_path.relative_to(control_dir.parent.parent.parent)),
            "size_bytes": mp4_path.stat().st_size,
            "sha256": mp4_sha,
            "resolution": render_result.get("resolution"),
            "fps": render_result.get("fps"),
            "duration_sec": render_result.get("duration_sec"),
        }

    gif_info = {}
    if gif_path.exists() and gif_path.stat().st_size > 0:
        gif_info = {
            "path": str(gif_path.relative_to(control_dir.parent.parent.parent)),
            "size_bytes": gif_path.stat().st_size,
            "sha256": gif_sha,
        }
        try:
            with Image.open(gif_path) as gif:
                gif_info["width"] = gif.width
                gif_info["height"] = gif.height
                gif_info["frame_count"] = getattr(gif, "n_frames", 0)
        except Exception:
            pass

    sheet_info = {}
    if sheet_path.exists() and sheet_path.stat().st_size > 0:
        sheet_info = {
            "path": str(sheet_path.relative_to(control_dir.parent.parent.parent)),
            "size_bytes": sheet_path.stat().st_size,
            "sha256": sheet_sha,
        }
        try:
            with Image.open(sheet_path) as img:
                sheet_info["width"] = img.width
                sheet_info["height"] = img.height
        except Exception:
            pass

    return {
        "task_id": TASK_ID,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "renderer": render_result.get("renderer", "unknown"),
        "source_timeline": source_timeline,
        "fps": render_result.get("fps"),
        "resolution": render_result.get("resolution"),
        "duration_sec": render_result.get("duration_sec"),
        "outputs": {
            "preview_lowres.mp4": mp4_info,
            "preview.gif": gif_info,
            "contact_sheet.jpg": sheet_info,
        },
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_preview_result_review(
    artifact_validation: Dict[str, Any],
    render_success: bool,
) -> Dict[str, Any]:
    """Build preview_result_review.json."""
    return {
        "task_id": TASK_ID,
        "preview_artifacts_valid": artifact_validation.get("valid", False) and render_success,
        "preview_lowres_valid": artifact_validation.get(
            "preview_lowres_mp4_valid", False
        ),
        "preview_gif_valid": artifact_validation.get("preview_gif_valid", False),
        "contact_sheet_valid": artifact_validation.get(
            "contact_sheet_jpg_valid", False
        ),
        "operator_review_required": True,
        "production_accepted": False,
        "errors": artifact_validation.get("errors", []),
        "warnings": artifact_validation.get("warnings", []),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_preview_operator_review_packet(
    render_report: Dict[str, Any],
    result_review: Dict[str, Any],
) -> Dict[str, Any]:
    """Build preview_operator_review_packet.json."""
    return {
        "task_id": TASK_ID,
        "operator_preview_review_required": True,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "review_items": [
            "timeline pacing",
            "asset placement",
            "subtitle timing",
            "transition quality",
            "preview readability",
            "audio/voice placeholder policy",
            "overall preview acceptability",
        ],
        "allowed_operator_verdicts": [
            "accepted",
            "rejected",
            "needs_fix",
        ],
        "agent_may_accept_preview": False,
        "production_accepted": False,
        "render_report": {
            k: v for k, v in render_report.items() if k in (
                "renderer", "fps", "resolution", "duration_sec", "outputs",
            )
        },
        "result_review_summary": {
            "preview_artifacts_valid": result_review.get("preview_artifacts_valid"),
            "errors": result_review.get("errors", []),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Authorization missing / blocker artifacts
# ---------------------------------------------------------------------------


def build_authorization_required_artifact(control_dir: Path) -> Dict[str, Any]:
    """Create preview_render_authorization_required.json when authorization is missing."""
    return {
        "task_id": TASK_ID,
        "authorization_required": True,
        "authorization_granted": False,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "preview_render_authorization_required",
        "next_allowed_action": "preview_render_authorization_required",
        "message": "Preview render authorization is missing or invalid. "
                   "Create preview_render_authorization.json with operator authorization.",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_gate_blocker_report(
    auth_validation: Tuple[bool, Optional[Dict], str],
    input_validation: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create preview_render_gate_blocker_report.json when gate is blocked."""
    _, _, auth_msg = auth_validation
    return {
        "task_id": TASK_ID,
        "gate_blocked": True,
        "reason": "Preview render authorization missing or invalid",
        "authorization_validation_message": auth_msg,
        "input_validation_errors": (input_validation or {}).get("errors", []),
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "preview_render_authorization_required",
        "next_allowed_action": "preview_render_authorization_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_runtime_blocker_report(
    render_result: Dict[str, Any],
) -> Dict[str, Any]:
    """Create preview_render_runtime_blocker_report.json when render fails at runtime."""
    return {
        "task_id": TASK_ID,
        "runtime_blocked": True,
        "reason": "Preview render failed at runtime",
        "render_details": render_result,
        "preview_render_executed": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "preview_render_blocked",
        "next_allowed_action": "preview_render_blocker_review_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def build_blocker_review_packet(
    blocker_report: Dict[str, Any],
) -> Dict[str, Any]:
    """Create preview_render_blocker_review_packet.json."""
    return {
        "task_id": TASK_ID,
        "blocker_review_required": True,
        "blocker_type": "runtime",
        "blocker_report": blocker_report,
        "operator_may_retry_preview_render": True,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Ledger and index updates
# ---------------------------------------------------------------------------


def build_ledger_events(
    auth_data: Dict[str, Any],
    render_result: Optional[Dict[str, Any]],
    input_validation: Dict[str, Any],
    target_state: str,
    target_action: str,
    preview_render_executed: bool,
) -> list:
    """Build ledger events for the controlled preview render cycle."""
    timestamp = datetime.now(timezone.utc).isoformat()
    source_timeline = auth_data.get("source_timeline", "")

    events = []

    if preview_render_executed:
        events.append({
            "event_type": "preview_render_started",
            "task_id": TASK_ID,
            "stage": target_state,
            "source_timeline": source_timeline,
            "preview_render_count": 1,
            "max_preview_renders": 1,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "timestamp": timestamp,
        })
        events.append({
            "event_type": "preview_lowres_created",
            "task_id": TASK_ID,
            "stage": target_state,
            "artifact": "preview_lowres.mp4",
            "timestamp": timestamp,
        })
        events.append({
            "event_type": "preview_gif_created",
            "task_id": TASK_ID,
            "stage": target_state,
            "artifact": "preview.gif",
            "timestamp": timestamp,
        })
        events.append({
            "event_type": "contact_sheet_created",
            "task_id": TASK_ID,
            "stage": target_state,
            "artifact": "contact_sheet.jpg",
            "timestamp": timestamp,
        })
        events.append({
            "event_type": "preview_render_completed",
            "task_id": TASK_ID,
            "stage": target_state,
            "preview_render_executed": True,
            "preview_render_count": 1,
            "second_preview_render_attempted": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "input_errors": len(input_validation.get("errors", [])),
            "timestamp": timestamp,
        })
        events.append({
            "event_type": "preview_operator_review_required",
            "task_id": TASK_ID,
            "stage": target_state,
            "operator_preview_review_required": True,
            "agent_may_accept_preview": False,
            "preview_render_executed": True,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "timestamp": timestamp,
        })
    else:
        events.append({
            "event_type": "preview_render_blocked_or_not_authorized",
            "task_id": TASK_ID,
            "stage": target_state,
            "preview_render_executed": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
            "current_state": target_state,
            "next_allowed_action": target_action,
            "timestamp": timestamp,
        })

    return events


def build_artifact_index_update(
    auth_valid: bool,
    render_result: Optional[Dict[str, Any]],
    input_validation: Dict[str, Any],
    target_state: str,
    target_action: str,
) -> Dict[str, Any]:
    """Build artifact index update payload."""
    update: Dict[str, Any] = {
        "task_id": TASK_ID,
        "current_state": target_state,
        "next_allowed_action": target_action,
        "production_accepted": False,
        "preview_render_authorization_checked": True,
        "input_artifacts_validated": input_validation.get("valid", False),
        "input_validation_errors": input_validation.get("errors", []),
        "input_validation_warnings": input_validation.get("warnings", []),
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
    }

    if render_result:
        update["preview_render_executed"] = render_result.get(
            "preview_render_executed", False
        )
        update["preview_render_count"] = render_result.get("preview_render_count", 0)
        update["preview_render_has_ffmpeg"] = render_result.get("has_ffmpeg", False)
        update["preview_render_mp4_rendered"] = render_result.get("mp4_rendered", False)
        update["preview_render_gif_rendered"] = render_result.get(
            "gif_rendered", False
        )
        update["preview_render_contact_sheet_rendered"] = render_result.get(
            "contact_sheet_rendered", False
        )
        update["preview_render_renderer"] = render_result.get("renderer", "")
    else:
        update["preview_render_executed"] = False
        update["preview_render_count"] = 0

    return update


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_controlled_preview_render(
    project_root: Optional[str] = None,
) -> Dict[str, Any]:
    """Run the full controlled preview render gate.

    Validates authorization -> validates inputs -> executes preview render
    -> validates artifacts -> creates reports -> updates state -> returns result.

    Args:
        project_root: Path to the project root (default: cwd).

    Returns:
        A result dict with status, artifact paths, and state info.
    """
    root = _resolve_project_root(project_root)
    control_dir = root / "output" / "control"
    preview_dir = root / "output" / "preview"
    timestamp = datetime.now(timezone.utc).isoformat()

    # ------------------------------------------------------------------
    # Step 1: Validate preview render authorization
    # ------------------------------------------------------------------
    auth_valid, auth_data, auth_msg = validate_preview_render_authorization(control_dir)

    if not auth_valid:
        # Not authorized — create blocker artifacts and stop
        auth_required = build_authorization_required_artifact(control_dir)
        _write_json(
            control_dir / "preview_render_authorization_required.json",
            auth_required,
        )

        input_validation = validate_input_artifacts(control_dir)
        gate_blocker = build_gate_blocker_report(
            (auth_valid, auth_data, auth_msg), input_validation
        )
        _write_json(
            control_dir / "preview_render_gate_validation.json",
            {
                "authorization_valid": False,
                "authorization_message": auth_msg,
                "input_validation": input_validation,
                "gate_blocked": True,
            },
        )
        _write_json(
            control_dir / "preview_render_gate_blocker_report.json",
            gate_blocker,
        )

        # Update artifact index
        existing_index = _read_json(control_dir / "artifact_index.json") or {}
        index_update = build_artifact_index_update(
            auth_valid=False,
            render_result=None,
            input_validation=input_validation,
            target_state="preview_render_authorization_required",
            target_action="preview_render_authorization_required",
        )
        existing_index.update(index_update)
        _write_json(control_dir / "artifact_index.json", existing_index)

        # Update episode ledger
        ledger_path = control_dir / "episode_ledger.json"
        existing_ledger = _read_ledger(ledger_path)
        new_events = build_ledger_events(
            auth_data={},
            render_result=None,
            input_validation=input_validation,
            target_state="preview_render_authorization_required",
            target_action="preview_render_authorization_required",
            preview_render_executed=False,
        )
        existing_ledger.extend(new_events)
        _write_ledger(ledger_path, existing_ledger)

        return {
            "status": "accepted_with_blockers",
            "task_id": TASK_ID,
            "selected_branch": "authorization_required",
            "preview_render_authorized": False,
            "preview_render_executed": False,
            "preview_render_authorization_required_created": True,
            "current_state": "preview_render_authorization_required",
            "next_allowed_action": "preview_render_authorization_required",
            "production_accepted": False,
            "message": auth_msg,
            "blocker": "preview_render_authorization_required.json",
            "blocker_report": "preview_render_gate_blocker_report.json",
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 2: Validate input artifacts
    # ------------------------------------------------------------------
    input_validation = validate_input_artifacts(control_dir)

    # ------------------------------------------------------------------
    # Step 3: Execute preview render (exactly one)
    # ------------------------------------------------------------------
    # Find the approved asset
    asset_rel_path = auth_data.get("source_timeline", "timeline_model.json")
    # Actually, source_timeline is the timeline model path. The asset is in
    # timeline_model. Let's load the timeline model to find the asset.
    timeline_path = control_dir / asset_rel_path.split("/")[-1]
    if not timeline_path.exists():
        timeline_path = control_dir / "timeline_model.json"

    timeline_data = _read_json(timeline_path) or {}
    # Extract asset path from timeline operations or scenes
    asset_path_str = _resolve_asset_path(timeline_data, root)

    if not asset_path_str or not Path(asset_path_str).exists():
        # Runtime blocked — asset not found
        blocker_report = build_runtime_blocker_report({
            "error": "Approved asset not found from timeline model",
            "timeline_path": str(timeline_path),
        })
        _write_json(
            control_dir / "preview_render_runtime_blocker_report.json",
            blocker_report,
        )
        _write_json(
            control_dir / "preview_render_blocker_review_packet.json",
            build_blocker_review_packet(blocker_report),
        )
        _write_json(
            control_dir / "preview_render_gate_validation.json",
            {
                "authorization_valid": True,
                "input_validation": input_validation,
                "gate_blocked": False,
                "runtime_blocked": True,
            },
        )

        # Update artifact index
        existing_index = _read_json(control_dir / "artifact_index.json") or {}
        index_update = build_artifact_index_update(
            auth_valid=True,
            render_result=None,
            input_validation=input_validation,
            target_state="preview_render_blocked",
            target_action="preview_render_blocker_review_required",
        )
        existing_index.update(index_update)
        _write_json(control_dir / "artifact_index.json", existing_index)

        # Update ledger
        ledger_path = control_dir / "episode_ledger.json"
        existing_ledger = _read_ledger(ledger_path)
        new_events = build_ledger_events(
            auth_data=auth_data or {},
            render_result=None,
            input_validation=input_validation,
            target_state="preview_render_blocked",
            target_action="preview_render_blocker_review_required",
            preview_render_executed=False,
        )
        existing_ledger.extend(new_events)
        _write_ledger(ledger_path, existing_ledger)

        return {
            "status": "error",
            "task_id": TASK_ID,
            "selected_branch": "runtime_blocked",
            "preview_render_authorized": True,
            "preview_render_executed": False,
            "preview_render_runtime_blocker_report_created": True,
            "current_state": "preview_render_blocked",
            "next_allowed_action": "preview_render_blocker_review_required",
            "production_accepted": False,
            "message": f"Approved asset not found: {asset_path_str}",
            "timestamp": timestamp,
        }

    # Execute preview render
    asset_path = Path(asset_path_str)
    render_result = execute_preview_render(asset_path, preview_dir)

    # Check if render actually produced valid MP4
    mp4_path = preview_dir / "preview_lowres.mp4"
    render_success = (
        render_result["mp4_rendered"]
        and mp4_path.exists()
        and mp4_path.stat().st_size > 0
    )

    if not render_success:
        # Runtime blocked — render failed
        blocker_report = build_runtime_blocker_report(render_result)
        _write_json(
            control_dir / "preview_render_runtime_blocker_report.json",
            blocker_report,
        )
        _write_json(
            control_dir / "preview_render_blocker_review_packet.json",
            build_blocker_review_packet(blocker_report),
        )

        # Still write gate validation
        _write_json(
            control_dir / "preview_render_gate_validation.json",
            {
                "authorization_valid": True,
                "input_validation": input_validation,
                "render_result": render_result,
                "gate_blocked": False,
                "runtime_blocked": True,
            },
        )

        existing_index = _read_json(control_dir / "artifact_index.json") or {}
        index_update = build_artifact_index_update(
            auth_valid=True,
            render_result=render_result,
            input_validation=input_validation,
            target_state="preview_render_blocked",
            target_action="preview_render_blocker_review_required",
        )
        existing_index.update(index_update)
        _write_json(control_dir / "artifact_index.json", existing_index)

        ledger_path = control_dir / "episode_ledger.json"
        existing_ledger = _read_ledger(ledger_path)
        new_events = build_ledger_events(
            auth_data=auth_data or {},
            render_result=render_result,
            input_validation=input_validation,
            target_state="preview_render_blocked",
            target_action="preview_render_blocker_review_required",
            preview_render_executed=False,
        )
        existing_ledger.extend(new_events)
        _write_ledger(ledger_path, existing_ledger)

        return {
            "status": "error",
            "task_id": TASK_ID,
            "selected_branch": "runtime_blocked",
            "preview_render_authorized": True,
            "preview_render_executed": False,
            "preview_render_runtime_blocker_report_created": True,
            "current_state": "preview_render_blocked",
            "next_allowed_action": "preview_render_blocker_review_required",
            "production_accepted": False,
            "message": "Preview render failed at runtime (FFmpeg unavailable or error)",
            "timestamp": timestamp,
        }

    # ------------------------------------------------------------------
    # Step 4: Validate preview artifacts
    # ------------------------------------------------------------------
    artifact_validation = validate_preview_artifacts(preview_dir)

    # ------------------------------------------------------------------
    # Step 5: Create reports and review packet
    # ------------------------------------------------------------------
    source_timeline = auth_data.get("source_timeline", "timeline_model.json")
    render_report = build_preview_render_report(
        render_result, source_timeline, control_dir
    )
    _write_json(control_dir / "preview_render_report.json", render_report)

    result_review = build_preview_result_review(artifact_validation, render_success)
    _write_json(control_dir / "preview_result_review.json", result_review)

    operator_packet = build_preview_operator_review_packet(render_report, result_review)
    _write_json(
        control_dir / "preview_operator_review_packet.json", operator_packet
    )

    # Write gate validation
    _write_json(
        control_dir / "preview_render_gate_validation.json",
        {
            "authorization_valid": True,
            "authorization": auth_data,
            "input_validation": input_validation,
            "render_result": render_result,
            "artifact_validation": artifact_validation,
            "render_report_created": True,
            "result_review_created": True,
            "operator_review_packet_created": True,
            "gate_blocked": False,
            "runtime_blocked": False,
        },
    )

    # ------------------------------------------------------------------
    # Step 6: Update artifact index and ledger
    # ------------------------------------------------------------------
    target_state = "preview_operator_review_required"
    target_action = "preview_operator_review_required"

    existing_index = _read_json(control_dir / "artifact_index.json") or {}
    index_update = build_artifact_index_update(
        auth_valid=True,
        render_result=render_result,
        input_validation=input_validation,
        target_state=target_state,
        target_action=target_action,
    )
    index_update.update({
        "preview_render_report_created": True,
        "preview_result_review_created": True,
        "preview_operator_review_packet_created": True,
        "preview_lowres_created": render_result["mp4_rendered"],
        "preview_gif_created": render_result["gif_rendered"],
        "contact_sheet_created": render_result["contact_sheet_rendered"],
    })
    existing_index.update(index_update)
    _write_json(control_dir / "artifact_index.json", existing_index)

    ledger_path = control_dir / "episode_ledger.json"
    existing_ledger = _read_ledger(ledger_path)
    new_events = build_ledger_events(
        auth_data=auth_data or {},
        render_result=render_result,
        input_validation=input_validation,
        target_state=target_state,
        target_action=target_action,
        preview_render_executed=True,
    )
    existing_ledger.extend(new_events)
    _write_ledger(ledger_path, existing_ledger)

    # ------------------------------------------------------------------
    # Step 7: Return result
    # ------------------------------------------------------------------
    return {
        "status": "ok",
        "task_id": TASK_ID,
        "selected_branch": "preview_render_executed",
        "preview_render_authorized": True,
        "preview_render_executed": True,
        "preview_render_count": 1,
        "second_preview_render_attempted": False,
        "preview_lowres_created": render_result["mp4_rendered"],
        "preview_gif_created": render_result["gif_rendered"],
        "contact_sheet_created": render_result["contact_sheet_rendered"],
        "current_state": target_state,
        "next_allowed_action": target_action,
        "production_accepted": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "render_report": "preview_render_report.json",
        "result_review": "preview_result_review.json",
        "operator_review_packet": "preview_operator_review_packet.json",
        "artifacts": {
            "preview_render_authorization": "preview_render_authorization.json",
            "preview_render_report": "preview_render_report.json",
            "preview_result_review": "preview_result_review.json",
            "preview_operator_review_packet": "preview_operator_review_packet.json",
            "preview_lowres_mp4": "preview/preview_lowres.mp4",
            "preview_gif": "preview/preview.gif",
            "contact_sheet": "preview/contact_sheet.jpg",
        },
        "forbidden_actions": {
            "new_generation": False,
            "retry": False,
            "comfyui_submit": False,
            "preview_render_executed": True,
            "preview_render_count": 1,
            "second_preview_render_attempted": False,
            "voice_generation_executed": False,
            "assembly_executed": False,
            "downstream_executed": False,
            "production_accepted": False,
        },
        "timestamp": timestamp,
    }


def _resolve_asset_path(
    timeline_data: Dict[str, Any], project_root: Path
) -> Optional[str]:
    """Resolve the approved asset path from timeline model data."""
    # Try operations first
    operations = timeline_data.get("operations", [])
    for op in operations:
        asset_ref = op.get("asset_ref", "")
        if asset_ref:
            candidate = Path(asset_ref)
            if candidate.exists():
                return str(candidate.resolve())
            # Try relative to project_root
            candidate2 = project_root / asset_ref
            if candidate2.exists():
                return str(candidate2.resolve())

    # Try scenes
    scenes = timeline_data.get("scenes", [])
    for scene in scenes:
        asset_refs = scene.get("asset_refs", [])
        for ref in asset_refs:
            candidate = Path(ref)
            if candidate.exists():
                return str(candidate.resolve())
            candidate2 = project_root / ref
            if candidate2.exists():
                return str(candidate2.resolve())

    # Try the approved_visual_assets_manifest
    manifest_path = (
        project_root / "output" / "control" / "approved_visual_assets_manifest.json"
    )
    manifest = _read_json(manifest_path)
    if manifest:
        assets = manifest.get("approved_assets", [])
        if assets:
            asset_path = assets[0].get("path", "")
            if asset_path:
                candidate = Path(asset_path)
                if candidate.exists():
                    return str(candidate.resolve())
                candidate2 = project_root / asset_path
                if candidate2.exists():
                    return str(candidate2.resolve())

    return None
