"""
CLI entrypoint for MK-4 Scene Audio / Voiceover Integration.

Usage:
    python -m app.scene_audio_run --manifest data/manifests/video_scene_20260419_155010_4ad579f0.json
"""

import argparse
import json
import sys
from pathlib import Path

from app.scene.scene_audio_agent import run_scene_audio


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="MK-4 Scene Audio / Voiceover Integration - Generate voiceover audio for scene videos"
    )
    parser.add_argument(
        "--manifest",
        type=str,
        required=True,
        help="Path to scene manifest JSON file",
    )
    parser.add_argument(
        "--voiceover-text",
        type=str,
        default=None,
        help="Custom voiceover text (auto-generated if not provided)",
    )
    parser.add_argument(
        "--tts-tool",
        type=str,
        default="edge-tts",
        choices=["pyttsx3", "edge-tts"],
        help="TTS tool to use (default: edge-tts)",
    )
    parser.add_argument(
        "--audio-format",
        type=str,
        default="wav",
        choices=["wav", "mp3"],
        help="Audio output format (default: wav)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print the final result as JSON",
    )
    return parser


def _render_result(result: dict) -> None:
    """Render scene audio generation result to console."""
    print("\n" + "=" * 60)
    print("MK-4 SCENE AUDIO GENERATION RESULT")
    print("=" * 60)
    print(f"status:           {result.get('status', '').upper()}")
    print(f"scene_id:         {result.get('scene_id')}")
    print(f"video_path:       {result.get('video_path')}")
    print(f"voiceover_text:   {result.get('voiceover_text')}")
    print(f"tts_tool:         {result.get('tts_tool')}")
    print(f"audio_path:       {result.get('audio_path')}")
    print(f"audio_format:     {result.get('audio_format')}")
    print(f"manifest_path:    {result.get('manifest_path')}")
    
    if result.get("error"):
        print(f"error:            {result.get('error')}")
    
    if result.get("scene_linkage"):
        print("\nScene Linkage:")
        for key, value in result.get("scene_linkage", {}).items():
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
        result = await run_scene_audio(
            scene_manifest_path=str(manifest_path),
            voiceover_text=args.voiceover_text,
            tts_tool=args.tts_tool,
            audio_format=args.audio_format,
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
