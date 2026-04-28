"""Agent-run CLI entrypoint for live runtime integration."""

import argparse
import asyncio
import json
import uuid
from collections.abc import Callable
from pathlib import Path
from typing import Any

from app.agent.task_selector import TaskSelector, TaskSelectionResult
from app.agent.workflow_agent_service import WorkflowAgentService
from app.assets.organizer import organize_run_artifacts
from app.assets.paths import ASSET_PATHS, ensure_asset_dirs
from app.comfy.comfy_client import ComfyClient
from app.services.openrouter_client import OpenRouterClient
from app.tools import detect_task as detect_task_tool
from app.tools.tool_trace import ToolTrace
from app.workflows.workflow_registry import WorkflowRegistry
from app.workflows.workflow_types import TaskType


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS_DIR = PROJECT_ROOT / "data" / "workflows"
OUTPUTS_DIR = ASSET_PATHS.outputs
PRESETS_PATH = PROJECT_ROOT / "data" / "presets" / "sdxl_presets.json"
TRACES_DIR = ASSET_PATHS.traces


StatusCallback = Callable[[str, dict[str, Any] | None], None]


def print_status(status: str, payload: dict[str, Any] | None = None) -> None:
    """Default status callback for progress tracking."""
    payload = payload or {}
    prompt_id = payload.get("prompt_id", "-")
    
    if status == "QUEUED":
        print(f"QUEUED | prompt_id={prompt_id}")
    elif status == "RUNNING":
        print(f"RUNNING | prompt_id={prompt_id}")
    elif status == "COMPLETED":
        images_found = payload.get("images_found", 0)
        print(f"COMPLETED | prompt_id={prompt_id} | images_found={images_found}")
    elif status == "FAILED":
        stage = payload.get("stage", "unknown")
        error_type = payload.get("error_type", "Error")
        error = payload.get("error", "Unknown error")
        print(f"FAILED | prompt_id={prompt_id} | stage={stage} | {error_type}: {error}")
    elif status == "RETRYING":
        reason = payload.get("reason", "Unknown reason")
        print(f"RETRYING | prompt_id={prompt_id} | reason={reason}")
    else:
        print(f"{status} | prompt_id={prompt_id}")


def print_user_facing_result(result: dict[str, Any]) -> None:
    """Print user-friendly final result."""
    print("\n" + "="*60)
    print("AGENT RUN RESULT")
    print("="*60)
    
    status = result.get("status", "unknown")
    print(f"Status: {status.upper()}")
    
    if status == "failed":
        print(f"Failed Stage: {result.get('failed_stage', 'unknown')}")
        print(f"Error Type: {result.get('error_type', 'unknown')}")
        print(f"Error: {result.get('error', 'No error message')}")
        print(f"\nMetadata: {result.get('metadata_path', 'disabled')}")
        print(f"Summary: {result.get('summary_path', 'disabled')}")
        return
    
    # Success case
    print(f"\nSelected Workflow: {result.get('execution_plan', {}).get('workflow_id', 'unknown')}")
    print(f"Task Type: {result.get('execution_plan', {}).get('task_type', 'unknown')}")
    
    # Check for retry/switch
    corrective_action = result.get("corrective_action")
    if corrective_action:
        print(f"\nCorrective Action: {corrective_action.get('action', 'none')}")
        print(f"Reason: {corrective_action.get('reason', 'no reason')}")
    
    workflow_switch = result.get("workflow_switch")
    if workflow_switch and workflow_switch.get("switch_applied"):
        print(f"\nWorkflow Switch: {workflow_switch.get('from_workflow_id')} -> {workflow_switch.get('to_workflow_id')}")
        print(f"Reason: {workflow_switch.get('switch_reason')}")
    
    executed_action = result.get("executed_action")
    if executed_action:
        print(f"\nExecuted Action: {executed_action.get('executed_action', 'none')}")
        print(f"Branch: {executed_action.get('branch_taken', 'none')}")
    
    verdict = result.get("verdict")
    if verdict:
        print(f"\nVerdict: {verdict}")
    
    images = result.get("images", [])
    if images:
        print(f"\nImages Generated: {len(images)}")
        for i, img in enumerate(images, 1):
            print(f"  {i}. {img.get('filename', 'unknown')}")
    
    print(f"\nMetadata: {result.get('metadata_path', 'disabled')}")
    print(f"Summary: {result.get('summary_path', 'disabled')}")
    print(f"Trace: {result.get('trace_path', 'disabled')}")
    
    # Seam-fix #4: Post-run manual step summary
    print("\n" + "-"*60)
    print("NEXT MANUAL STEPS:")
    mode = result.get('execution_plan', {}).get('task_type', 'unknown').lower()
    if mode == 'edit':
        print("  - Review generated image in output folder")
        print("  - Run additional edit passes if needed")
    elif mode == 'portrait':
        print("  - Review generated portrait")
        print("  - Adjust prompt or recipe for variations")
    elif mode == 'batch':
        print("  - Review batch manifest and job outputs")
        print("  - Compare results across jobs")
    else:
        print("  - Review generated outputs")
    print("-"*60)
    print("="*60 + "\n")


