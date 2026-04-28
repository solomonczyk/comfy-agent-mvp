import argparse
import asyncio
import json
from pathlib import Path
from typing import Any

from app.services.generation_service import GenerationService

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOW_PATH = PROJECT_ROOT / "data" / "workflows" / "sdxl_txt2img_template.json"
OUTPUTS_DIR = PROJECT_ROOT / "data" / "outputs"
PRESETS_PATH = PROJECT_ROOT / "data" / "presets" / "sdxl_presets.json"


def print_terminal_report(report: dict[str, Any]) -> None:
    if report["status"] == "failed":
        print("AGENT RUN FAILED")
        print("prompt_id:", report["prompt_id"])
        print("failed_stage:", report["failed_stage"])
        print("error_type:", report["error_type"])
        print("error:", report["error"])
        print("metadata_saved_to:", report["metadata_path"])
        print("summary_saved_to:", report["summary_path"])
        return
    print("AGENT RUN OK")
    print("prompt_id:", report["prompt_id"])
    print("seed:", report["seed"])
    print("preset_name:", report["preset_name"])
    print("rewrite_mode:", report["rewrite_mode"])
    print("final_positive_prompt:", report["final_positive_prompt"])
    print("images_found:", len(report["images"]))
    for image in report["images"]:
        print(image)
    print("metadata_saved_to:", report["metadata_path"])
    print("summary_saved_to:", report["summary_path"])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="SDXL personal tool for ComfyUI")
    parser.add_argument("--prompt", help="User prompt")
    parser.add_argument("--preset", default="portrait", help="Preset name")
    parser.add_argument("--negative", default=None, help="Override negative prompt")
    parser.add_argument("--width", type=int, default=None)
    parser.add_argument("--height", type=int, default=None)
    parser.add_argument("--steps", type=int, default=None)
    parser.add_argument("--cfg", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--checkpoint", default=None)
    parser.add_argument("--prefix", default=None)
    parser.add_argument(
        "--list-presets",
        action="store_true",
        help="Print available presets and exit",
    )
    parser.add_argument(
        "--show-final-settings",
        action="store_true",
        help="Print resolved settings after preset + overrides merge",
    )
    parser.add_argument(
        "--no-save-metadata",
        action="store_true",
        help="Skip saving metadata JSON and run summary (for quick test runs)",
    )
    parser.add_argument(
        "--print-report-json",
        action="store_true",
        help="Print final unified report as JSON to stdout",
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--raw-prompt",
        action="store_true",
        help="Use prompt as-is",
    )
    mode_group.add_argument(
        "--rewrite-prompt",
        action="store_true",
        help="Rewrite prompt via OpenRouter",
    )
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    service = GenerationService(
        workflow_path=WORKFLOW_PATH,
        outputs_dir=OUTPUTS_DIR,
        presets_path=PRESETS_PATH,
    )
    if args.list_presets:
        print("AVAILABLE PRESETS")
        print(json.dumps(service.list_presets(), indent=2, ensure_ascii=False))
        return
    if not args.prompt or not args.prompt.strip():
        parser.error("--prompt is required unless --list-presets is used.")
    if args.raw_prompt:
        rewrite_mode = "raw"
    elif args.rewrite_prompt:
        rewrite_mode = "llm"
    else:
        rewrite_mode = "fallback"
    if args.show_final_settings:
        resolved_settings = service.resolve_generation_settings(
            preset_name=args.preset,
            negative_prompt=args.negative,
            width=args.width,
            height=args.height,
            steps=args.steps,
            cfg=args.cfg,
            seed=args.seed,
            checkpoint=args.checkpoint,
            prefix=args.prefix,
        )
        print("FINAL SETTINGS")
        print(json.dumps(resolved_settings, indent=2, ensure_ascii=False))
    report = await service.generate_from_text(
        user_prompt=args.prompt,
        rewrite_mode=rewrite_mode,
        preset_name=args.preset,
        negative_prompt=args.negative,
        width=args.width,
        height=args.height,
        steps=args.steps,
        cfg=args.cfg,
        seed=args.seed,
        checkpoint=args.checkpoint,
        prefix=args.prefix,
        save_metadata=not args.no_save_metadata,
    )
    if args.print_report_json:
        print(json.dumps(report, indent=2, ensure_ascii=False))
    else:
        print_terminal_report(report)
    if report["status"] == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())