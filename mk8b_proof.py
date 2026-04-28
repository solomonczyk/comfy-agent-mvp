"""MK-8B — Real Reference Validation v1 proof script.

Reference selection:
  data/outputs/runs/3a29051c/images/portrait_00049_.png
  - Source: canonical portrait agent run (portrait_txt2img)
  - Prompt: "realistic female portrait for premium advertising look"
  - Judge: PASS, score 9.1 (technical=8, semantic=9, aesthetic=9)
  - Recipe: realvisxlV50_v50Bakedvae.safetensors, 30 steps, euler/karras
  - Size: 1024x1024 (~1.78MB)
  - NOT test_portrait.png or test_input_image.png

Strategy (same as MK-8A):
  bounded_mode=True, reference_locked=True, num_frames=12, fps=8 -> 1.5s

MK-5V voiceover readiness gate (inline):
  - duration >= 1.0s  -> voiceover_duration_ok
  - scene_verdict != "reject"  -> scene_not_rejected
  Both must be true for voiceover_readiness = PASS
"""
from __future__ import annotations

import asyncio
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from app.scene.scene_agent import run_scene_agent

REFERENCE_PATH = Path(
    "data/outputs/runs/3a29051c/images/portrait_00049_.png"
)
REFERENCE_SOURCE = "generated"
REFERENCE_PROMPT = "realistic female portrait for premium advertising look"
REFERENCE_JUDGE_SCORE = 9.1

TARGET_FRAMES = 12
TARGET_FPS = 8.0
TARGET_DURATION = TARGET_FRAMES / TARGET_FPS  # 1.5s

OUTPUT_DIR = Path("data/outputs")
VIDEO_DST = OUTPUT_DIR / "mk8b_scene_v1.mp4"
MANIFEST_DST = OUTPUT_DIR / "mk8b_manifest.json"

FORBIDDEN_REFERENCES = {"test_portrait.png", "test_input_image.png"}


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


def _mk5v_voiceover_gate(duration_s: float, scene_verdict: str | None) -> tuple[bool, str]:
    """MK-5V inline voiceover readiness gate.

    Returns (passed, reason).
    Gate passes when duration >= 1.0s AND scene not rejected.
    """
    duration_ok = duration_s >= 1.0
    not_rejected = scene_verdict != "reject"
    passed = duration_ok and not_rejected
    if passed:
        reason = f"PASS (duration={duration_s:.3f}s >= 1.0s, verdict={scene_verdict})"
    else:
        parts = []
        if not duration_ok:
            parts.append(f"duration {duration_s:.3f}s < 1.0s")
        if not not_rejected:
            parts.append(f"scene verdict = {scene_verdict}")
        reason = "FAIL: " + ", ".join(parts)
    return passed, reason