def fail_fast_guard(
    task_selection: TaskSelectionResult,
    assets: dict[str, Any],
) -> None:
    """Fail-fast guard for missing assets.
    
    Args:
        task_selection: Task selection result
        assets: Available assets dictionary
        
    Raises:
        ValueError: If required assets are missing
    """
    missing_inputs = task_selection.missing_inputs or []
    
    if missing_inputs:
        task_type = task_selection.task_type.value
        error_msg = f"FAIL-FAST: Missing required assets for {task_type}: {', '.join(missing_inputs)}"
        raise ValueError(error_msg)


async def run_agent(
    prompt: str,
    mode: str,
    input_image: str | None = None,
    mask_image: str | None = None,
    enable_judging: bool = False,
    enable_retry_loop: bool = False,
    force_retry: bool = False,
    force_switch: str | None = None,
    canonical_recipe: dict[str, Any] | None = None,
    status_callback: StatusCallback | None = None,
    verbose: bool = False,
) -> dict[str, Any]:
    """Run agent with real ComfyUI integration.
    
    Args:
        prompt: User prompt
        mode: Mode (auto, portrait, product, edit, upscale, face-repair)
        input_image: Optional input image path
        mask_image: Optional mask image path
        enable_judging: Whether to enable judging
        enable_retry_loop: Whether to enable retry loop
        force_retry: Force retry path for proof mode (bypasses natural judge trigger)
        force_switch: Force workflow switch for proof mode (e.g., upscale_v1, inpaint_face_v1)
        status_callback: Optional status callback
        
    Returns:
        Final result dictionary
    """
    callback = status_callback or print_status

    # Build assets dictionary
    assets = {}
    if input_image:
        assets["input_image"] = input_image
    if mask_image:
        assets["mask_image"] = mask_image

    # Ensure asset dirs exist (KT-5)
    ensure_asset_dirs()

    # Construct KT-2 tool trace for this run
    run_id = str(uuid.uuid4())[:8]
    tool_trace = ToolTrace(run_id=run_id, trace_dir=TRACES_DIR)

    def _attach_trace(result_dict: dict[str, Any]) -> dict[str, Any]:
        """Finalize trace and attach trace_path + tool_chain to result."""
        tool_trace.finalize()
        result_dict["trace_path"] = str(tool_trace.path)
        result_dict["tool_chain"] = tool_trace.tool_chain
        result_dict["run_id"] = run_id
        return result_dict

    # Initialize LLM client for task selection
    try:
        llm_client = OpenRouterClient()
    except Exception:
        llm_client = None

    task_selector = TaskSelector(llm_client)

    # Step 1: detect_task (tool-wrapped)
    try:
        task_selection = await detect_task_tool.run(
            tool_trace,
            user_prompt=prompt,
            mode=mode,
            assets=assets,
            task_selector=task_selector,
        )
    except Exception as exc:
        callback("FAILED", {
            "stage": "task_detection",
            "error_type": "task_detection_error",
            "error": str(exc),
        })
        return _attach_trace({
            "status": "failed",
            "failed_stage": "task_detection",
            "error_type": "task_detection_error",
            "error": str(exc),
            "user_prompt": prompt,
            "metadata_path": None,
            "summary_path": None,
        })
    
    # Upload assets if provided
    comfy_client = ComfyClient()
    uploaded_assets = {}

    # Seam-fix #5: Auto-detect input image for edit mode if not provided
    if mode == "edit" and not input_image:
        inputs_dir = ASSET_PATHS.inputs
        if inputs_dir.exists():
            # Find latest image in data/inputs/
            image_files = list(inputs_dir.glob("*.png")) + list(inputs_dir.glob("*.jpg")) + list(inputs_dir.glob("*.jpeg"))
            if image_files:
                input_image = str(max(image_files, key=lambda p: p.stat().st_mtime))
                print(f"Auto-detected input image: {input_image}")

    if input_image:
        try:
            upload_result = await comfy_client.upload_image(input_image)
            uploaded_assets["input_image"] = upload_result.get("name", Path(input_image).name)
            callback("QUEUED", {"prompt_id": "-", "info": f"Uploaded input image: {uploaded_assets['input_image']}"})
        except Exception as exc:
            callback("FAILED", {
                "stage": "asset_upload",
                "error_type": "upload_error",
                "error": str(exc),
            })
            return _attach_trace({
                "status": "failed",
                "failed_stage": "asset_upload",
                "error_type": "upload_error",
                "error": str(exc),
                "user_prompt": prompt,
                "metadata_path": None,
                "summary_path": None,
            })
    
    if mask_image:
        try:
            upload_result = await comfy_client.upload_mask(mask_image)
            uploaded_assets["mask_image"] = upload_result.get("name", Path(mask_image).name)
            callback("QUEUED", {"prompt_id": "-", "info": f"Uploaded mask image: {uploaded_assets['mask_image']}"})
        except Exception as exc:
            callback("FAILED", {
                "stage": "asset_upload",
                "error_type": "upload_error",
                "error": str(exc),
            })
            return _attach_trace({
                "status": "failed",
                "failed_stage": "asset_upload",
                "error_type": "upload_error",
                "error": str(exc),
                "user_prompt": prompt,
                "metadata_path": None,
                "summary_path": None,
            })
    
    # Merge uploaded assets with original assets
    resolved_inputs = {**assets, **uploaded_assets}
    
    # Initialize workflow agent service
    workflow_agent = WorkflowAgentService(
        workflows_dir=WORKFLOWS_DIR,
        outputs_dir=OUTPUTS_DIR,
        presets_path=PRESETS_PATH,
        llm_client=llm_client,
        enable_judging=enable_judging,
        verbose=verbose,
    )
    
    # Run workflow agent (tool_trace threaded through)
    try:
        result = await workflow_agent.run(
            user_prompt=prompt,
            task_selection=task_selection,
            assets=resolved_inputs,
            enable_judging=enable_judging,
            enable_retry_loop=enable_retry_loop,
            force_retry=force_retry,
            force_switch=force_switch,
            canonical_recipe=canonical_recipe,
            status_callback=callback,
            tool_trace=tool_trace,
            verbose=verbose,
        )
        result = _attach_trace(result)
        # Seam-fix #1: Ensure metadata_path and summary_path are surfaced for edit mode
        # (matches portrait/batch/video consistency)
        if "metadata_path" not in result or result["metadata_path"] is None:
            result["metadata_path"] = result.get("asset_report", {}).get("metadata_path")
        if "summary_path" not in result or result["summary_path"] is None:
            result["summary_path"] = result.get("asset_report", {}).get("summary_path")
        # KT-5: organize artifacts into data/outputs/runs/{run_id}/
        try:
            asset_report = organize_run_artifacts(
                target_dir=ASSET_PATHS.run_dir(run_id),
                result=result,
            )
            result["asset_report"] = asset_report
        except Exception as exc:
            result["asset_report"] = {"error": str(exc)}
        print(tool_trace.summary_line())
        return result
    except Exception as exc:
        callback("FAILED", {
            "stage": "execution",
            "error_type": "execution_error",
            "error": str(exc),
        })
        return _attach_trace({
            "status": "failed",
            "failed_stage": "execution",
            "error_type": "execution_error",
            "error": str(exc),
            "user_prompt": prompt,
            "metadata_path": None,
            "summary_path": None,
        })


