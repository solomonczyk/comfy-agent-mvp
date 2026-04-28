"""KT-6/KT-7 Video-run CLI entrypoint.

Usage (KT-6 plumbing proof, PIL):
    python -m app.video_run --input path/to/video.mp4 --processor pil \
                            --subset-every 5 --max-processed-frames 8

Usage (KT-7 real Comfy edit path):
    python -m app.video_run --input path/to/video.mp4 --processor comfy \
                            --prompt "cinematic lighting, high detail" \
                            --subset-every 9 --max-processed-frames 4 \
                            --width 512 --height 512 --steps 15

Runs the video pipeline: extract -> select subset -> process -> assemble export.
Writes everything under the KT-5 asset structure and persists a video
manifest at data/manifests/video_{video_id}.json.
"""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.assets.paths import ensure_asset_dirs
from app.video.video_orchestrator import run_video_pipeline
from app.video.video_qc import run_video_qc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="KT-6/KT-7 Video Operations CLI",
    )
    parser.add_argument("--input", required=False, help="Path to input video (auto-detects latest if not provided)")
    parser.add_argument(
        "--video-id",
        default=None,
        help="Optional explicit video_id; otherwise derived from input filename",
    )
    parser.add_argument(
        "--extract-fps",
        type=float,
        default=None,
        help="Optional fps for frame extraction (default: source fps)",
    )
    parser.add_argument(
        "--subset-every",
        type=int,
        default=5,
        help="Select every Nth frame for processing (default: 5)",
    )
    parser.add_argument(
        "--export-fps",
        type=float,
        default=12.0,
        help="Output video fps for the assembled export (default: 12)",
    )
    parser.add_argument(
        "--max-processed-frames",
        type=int,
        default=None,
        help="Optional cap on number of processed frames",
    )
    parser.add_argument(
        "--processor",
        choices=["pil", "comfy"],
        default="pil",
        help="Frame processor: 'pil' (KT-6 plumbing) or 'comfy' (KT-7 real edit path)",
    )
    parser.add_argument(
        "--prompt",
        default=None,
        help="Edit prompt (required when --processor=comfy)",
    )
    # Comfy recipe overrides (forwarded as canonical_recipe to run_agent)
    parser.add_argument("--width", type=int, default=None, help="Comfy: target width")
    parser.add_argument("--height", type=int, default=None, help="Comfy: target height")
    parser.add_argument("--steps", type=int, default=None, help="Comfy: sampler steps")
    parser.add_argument("--cfg", type=float, default=None, help="Comfy: CFG scale")
    parser.add_argument(
        "--sampler-name",
        default=None,
        help="Comfy: sampler name (e.g. dpmpp_2m)",
    )
    parser.add_argument(
        "--scheduler",
        default=None,
        help="Comfy: scheduler (e.g. karras)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print the final result as JSON",
    )
    parser.add_argument(
        "--auto-qc",
        action="store_true",
        help="Automatically run video QC after export (seam-fix #2)",
    )
    parser.add_argument(
        "--intelligence",
        action="store_true",
        help="Use intelligence-driven subset selection (v1.1 Video Intelligence)",
    )
    parser.add_argument(
        "--multi-scene",
        action="store_true",
        help="Use multi-scene detection with per-scene decisions (v1.1 Layer 2)",
    )
    return parser


def _build_comfy_recipe(args: argparse.Namespace) -> dict | None:
    """Assemble a canonical_recipe dict from CLI overrides, or None if empty."""
    recipe = {
        "width": args.width,
        "height": args.height,
        "steps": args.steps,
        "cfg": args.cfg,
        "sampler_name": args.sampler_name,
        "scheduler": args.scheduler,
    }
    recipe = {k: v for k, v in recipe.items() if v is not None}
    return recipe or None


async def _amain() -> None:
    parser = build_parser()
    args = parser.parse_args()

    ensure_asset_dirs()

    # Seam-fix #6: Auto-detect input video if not provided
    if not args.input:
        from app.assets.paths import ASSET_PATHS
        inputs_dir = ASSET_PATHS.inputs
        if inputs_dir.exists():
            # Find latest video in data/inputs/
            video_files = list(inputs_dir.glob("*.mp4")) + list(inputs_dir.glob("*.mov")) + list(inputs_dir.glob("*.avi"))
            if video_files:
                input_path = max(video_files, key=lambda p: p.stat().st_mtime)
                print(f"Auto-detected input video: {input_path}")
            else:
                print(f"Error: no video files found in {inputs_dir}")
                raise SystemExit(1)
        else:
            print(f"Error: inputs directory not found: {inputs_dir}")
            raise SystemExit(1)
    else:
        input_path = Path(args.input)

    if not input_path.exists():
        print(f"Error: input video not found: {input_path}")
        raise SystemExit(1)

    if args.processor == "comfy" and not args.prompt:
        print("Error: --prompt is required when --processor=comfy")
        raise SystemExit(2)

    try:
        result = await run_video_pipeline(
            input_path=input_path,
            video_id=args.video_id,
            extract_fps=args.extract_fps,
            subset_every=args.subset_every,
            export_fps=args.export_fps,
            max_processed_frames=args.max_processed_frames,
            processor=args.processor,
            prompt=args.prompt,
            comfy_recipe=_build_comfy_recipe(args),
            intelligence_mode=args.intelligence,
            multi_scene=args.multi_scene,
        )
    except Exception as exc:
        print(f"VIDEO PIPELINE FAILED: {exc}")
        raise SystemExit(1)

    print("\n" + "=" * 60)
    print("VIDEO PIPELINE RESULT")
    print("=" * 60)
    print(f"video_id:         {result['video_id']}")
    print(f"status:           {result['status'].upper()}")
    print(f"processor:        {result.get('processor', args.processor)}")
    print(f"input_path:       {result['input_path']}")
    print(f"frames_dir:       {result['frames_dir']}")
    print(f"frames_extracted: {result['frames_extracted']}")
    print(f"processed_dir:    {result['processed_dir']}")
    print(f"processed_count:  {result['processed_count']}")
    print(f"export_path:      {result['export_path']}")
    print(f"manifest_path:    {result['manifest_path']}")
    if result.get('intelligence_report_path'):
        print(f"intelligence:     {result['intelligence_report_path']}")
    if result.get("per_frame"):
        print("-" * 60)
        print("PER-FRAME LINKAGE:")
        for entry in result["per_frame"]:
            print(
                f"  #{entry['index']:02d} "
                f"status={entry['status']} "
                f"run_id={entry.get('run_id')} "
                f"prompt_id={(entry.get('prompt_id') or '-')[:8]}..."
            )
    print("=" * 60 + "\n")

    # Seam-fix #2: Auto-run video QC if --auto-qc flag is set
    if args.auto_qc and result.get("status") == "completed":
        print("\n" + "=" * 60)
        print("AUTO-RUNNING VIDEO QC")
        print("=" * 60)
        try:
            qc_report = run_video_qc(
                manifest_path=None,
                video_id=result.get("video_id"),
            )
            print(f"\nQC Verdict: {qc_report.get('verdict', 'unknown').upper()}")
            if qc_report.get("reasons"):
                print(f"Reasons: {', '.join(qc_report['reasons'])}")
            print(f"QC Report: {qc_report.get('qc_report_path')}")
            print("=" * 60 + "\n")
        except Exception as exc:
            print(f"VIDEO QC FAILED: {exc}")
            print("=" * 60 + "\n")

    if args.print_result_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
