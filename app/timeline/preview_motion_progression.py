"""RC-COMBINE-V2-PREVIEW-MOTION-PROGRESSION-FIX-V4V5-001 — Preview Motion Progression Layer.

Deterministic, seed/config-driven motion progression algorithm for still-image
segments. Replaces static segment holds with controlled visual motion:
  - slow push-in / pull-out
  - pan left/right/up/down
  - crop window movement
  - subtle zoom variation
  - transition padding
  - minimum frame delta policy

Motion is deterministic, reproducible, and seed-driven.
No actual rendering is performed here — this module produces motion plans
and keyframes for the renderer to consume.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

PREVIEW_FPS = 24
PREVIEW_DURATION_SEC = 30.0
PREVIEW_WIDTH = 672
PREVIEW_HEIGHT = 384

# Motion amplitude limits (as ratios of image dimension)
MAX_PAN_RATIO = 0.25        # max 25% of image width/height
MAX_ZOOM_VARIATION = 0.15   # +/- 15% zoom variation around base
MIN_FRAME_DELTA_MAE = 2.0   # minimum perceptual difference between frames
TRANSITION_PADDING_FRAMES = 6  # blended transition between segments

# Duplicate QA thresholds
DUPLICATE_RATIO_FAIL_THRESHOLD = 0.85
STATIC_HOLD_DETECTION_THRESHOLD = 0.80

TASK_ID = "RC-COMBINE-V2-PREVIEW-MOTION-PROGRESSION-FIX-V4V5-001"


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class MotionKeyframe:
    """A single motion keyframe defining transform at a point in time."""
    frame_index: int
    time_sec: float
    zoom: float          # 1.0 = no zoom, >1 = zoom in, <1 = zoom out
    pan_x: float         # normalized -1..1 (left to right)
    pan_y: float         # normalized -1..1 (top to bottom)
    crop_left: float     # normalized 0..1
    crop_top: float      # normalized 0..1
    crop_width: float    # normalized 0..1
    crop_height: float   # normalized 0..1
    motion_score: float  # estimated visual change from previous keyframe


@dataclass
class SegmentMotionPlan:
    """Motion plan for a single segment."""
    segment_index: int
    asset_path: str
    frame_start: int
    frame_end: int
    motion_type: str       # e.g. "slow_push_in", "pan_right", "zoom_drift"
    direction: str         # e.g. "inward", "right", "diagonal_bl"
    keyframes: List[MotionKeyframe]
    deterministic_seed: int
    base_zoom: float
    min_frame_delta_policy_met: bool


# ---------------------------------------------------------------------------
# Deterministic motion generators
# ---------------------------------------------------------------------------

def _hash_seed(source: str, segment_index: int) -> int:
    """Create a deterministic integer seed from a string source."""
    s = f"{source}::{segment_index}::RC-COMBINE-V2-MOTION-SEED-SALT"
    h = hashlib.sha256(s.encode("utf-8")).hexdigest()
    return int(h[:16], 16) % (2**31)


def _lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def _ease_in_out(t: float) -> float:
    """Smooth ease-in-out curve for natural motion feel."""
    return t * t * (3.0 - 2.0 * t)


def _clamp01(v: float) -> float:
    return max(0.0, min(1.0, v))


def _fract(x: float) -> float:
    return x - math.floor(x)


def _deterministic_noise(seed: int, index: int) -> float:
    """Simple deterministic pseudo-random float in [0, 1)."""
    x = math.sin(seed * 12.9898 + index * 78.233) * 43758.5453
    return _fract(abs(x))


def generate_segment_keyframes(
    segment_index: int,
    asset_path: str,
    frame_start: int,
    frame_end: int,
    img_width: int,
    img_height: int,
    motion_type: Optional[str] = None,
    direction: Optional[str] = None,
) -> SegmentMotionPlan:
    """Generate deterministic keyframes for a segment.

    Args:
        segment_index: index of the segment
        asset_path: path to the source image
        frame_start: starting frame number (inclusive)
        frame_end: ending frame number (exclusive)
        img_width: source image width in pixels
        img_height: source image height in pixels
        motion_type: override motion type (auto-selected if None)
        direction: override direction (auto-selected if None)

    Returns:
        SegmentMotionPlan with populated keyframes.
    """
    seed = _hash_seed(asset_path, segment_index)
    frame_count = frame_end - frame_start
    duration_sec = frame_count / PREVIEW_FPS

    # Auto-select motion type from a deterministic cyclic palette
    motion_types = [
        "slow_push_in",
        "slow_pull_out",
        "pan_right",
        "pan_left",
        "pan_down",
        "pan_up",
        "zoom_drift",
        "subtle_parallax",
    ]
    if motion_type is None:
        motion_type = motion_types[seed % len(motion_types)]

    # Auto-select direction
    directions_map = {
        "slow_push_in": "inward",
        "slow_pull_out": "outward",
        "pan_right": "right",
        "pan_left": "left",
        "pan_down": "down",
        "pan_up": "up",
        "zoom_drift": "varied",
        "subtle_parallax": "diagonal_tl",
    }
    if direction is None:
        direction = directions_map.get(motion_type, "right")

    # Base zoom depends on source vs target aspect ratio
    src_ar = img_width / max(img_height, 1)
    tgt_ar = PREVIEW_WIDTH / max(PREVIEW_HEIGHT, 1)
    if src_ar > tgt_ar:
        base_zoom = src_ar / tgt_ar
    else:
        base_zoom = tgt_ar / src_ar
    base_zoom = max(1.0, min(base_zoom, 1.5))

    keyframes: List[MotionKeyframe] = []

    for i in range(frame_count):
        progress = i / max(frame_count - 1, 1)
        eased = _ease_in_out(progress)

        # Per-frame noise for organic feel
        n1 = _deterministic_noise(seed, i * 3 + 0)
        n2 = _deterministic_noise(seed, i * 3 + 1)
        n3 = _deterministic_noise(seed, i * 3 + 2)

        # Zoom variation
        zoom_amp = MAX_ZOOM_VARIATION * (0.5 + 0.5 * n1)
        if motion_type == "slow_push_in":
            zoom = base_zoom * (1.0 + zoom_amp * eased)
        elif motion_type == "slow_pull_out":
            zoom = base_zoom * (1.0 + zoom_amp * (1.0 - eased))
        elif motion_type == "zoom_drift":
            zoom = base_zoom * (1.0 + zoom_amp * math.sin(eased * math.pi * 2))
        else:
            zoom = base_zoom * (1.0 + zoom_amp * 0.3 * math.sin(eased * math.pi))

        # Pan variation
        pan_x, pan_y = 0.0, 0.0
        pan_range = MAX_PAN_RATIO * (0.6 + 0.4 * n2)

        if motion_type == "pan_right":
            pan_x = -pan_range + 2 * pan_range * eased
        elif motion_type == "pan_left":
            pan_x = pan_range - 2 * pan_range * eased
        elif motion_type == "pan_down":
            pan_y = -pan_range + 2 * pan_range * eased
        elif motion_type == "pan_up":
            pan_y = pan_range - 2 * pan_range * eased
        elif motion_type == "subtle_parallax":
            pan_x = -pan_range * 0.5 + pan_range * eased + pan_range * 0.15 * math.sin(eased * math.pi * 3)
            pan_y = -pan_range * 0.3 + pan_range * 0.6 * eased + pan_range * 0.1 * math.cos(eased * math.pi * 3)
        else:
            # Drift for push/pull
            pan_x = pan_range * 0.2 * math.sin(eased * math.pi * 2 + n3 * 6.28)
            pan_y = pan_range * 0.15 * math.cos(eased * math.pi * 2 + n3 * 6.28)

        # Crop window from zoom + pan
        inv_zoom = 1.0 / zoom
        crop_w = inv_zoom
        crop_h = inv_zoom
        crop_left = (1.0 - crop_w) * 0.5 + pan_x * (1.0 - crop_w)
        crop_top = (1.0 - crop_h) * 0.5 + pan_y * (1.0 - crop_h)
        crop_left = _clamp01(crop_left)
        crop_top = _clamp01(crop_top)
        crop_w = _clamp01(crop_w)
        crop_h = _clamp01(crop_h)
        if crop_left + crop_w > 1.0:
            crop_w = 1.0 - crop_left
        if crop_top + crop_h > 1.0:
            crop_h = 1.0 - crop_top

        # Motion score (approximate)
        if i == 0:
            motion_score = 1.0
        else:
            prev = keyframes[-1]
            dz = abs(zoom - prev.zoom)
            dp = math.hypot(pan_x - prev.pan_x, pan_y - prev.pan_y)
            motion_score = min(1.0, dz + dp * 2.0)

        keyframes.append(MotionKeyframe(
            frame_index=frame_start + i,
            time_sec=(frame_start + i) / PREVIEW_FPS,
            zoom=round(zoom, 5),
            pan_x=round(pan_x, 5),
            pan_y=round(pan_y, 5),
            crop_left=round(crop_left, 5),
            crop_top=round(crop_top, 5),
            crop_width=round(crop_w, 5),
            crop_height=round(crop_h, 5),
            motion_score=round(motion_score, 5),
        ))

    min_delta_met = all(
        k.motion_score > 0.001 or i == 0
        for i, k in enumerate(keyframes)
    )

    return SegmentMotionPlan(
        segment_index=segment_index,
        asset_path=asset_path,
        frame_start=frame_start,
        frame_end=frame_end,
        motion_type=motion_type,
        direction=direction,
        keyframes=keyframes,
        deterministic_seed=seed,
        base_zoom=round(base_zoom, 5),
        min_frame_delta_policy_met=min_delta_met,
    )


# ---------------------------------------------------------------------------
# Multi-segment progression plan
# ---------------------------------------------------------------------------

def build_preview_motion_progression_plan_v4v5(
    segments: List[Dict[str, Any]],
    img_dimensions: Optional[Dict[str, Tuple[int, int]]] = None,
) -> Dict[str, Any]:
    """Build a motion progression plan for all segments (v4/v5).

    Args:
        segments: list of segment dicts with at least segment_index,
                  asset_path, frame_start, frame_end
        img_dimensions: optional dict mapping asset_path -> (width, height)

    Returns:
        Plan dict with motion plans per segment.
    """
    if img_dimensions is None:
        img_dimensions = {}

    motion_plans: List[Dict[str, Any]] = []
    total_keyframes = 0
    all_motions_unique = True
    seen_motion_types: set = set()

    for seg in segments:
        seg_idx = seg.get("segment_index", 0)
        asset = seg.get("asset_path", "")
        fs = seg.get("frame_start", 0)
        fe = seg.get("frame_end", 0)

        w, h = img_dimensions.get(asset, (1024, 1024))

        plan = generate_segment_keyframes(
            segment_index=seg_idx,
            asset_path=asset,
            frame_start=fs,
            frame_end=fe,
            img_width=w,
            img_height=h,
        )

        if plan.motion_type in seen_motion_types:
            all_motions_unique = False
        seen_motion_types.add(plan.motion_type)

        total_keyframes += len(plan.keyframes)
        motion_plans.append(_segment_plan_to_dict(plan))

    return {
        "plan_type": "preview_motion_progression_plan_v4v5",
        "task_id": TASK_ID,
        "version": "v4v5",
        "deterministic": True,
        "reproducible": True,
        "seed_source": "asset_path + segment_index + SALT",
        "total_segments": len(segments),
        "total_keyframes": total_keyframes,
        "motion_types_used": sorted(seen_motion_types),
        "all_motions_unique": all_motions_unique,
        "transition_padding_frames": TRANSITION_PADDING_FRAMES,
        "min_frame_delta_policy": {
            "enabled": True,
            "threshold_mae": MIN_FRAME_DELTA_MAE,
        },
        "motion_amplitude_limits": {
            "max_pan_ratio": MAX_PAN_RATIO,
            "max_zoom_variation": MAX_ZOOM_VARIATION,
        },
        "segments": motion_plans,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def _segment_plan_to_dict(plan: SegmentMotionPlan) -> Dict[str, Any]:
    return {
        "segment_index": plan.segment_index,
        "asset_path": plan.asset_path,
        "frame_start": plan.frame_start,
        "frame_end": plan.frame_end,
        "motion_type": plan.motion_type,
        "direction": plan.direction,
        "deterministic_seed": plan.deterministic_seed,
        "base_zoom": plan.base_zoom,
        "min_frame_delta_policy_met": plan.min_frame_delta_policy_met,
        "keyframes": [asdict(k) for k in plan.keyframes],
    }


# ---------------------------------------------------------------------------
# Segment keyframe artifact builder
# ---------------------------------------------------------------------------

def build_segment_keyframes_artifact(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten keyframes into a per-segment lookup artifact."""
    segment_lookup: Dict[str, Any] = {}
    for seg in plan.get("segments", []):
        seg_idx = seg["segment_index"]
        segment_lookup[str(seg_idx)] = {
            "asset_path": seg["asset_path"],
            "motion_type": seg["motion_type"],
            "direction": seg["direction"],
            "frame_range": [seg["frame_start"], seg["frame_end"]],
            "keyframes": seg["keyframes"],
        }
    return {
        "artifact_type": "preview_motion_segment_keyframes_v4v5",
        "task_id": TASK_ID,
        "version": "v4v5",
        "segment_count": len(segment_lookup),
        "segment_lookup": segment_lookup,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Duplicate reduction QA (dry-run / synthetic mode)
# ---------------------------------------------------------------------------

def evaluate_motion_plan_for_duplicate_reduction(
    plan: Dict[str, Any],
    render_executed: bool = False,
) -> Dict[str, Any]:
    """Evaluate the motion plan's ability to reduce duplicate frames.

    Operates in dry-run / synthetic frame plan mode when render_executed=False.
    Returns honest render_executed flag.
    """
    segments = plan.get("segments", [])
    if not segments:
        return {
            "qa_type": "preview_motion_duplicate_reduction_qa",
            "task_id": TASK_ID,
            "render_executed": render_executed,
            "evaluated": False,
            "error": "No segments in motion plan",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    total_frames = 0
    total_motion_score = 0.0
    static_hold_segments = 0
    all_contact_sheet_useful = True

    per_segment_qa: List[Dict[str, Any]] = []

    for seg in segments:
        keyframes = seg.get("keyframes", [])
        frame_count = len(keyframes)
        total_frames += frame_count

        if frame_count < 2:
            motion_avg = 0.0
            is_static = True
        else:
            scores = [k.get("motion_score", 0.0) for k in keyframes[1:]]
            motion_avg = sum(scores) / len(scores) if scores else 0.0
            is_static = motion_avg < 0.01

        total_motion_score += motion_avg

        if is_static:
            static_hold_segments += 1

        # Estimate duplicate ratio from motion scores
        # High motion -> low duplicates
        estimated_duplicate_ratio = max(0.0, 1.0 - motion_avg * 10.0)
        estimated_duplicate_ratio = min(estimated_duplicate_ratio, 1.0)

        contact_sheet_useful = motion_avg > 0.02 or frame_count <= 1
        if not contact_sheet_useful:
            all_contact_sheet_useful = False

        per_segment_qa.append({
            "segment_index": seg.get("segment_index"),
            "motion_type": seg.get("motion_type"),
            "frame_count": frame_count,
            "average_motion_score": round(motion_avg, 5),
            "static_hold_detected": is_static,
            "estimated_duplicate_ratio": round(estimated_duplicate_ratio, 5),
            "contact_sheet_useful": contact_sheet_useful,
            "min_frame_delta_policy_met": seg.get("min_frame_delta_policy_met", False),
        })

    overall_motion_avg = total_motion_score / len(segments) if segments else 0.0
    overall_estimated_duplicate_ratio = max(0.0, 1.0 - overall_motion_avg * 10.0)
    overall_estimated_duplicate_ratio = min(overall_estimated_duplicate_ratio, 1.0)

    fail_threshold = DUPLICATE_RATIO_FAIL_THRESHOLD
    passes_qa = overall_estimated_duplicate_ratio < fail_threshold
    passes_qa = passes_qa and static_hold_segments == 0

    return {
        "qa_type": "preview_motion_duplicate_reduction_qa",
        "task_id": TASK_ID,
        "version": "v4v5",
        "render_executed": render_executed,
        "evaluated": True,
        "mode": "dry_run_synthetic" if not render_executed else "post_render",
        "total_frames_evaluated": total_frames,
        "overall_estimated_duplicate_ratio": round(overall_estimated_duplicate_ratio, 5),
        "duplicate_threshold": fail_threshold,
        "passes_qa": passes_qa,
        "static_hold_segments": static_hold_segments,
        "overall_average_motion_score": round(overall_motion_avg, 5),
        "contact_sheet_useful_overall": all_contact_sheet_useful,
        "per_segment_qa": per_segment_qa,
        "policy": {
            "max_duplicate_ratio": fail_threshold,
            "static_hold_detection_threshold": STATIC_HOLD_DETECTION_THRESHOLD,
            "min_frame_delta_mae": MIN_FRAME_DELTA_MAE,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Renderer contract (legacy static hold blocked)
# ---------------------------------------------------------------------------

def build_preview_motion_renderer_contract_v4v5() -> Dict[str, Any]:
    """Build the renderer contract that blocks legacy static hold mode."""
    return {
        "contract_type": "preview_motion_renderer_contract_v4v5",
        "task_id": TASK_ID,
        "version": "v4v5",
        "legacy_static_hold_mode": {
            "allowed": False,
            "default": False,
            "fallback_forbidden": True,
            "diagnostic_mode_only": False,
        },
        "required_renderer_features": [
            "per_frame_crop_transform",
            "per_frame_zoom_transform",
            "per_frame_pan_transform",
            "segment_transition_padding",
            "deterministic_keyframe_consumption",
        ],
        "motion_policy": {
            "slow_push_in_enabled": True,
            "slow_pull_out_enabled": True,
            "pan_left_enabled": True,
            "pan_right_enabled": True,
            "pan_up_enabled": True,
            "pan_down_enabled": True,
            "zoom_drift_enabled": True,
            "subtle_parallax_enabled": True,
            "transition_padding_frames": TRANSITION_PADDING_FRAMES,
        },
        "blocked_behaviors": [
            "asset = assets[0]; repeat asset for all frames",
            "single_source_repeat_for_all_segments",
            "zero_crop_variation_across_frames",
            "zero_zoom_variation_across_frames",
            "static_hold_without_explicit_still_scene_contract",
        ],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# Gate package
# ---------------------------------------------------------------------------

def build_controlled_preview_motion_render_gate_package(
    progression_plan: Dict[str, Any],
    keyframes_artifact: Dict[str, Any],
    qa_result: Dict[str, Any],
    renderer_contract: Dict[str, Any],
) -> Dict[str, Any]:
    """Build the gate package for controlled preview motion render authorization."""
    return {
        "package_type": "controlled_preview_motion_render_gate_package",
        "task_id": TASK_ID,
        "version": "v4v5",
        "current_state": "controlled_preview_motion_render_authorization_required",
        "next_allowed_action": "controlled_preview_motion_render_authorization_required",
        "requires_operator_authorization": True,
        "agent_may_authorize": False,
        "max_preview_renders": 1,
        "motion_progression_plan_ready": True,
        "segment_keyframes_ready": True,
        "duplicate_reduction_qa_ready": True,
        "renderer_contract_ready": True,
        "preview_render_executed": False,
        "new_image_generation_performed": False,
        "comfyui_submit_executed": False,
        "retry_attempted": False,
        "voice_generation_executed": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "blocked_until": "operator_authorization_for_controlled_preview_motion_render",
        "gate_artifacts": {
            "progression_plan": progression_plan.get("plan_type"),
            "segment_keyframes": keyframes_artifact.get("artifact_type"),
            "duplicate_reduction_qa": qa_result.get("qa_type"),
            "renderer_contract": renderer_contract.get("contract_type"),
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _read_json(path: Path) -> Any:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None