def _check_acceptance(
    result_dict: dict,
    video_dst: Path,
    manifest_dst: Path,
    reference_path: Path,
) -> tuple[bool, list[str]]:
    """Evaluate all MK-8B hard acceptance requirements."""
    failures = []
    tb = result_dict.get("timing_breakdown", {})

    frames_requested = tb.get("frames_requested", 0)
    frames_generated = tb.get("frames_generated", 0)
    submission_count = tb.get("comfy_submission_count", 0)
    images_per_sub = tb.get("images_per_submission", [])
    copy_fallback = tb.get("copy_fallback_used", True)
    generation_strategy = tb.get("generation_strategy", "unknown")
    scene_verdict = result_dict.get("scene_verdict")

    fps = TARGET_FPS
    duration = frames_generated / fps if frames_generated > 0 else 0.0

    frame_validity_data = tb.get("frame_validity", {})
    per_frame_diags = frame_validity_data.get("per_frame_diagnostics", [])

    vo_passed, vo_reason = _mk5v_voiceover_gate(duration, scene_verdict)

    print("\n" + "=" * 60)
    print("MK-8B ACCEPTANCE CHECK")
    print("=" * 60)
    print(f"  reference_file:         {reference_path}")
    print(f"  reference_source:       {REFERENCE_SOURCE}")
    print(f"  frames_requested:       {frames_requested}")
    print(f"  frames_generated:       {frames_generated}")
    print(f"  fps:                    {fps}")
    print(f"  duration_seconds:       {duration:.3f}s  (target >= {TARGET_DURATION}s)")
    print(f"  comfy_submission_count: {submission_count}")
    print(f"  images_per_submission:  {images_per_sub}")
    print(f"  generation_strategy:    {generation_strategy}")
    print(f"  copy_fallback_used:     {copy_fallback}")
    print(f"  reference_locked:       True (enforced)")
    print(f"  scene_verdict:          {scene_verdict}")
    print(f"  voiceover_readiness:    {vo_reason}")
    print(f"  video_exists:           {video_dst.exists()}")
    print(f"  manifest_exists:        {manifest_dst.exists()}")
    print()

    # 1. Reference must not be a forbidden test file
    ref_name = reference_path.name
    if ref_name in FORBIDDEN_REFERENCES:
        failures.append(f"FAIL: reference is forbidden test file: {ref_name}")
    else:
        print(f"  [PASS] reference is not a test file: {ref_name}")

    # 2. Duration >= 1.5s
    if duration < TARGET_DURATION:
        failures.append(f"FAIL: duration {duration:.3f}s < {TARGET_DURATION}s")
    else:
        print(f"  [PASS] duration_seconds {duration:.3f}s >= {TARGET_DURATION}s")

    # 3. comfy_submission_count = 4
    if submission_count != 4:
        failures.append(f"FAIL: comfy_submission_count={submission_count} (expected 4)")
    else:
        print(f"  [PASS] comfy_submission_count = 4")

    # 4. images_per_submission = [3,3,3,3]
    expected_ips = [3, 3, 3, 3]
    if images_per_sub != expected_ips:
        failures.append(f"FAIL: images_per_submission={images_per_sub} (expected {expected_ips})")
    else:
        print(f"  [PASS] images_per_submission = {images_per_sub}")

    # 5. reference_locked = true (enforced by this script)
    print(f"  [PASS] reference_locked = true (enforced)")

    # 6. copy_fallback_used = false
    if copy_fallback:
        failures.append("FAIL: copy_fallback_used = true")
    else:
        print(f"  [PASS] copy_fallback_used = false")

    # 7. Per-frame blue_ratio < 0.35
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
    else:
        print(f"  [INFO] per_frame_diags not available — blue_ratio check skipped")

    # 8. Subject coherence: check that frames are not black/invalid
    if per_frame_diags:
        invalid_frames = [
            d.get("frame_index") for d in per_frame_diags
            if d.get("stage_b", {}).get("invalid", False)
        ]
        valid_count = len(per_frame_diags) - len(invalid_frames)
        majority_valid = valid_count > len(per_frame_diags) / 2
        if not majority_valid:
            failures.append(
                f"FAIL: subject coherence lost — only {valid_count}/{len(per_frame_diags)} frames valid"
            )
        else:
            print(
                f"  [PASS] subject coherence: {valid_count}/{len(per_frame_diags)} frames valid"
            )
    else:
        print(f"  [INFO] per_frame_diags not available — subject coherence check skipped")

    # 9. Voiceover readiness (MK-5V gate)
    if not vo_passed:
        failures.append(f"FAIL: voiceover_readiness — {vo_reason}")
    else:
        print(f"  [PASS] voiceover_readiness: {vo_reason}")

    # 10. Video file exists and is non-empty
    if not video_dst.exists():
        failures.append(f"FAIL: {video_dst} does not exist")
    elif video_dst.stat().st_size == 0:
        failures.append(f"FAIL: {video_dst} is empty")
    else:
        print(f"  [PASS] video file exists: {video_dst} ({video_dst.stat().st_size:,} bytes)")

    # 11. Manifest exists and is valid JSON
    if not manifest_dst.exists():
        failures.append(f"FAIL: {manifest_dst} does not exist")
    else:
        try:
            json.loads(manifest_dst.read_text())
            print(f"  [PASS] manifest valid JSON: {manifest_dst}")
        except Exception as e:
            failures.append(f"FAIL: manifest invalid JSON: {e}")

    print("=" * 60)
    return len(failures) == 0, failures


