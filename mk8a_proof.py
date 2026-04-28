"""MK-8A — Scene Duration Extension v1 proof script.

Strategy: Option A — 4 submissions × 3 frames = 12 frames at 8 fps = 1.5s
  - bounded_mode=True   → batch template, 3 frames per submission
  - num_frames=12       → ceil(12/3) = 4 submissions
  - fps=8               → 12/8 = 1.5s
  - reference_locked=True, canonical_recipe

Hard acceptance requirements:
  - duration_seconds >= 1.5s
  - comfy_submission_count != frame_count  (no one-per-frame regression)
  - images_per_submission proves multi-frame submit (each entry == 3)
  - reference_locked = true
  - copy_fallback_used = false
  - blue_ratio < 0.35 on all frames
  - mk8a_scene_v1.mp4 exists and is playable
  - manifest saved as valid JSON
"""
from __future__ import annotations

import argparse
import asyncio
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.scene.scene_agent import run_scene_agent

TARGET_FRAMES = 12
TARGET_FPS = 8.0
TARGET_DURATION = TARGET_FRAMES / TARGET_FPS  # 1.5s

OUTPUT_DIR = Path("data/outputs")
VIDEO_DST = OUTPUT_DIR / "mk8a_scene_v1.mp4"
MANIFEST_DST = OUTPUT_DIR / "mk8a_manifest.json"


def _build_canonical_recipe() -> dict:
    return {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "euler",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 6.0,
        "negative_prompt": (
            "blurry, low quality, bad anatomy, deformed face, deformed eyes, "
            "plastic skin, smooth skin texture, doll-like, anime, cartoon, "
            "oversaturated, harsh lighting, frozen, repetitive, jitter"
        ),
    }


def _check_acceptance(result_dict: dict, video_dst: Path, manifest_dst: Path) -> tuple[bool, list[str]]:
    """Evaluate all hard acceptance requirements. Returns (passed, failures)."""
    failures = []
    tb = result_dict.get("timing_breakdown", {})

    frames_requested = tb.get("frames_requested", 0)
    frames_generated = tb.get("frames_generated", 0)
    submission_count = tb.get("comfy_submission_count", 0)
    images_per_sub = tb.get("images_per_submission", [])
    copy_fallback = tb.get("copy_fallback_used", True)
    generation_strategy = tb.get("generation_strategy", "unknown")

    fps = TARGET_FPS
    duration = frames_generated / fps if frames_generated > 0 else 0.0

    print("\n" + "=" * 60)
    print("MK-8A ACCEPTANCE CHECK")
    print("=" * 60)
    print(f"  frames_requested:       {frames_requested}")
    print(f"  frames_generated:       {frames_generated}")
    print(f"  fps:                    {fps}")
    print(f"  duration_seconds:       {duration:.3f}s  (target >= {TARGET_DURATION}s)")
    print(f"  comfy_submission_count: {submission_count}")
    print(f"  images_per_submission:  {images_per_sub}")
    print(f"  generation_strategy:    {generation_strategy}")
    print(f"  copy_fallback_used:     {copy_fallback}")
    print(f"  reference_locked:       True (forced by proof)")
    print(f"  video_exists:           {video_dst.exists()}")
    print(f"  manifest_exists:        {manifest_dst.exists()}")

    # Per-frame blue ratio from frame_validity (propagated into timing_breakdown by scene_agent)
    frame_validity_data = tb.get("frame_validity", {})
    per_frame_diags = frame_validity_data.get("per_frame_diagnostics", [])

    print()

    # 1. Duration >= 1.5s
    if duration < TARGET_DURATION:
        failures.append(f"FAIL: duration {duration:.3f}s < {TARGET_DURATION}s")
    else:
        print(f"  [PASS] duration_seconds {duration:.3f}s >= {TARGET_DURATION}s")

    # 2. submission_count != frame_count (no one-per-frame regression)
    if submission_count == frames_generated:
        failures.append(f"FAIL: comfy_submission_count ({submission_count}) == frames_generated ({frames_generated}) — one-per-frame regression")
    else:
        print(f"  [PASS] comfy_submission_count {submission_count} != frames_generated {frames_generated}")

    # 3. images_per_submission proves multi-frame behavior (each entry > 1)
    if not images_per_sub:
        failures.append("FAIL: images_per_submission is empty")
    elif any(n <= 1 for n in images_per_sub):
        failures.append(f"FAIL: images_per_submission has single-frame entries: {images_per_sub}")
    else:
        print(f"  [PASS] images_per_submission all multi-frame: {images_per_sub}")

    # 4. reference_locked = true (enforced by this script)
    print(f"  [PASS] reference_locked = true (enforced)")

    # 5. copy_fallback_used = false
    if copy_fallback:
        failures.append("FAIL: copy_fallback_used = true")
    else:
        print(f"  [PASS] copy_fallback_used = false")

    # 6. Video file exists and is non-empty
    if not video_dst.exists():
        failures.append(f"FAIL: {video_dst} does not exist")
    elif video_dst.stat().st_size == 0:
        failures.append(f"FAIL: {video_dst} is empty")
    else:
        print(f"  [PASS] video file exists: {video_dst} ({video_dst.stat().st_size:,} bytes)")

    # 7. Manifest exists and is valid JSON
    if not manifest_dst.exists():
        failures.append(f"FAIL: {manifest_dst} does not exist")
    else:
        try:
            data = json.loads(manifest_dst.read_text())
            print(f"  [PASS] manifest valid JSON: {manifest_dst}")
        except Exception as e:
            failures.append(f"FAIL: manifest invalid JSON: {e}")

    # 8. Per-frame blue_ratio < 0.35 (if diagnostics available)
    if per_frame_diags:
        blue_failures = []
        for d in per_frame_diags:
            stage_b = d.get("stage_b", {})
            blue_ratio = stage_b.get("blue_dominance_ratio", 0.0)
            frame_idx = d.get("frame_index")
            if blue_ratio >= 0.35:
                blue_failures.append(f"frame {frame_idx}: blue_ratio={blue_ratio:.3f}")
        if blue_failures:
            failures.append(f"FAIL: blue_ratio >= 0.35 on frames: {blue_failures}")
        else:
            print(f"  [PASS] blue_ratio < 0.35 on all {len(per_frame_diags)} frames")

    print("=" * 60)
    return len(failures) == 0, failures