def build_parser() -> argparse.ArgumentParser:
    """Build CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Agent-run CLI for live ComfyUI integration",
    )
    parser.add_argument("--prompt", required=True, help="User prompt for generation")
    parser.add_argument(
        "--mode",
        choices=["auto", "portrait", "product", "edit", "upscale", "face-repair"],
        default="auto",
        help="Generation mode (default: auto)",
    )
    parser.add_argument("--input-image", help="Path to input image for edit/upscale/inpaint")
    parser.add_argument("--mask-image", help="Path to mask image for inpaint")
    parser.add_argument(
        "--enable-judging",
        action="store_true",
        help="Enable judge pipeline for quality assessment",
    )
    parser.add_argument(
        "--enable-retry-loop",
        action="store_true",
        help="Enable automatic retry loop on judge retry",
    )
    parser.add_argument(
        "--force-retry",
        action="store_true",
        help="Force retry path for proof mode (bypasses natural judge trigger)",
    )
    parser.add_argument(
        "--force-switch",
        type=str,
        help="Force workflow switch path for proof mode (e.g., upscale_v1, inpaint_face_v1)",
    )
    parser.add_argument(
        "--canonical-recipe",
        action="store_true",
        help="Use canonical recipe for portrait proof mode (overrides preset defaults)",
    )
    parser.add_argument(
        "--print-result-json",
        action="store_true",
        help="Print final result as JSON",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose live trace mode to show intermediate execution steps",
    )
    return parser


async def main() -> None:
    """Main entry point."""
    import traceback
    parser = build_parser()
    args = parser.parse_args()
    
    # Define canonical recipe if flag is set
    canonical_recipe = None
    if args.canonical_recipe:
        canonical_recipe = {
            "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
            "sampler_name": "euler",
            "scheduler": "karras",
            "steps": 30,
            "cfg": 6.0,
            "width": 1024,
            "height": 1024,
            "seed": 123456789,
            "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, extra fingers, duplicate, distorted features, oversaturated",
            "filename_prefix": "portrait_comparison/test",
        }
    
    try:
        result = await run_agent(
            prompt=args.prompt,
            mode=args.mode,
            input_image=args.input_image,
            mask_image=args.mask_image,
            enable_judging=args.enable_judging,
            enable_retry_loop=args.enable_retry_loop,
            force_retry=args.force_retry,
            force_switch=args.force_switch,
            canonical_recipe=canonical_recipe,
            status_callback=print_status,
            verbose=args.verbose,
        )
    except Exception as e:
        print(f"[DEBUG] Global exception caught: {e}")
        print(f"[DEBUG] Full traceback: {traceback.format_exc()}")
        raise
    
    if args.print_result_json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_user_facing_result(result)
    
    # Exit with error code if failed
    if result.get("status") == "failed":
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