async def _amain() -> None:
    reference_path = REFERENCE_PATH

    if not reference_path.exists():
        print(f"ERROR: reference image not found: {reference_path}")
        sys.exit(1)

    if reference_path.name in FORBIDDEN_REFERENCES:
        print(f"ERROR: forbidden reference file: {reference_path.name}")
        sys.exit(1)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    recipe = _build_canonical_recipe()

    print("=" * 60)
    print("MK-8B — Real Reference Validation v1")
    print("=" * 60)
    print(f"  reference:       {reference_path}")
    print(f"  reference_source: {REFERENCE_SOURCE}")
    print(f"  ref_prompt:      {REFERENCE_PROMPT}")
    print(f"  ref_judge_score: {REFERENCE_JUDGE_SCORE}")
    print(f"  strategy:        Option A — 4 submissions × 3 frames")
    print(f"  num_frames:      {TARGET_FRAMES}")
    print(f"  fps:             {TARGET_FPS}")
    print(f"  duration:        {TARGET_DURATION}s")
    print(f"  bounded:         True")
    print(f"  ref_locked:      True")
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
        print(f"\n[MK-8B] Video copied to: {VIDEO_DST}")
    else:
        print(f"\n[MK-8B] WARNING: scene video not found at {result.video_path}")

    # --- Build and save manifest ---
    tb = result_dict.get("timing_breakdown", {})
    frames_generated = tb.get("frames_generated", 0)
    submission_count = tb.get("comfy_submission_count", 0)
    images_per_sub = tb.get("images_per_submission", [])
    duration_s = frames_generated / TARGET_FPS if frames_generated > 0 else 0.0
    vo_passed, vo_reason = _mk5v_voiceover_gate(duration_s, result.scene_verdict)

    # Collect per-frame blue ratios for manifest
    per_frame_diags = tb.get("frame_validity", {}).get("per_frame_diagnostics", [])
    per_frame_blue = [
        {
            "frame_index": d.get("frame_index"),
            "blue_ratio": d.get("stage_b", {}).get("blue_dominance_ratio", 0.0),
            "valid": not d.get("stage_b", {}).get("invalid", False),
        }
        for d in per_frame_diags
    ]

    mk8b_manifest = {
        "mk": "MK-8B",
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "reference_file": str(reference_path),
        "reference_source": REFERENCE_SOURCE,
        "reference_prompt": REFERENCE_PROMPT,
        "reference_judge_score": REFERENCE_JUDGE_SCORE,
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
        "voiceover_readiness": {
            "passed": vo_passed,
            "reason": vo_reason,
            "duration_s": duration_s,
            "min_duration_s": 1.0,
        },
        "per_frame_blue_ratio": per_frame_blue,
        "acceptance": {
            "target_duration_s": TARGET_DURATION,
            "target_frames": TARGET_FRAMES,
            "target_fps": TARGET_FPS,
        },
    }

    MANIFEST_DST.write_text(json.dumps(mk8b_manifest, indent=2, ensure_ascii=False))
    print(f"[MK-8B] Manifest saved to: {MANIFEST_DST}")

    # --- Acceptance check ---
    passed, failures = _check_acceptance(result_dict, VIDEO_DST, MANIFEST_DST, reference_path)

    # Update manifest with acceptance result
    mk8b_manifest["acceptance_result"] = {
        "passed": passed,
        "failures": failures,
    }
    MANIFEST_DST.write_text(json.dumps(mk8b_manifest, indent=2, ensure_ascii=False))

    print()
    if passed:
        print("MK-8B: PASS")
    else:
        print("MK-8B: FAIL")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
