"""MK-3 Reference-to-Video Scene Agent CLI entrypoint.

Usage:
    python -m app.scene_run --reference path/to/reference.png \
                            --prompt "cinematic scene, subtle motion" \
                            --num-frames 8 \
                            --fps 12.0

Proves the first practical scene-generation loop on the video side:
- Takes one approved image/reference as visual anchor
- Builds usable video prompt from that reference/task
- Selects one video route/workflow by itself
- Generates one real video artifact
- Evaluates generated video through existing QC/intelligence path
- Returns scene verdict: accept / retry_candidate / reject
- Persists scene artifacts, manifest/report, and decision linkage
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.scene.scene_agent import run_scene_agent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="MK-3 Reference-to-Video Scene Agent v1",
    )
    parser.add_argument(
        "--reference",
        required=True,
        help="Path to reference image (approved portrait/reference)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Optional user-specified video prompt (auto-generated if not provided)",
    )
    parser.add_argument(
        "--num-frames",
        type=int,
        default=8,
        help="Number of video frames to generate (default: 8)",
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=12.0,
        help="Output video FPS (default: 12.0)",
    )
    parser.add_argument(
        "--canonical-recipe",
        action="store_true",
        help="Use canonical recipe for video generation",
    )
    parser.add_argument(
        "--weak-recipe",
        action="store_true",
        help="Use weak recipe for degraded scene generation (triggers quality heuristics)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print the final result as JSON",
    )
    parser.add_argument(
        "--reference-locked",
        action="store_true",
        help="Bypass multi-candidate selection when reference is already accepted",
    )
    parser.add_argument(
        "--batch-mode",
        action="store_true",
        help="Use parallel processing to reduce wall time for frame generation",
    )
    parser.add_argument(
        "--bounded-mode",
        action="store_true",
        help="MK-6J: Use bounded batch generation (2 submissions for 6 frames) instead of framewise",
    )
    return parser


def _build_canonical_recipe() -> dict[str, any]:
    """Build canonical recipe for video generation."""
    return {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "euler",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 6.0,
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting, frozen, repetitive, jitter",
    }


def _build_weak_recipe() -> dict[str, any]:
    """Build weak recipe for degraded scene generation (triggers quality heuristics)."""
    return {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "euler",
        "scheduler": "karras",
        "steps": 5,  # Very few steps to reduce variation
        "cfg": 6.0,
        "denoise": 0.05,  # Extremely low denoise to produce near-identical frames
        "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting, frozen, repetitive, jitter",
    }


def _render_result(result: dict) -> None:
    """Render scene generation result to console."""
    print("\n" + "=" * 60)
    print("MK-3 SCENE GENERATION RESULT")
    print("=" * 60)
    print(f"scene_id:         {result.get('scene_id')}")
    print(f"status:           {result.get('status', '').upper()}")
    print(f"reference_image:  {result.get('reference_image_path')}")
    print(f"video_prompt:     {result.get('generated_video_prompt')}")
    print(f"video_workflow:   {result.get('selected_video_workflow')}")
    print(f"video_path:       {result.get('video_path')}")
    print(f"manifest_path:    {result.get('manifest_path')}")
    print(f"qc_report_path:   {result.get('qc_report_path')}")
    print(f"scene_verdict:    {result.get('scene_verdict', '').upper()}")
    if result.get('scene_reasons'):
        print(f"scene_reasons:    {', '.join(result['scene_reasons'])}")
    print(f"generation_start: {result.get('generation_start')}")
    print(f"generation_end:   {result.get('generation_end')}")
    timing_breakdown = result.get('timing_breakdown', {})
    if timing_breakdown:
        print(f"\nTiming Breakdown:")
        print(f"  route:                {timing_breakdown.get('route')}")
        print(f"  generation_strategy: {timing_breakdown.get('generation_strategy')}")
        print(f"  generation_path:      {timing_breakdown.get('generation_path')}")
        print(f"  copy_fallback_used:   {timing_breakdown.get('copy_fallback_used')}")
        print(f"  real_generation_used: {timing_breakdown.get('real_generation_used')}")
        print(f"  real_generation_count:{timing_breakdown.get('real_generation_count', 0)}")
        print(f"  comfy_submission_count:{timing_breakdown.get('comfy_submission_count', 0)}")
        print(f"  images_per_submission:{timing_breakdown.get('images_per_submission', [])}")
        print(f"  frames_requested:     {timing_breakdown.get('frames_requested', 0)}")
        print(f"  frames_generated:     {timing_breakdown.get('frames_generated', 0)}")
        print(f"  pre_scene_latency_s:   {timing_breakdown.get('pre_scene_latency_s', 0):.2f}s")
        print(f"  generation_latency_s: {timing_breakdown.get('generation_latency_s', 0):.2f}s")
        print(f"  candidate_loop_count: {timing_breakdown.get('candidate_loop_count', 0)}")
        print(f"  prep_pass_count:      {timing_breakdown.get('prep_pass_count', 0)}")
        frame_integrity = timing_breakdown.get('frame_integrity', {})
        if frame_integrity:
            print(f"\nFrame Integrity:")
            print(f"  frame_count:          {frame_integrity.get('frame_count', 0)}")
            print(f"  motion_score:         {frame_integrity.get('motion_score', 0):.3f}")
            print(f"  repetitive_ratio:     {frame_integrity.get('repetitive_ratio', 0):.3f}")
            print(f"  frozen_ratio:         {frame_integrity.get('frozen_ratio', 0):.3f}")
    if result.get('error'):
        print(f"error:            {result.get('error')}")
    print("=" * 60 + "\n")


async def _amain() -> None:
    parser = build_parser()
    args = parser.parse_args()

    reference_path = Path(args.reference)
    if not reference_path.exists():
        print(f"Error: reference image not found: {reference_path}")
        raise SystemExit(1)

    comfy_recipe = None
    if args.weak_recipe:
        comfy_recipe = _build_weak_recipe()
    elif args.canonical_recipe:
        comfy_recipe = _build_canonical_recipe()

    try:
        result = await run_scene_agent(
            reference_image_path=str(reference_path),
            user_prompt=args.prompt,
            num_frames=args.num_frames,
            fps=args.fps,
            comfy_recipe=comfy_recipe,
            reference_locked=args.reference_locked,
            batch_mode=args.batch_mode,
            bounded_mode=args.bounded_mode,
        )
    except Exception as exc:
        print(f"SCENE GENERATION FAILED: {exc}")
        raise SystemExit(1)

    result_dict = result.to_dict()
    _render_result(result_dict)

    if args.print_result_json:
        print(json.dumps(result_dict, indent=2, ensure_ascii=False))

    # Exit with error code if failed
    if result.status == "failed":
        raise SystemExit(1)


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
