"""
CLI entrypoint for MK-5 Scene AV Attachment & LipSync Integration.

Usage:
    python -m app.scene_av_run --manifest data/manifests/video_scene_20260419_155010_4ad579f0.json
"""

import argparse
import json
import sys
from pathlib import Path

from app.scene.scene_av_agent import run_scene_av


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="MK-5 Scene AV Attachment & LipSync Integration - Attach audio to scene videos and run QC"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to scene manifest JSON file",
    )
    parser.add_argument(
        "--av-route",
        type=str,
        default="audio_mux",
        choices=["audio_mux"],
        help="AV attachment route (default: audio_mux)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print the final result as JSON",
    )
    return parser


def _render_result(result: dict) -> None:
    """Render scene AV attachment result to console."""
    print("\n" + "=" * 60)
    print("MK-5 SCENE AV ATTACHMENT RESULT")
    print("=" * 60)
    print(f"status:                {result.get('status', '').upper()}")
    print(f"scene_id:              {result.get('scene_id')}")
    print(f"source_video_path:     {result.get('source_video_path')}")
    print(f"source_audio_path:     {result.get('source_audio_path')}")
    print(f"av_route:              {result.get('av_route')}")
    print(f"synced_scene_path:     {result.get('synced_scene_path')}")
    print(f"manifest_path:         {result.get('manifest_path')}")
    
    if result.get("error"):
        print(f"error:                 {result.get('error')}")
    
    if result.get("av_processing_fragment"):
        print("\nAV Processing Fragment:")
        for key, value in result.get("av_processing_fragment", {}).items():
            print(f"  {key}: {value}")
    
    if result.get("qc_fragment"):
        print("\nQC Fragment:")
        qc_fragment = result.get("qc_fragment", {})
        print(f"  verdict: {qc_fragment.get('verdict')}")
        print(f"  reasons: {qc_fragment.get('reasons')}")
        if qc_fragment.get("checks"):
            print(f"  checks:")
            for check_name, check_data in qc_fragment.get("checks", {}).items():
                print(f"    {check_name}: {check_data}")
    
    if result.get("decision_fragment"):
        print("\nDecision Fragment:")
        for key, value in result.get("decision_fragment", {}).items():
            print(f"  {key}: {value}")
    
    print("=" * 60)


async def _amain() -> None:
    """Main async entrypoint."""
    parser = build_parser()
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Error: manifest file not found: {manifest_path}")
        raise SystemExit(1)

    try:
        result = run_scene_av(
            scene_manifest_path=str(manifest_path),
            av_route=args.av_route,
        )
    except Exception as exc:
        print(f"Error: {exc}")
        raise SystemExit(1)

    if args.print_result_json:
        print(json.dumps(result, indent=2))
    else:
        _render_result(result)

    # Exit with error code if failed
    if result.get("status") == "failed":
        raise SystemExit(1)


def main() -> None:
    """Main entrypoint."""
    import asyncio
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