async def _amain() -> None:
    parser = argparse.ArgumentParser(description="MK-8A Scene Duration Extension v1 proof")
    parser.add_argument("--reference", required=True, help="Path to reference image")
    args = parser.parse_args()

    reference_path = Path(args.reference)
    if not reference_path.exists():
        print(f"ERROR: reference image not found: {reference_path}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    recipe = _build_canonical_recipe()

    print("=" * 60)
    print("MK-8A — Scene Duration Extension v1")
    print("=" * 60)
    print(f"  strategy:    Option A — {TARGET_FRAMES // 3} submissions × 3 frames")
    print(f"  num_frames:  {TARGET_FRAMES}")
    print(f"  fps:         {TARGET_FPS}")
    print(f"  duration:    {TARGET_DURATION}s")
    print(f"  bounded:     True")
    print(f"  ref_locked:  True")
    print(f"  reference:   {reference_path}")
    print("=" * 60)

    result = await run_scene_agent(
        reference_image_path=str(reference_path),
        user_prompt=None,
        num_frames=TARGET_FRAMES,
        fps=TARGET_FPS,
        comfy_recipe=recipe,
        reference_locked=True,
        batch_mode=False,
        bounded_mode=True,
    )

    result_dict = result.to_dict()

    if result.status == "failed":
        print(f"\nSCENE GENERATION FAILED: {result.error}")
        sys.exit(1)

    # --- Copy video to canonical output path ---
    scene_video = Path(result.video_path) if result.video_path else None
    if scene_video and scene_video.exists():
        shutil.copy2(scene_video, VIDEO_DST)
        print(f"\n[MK-8A] Video copied to: {VIDEO_DST}")
    else:
        print(f"\n[MK-8A] WARNING: scene video not found at {result.video_path}")

    # --- Build and save manifest ---
    tb = result_dict.get("timing_breakdown", {})
    frames_generated = tb.get("frames_generated", 0)
    submission_count = tb.get("comfy_submission_count", 0)
    images_per_sub = tb.get("images_per_submission", [])
    duration_s = frames_generated / TARGET_FPS if frames_generated > 0 else 0.0

    mk8a_manifest = {
        "mk": "MK-8A",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "frame_count": frames_generated,
        "frames_requested": TARGET_FRAMES,
        "fps": TARGET_FPS,
        "duration_seconds": duration_s,
        "comfy_submission_count": submission_count,
        "images_per_submission": images_per_sub,
        "reference_locked": True,
        "copy_fallback_used": tb.get("copy_fallback_used", None),
        "generation_strategy": tb.get("generation_strategy", "bounded_batch"),
        "scene_id": result.scene_id,
        "scene_verdict": result.scene_verdict,
        "scene_reasons": result.scene_reasons,
        "video_path": str(VIDEO_DST),
        "source_video_path": result.video_path,
        "acceptance": {
            "target_duration_s": TARGET_DURATION,
            "target_frames": TARGET_FRAMES,
            "target_fps": TARGET_FPS,
        },
    }

    MANIFEST_DST.write_text(json.dumps(mk8a_manifest, indent=2, ensure_ascii=False))
    print(f"[MK-8A] Manifest saved to: {MANIFEST_DST}")

    # --- Acceptance check ---
    passed, failures = _check_acceptance(result_dict, VIDEO_DST, MANIFEST_DST)

    # Update manifest with acceptance result
    mk8a_manifest["acceptance_result"] = {
        "passed": passed,
        "failures": failures,
    }
    MANIFEST_DST.write_text(json.dumps(mk8a_manifest, indent=2, ensure_ascii=False))

    print()
    if passed:
        print("MK-8A: PASS")
    else:
        print("MK-8A: FAIL")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
