#!/usr/bin/env python3
"""Execute one real V8 quality-locked generation via ComfyUI API.
Task: RC-COMBINE-V2-7601-8600
"""
import asyncio
import json
import hashlib
import os
import random
import sys
import time
from pathlib import Path
from datetime import datetime, timezone

import httpx

BASE_URL = "http://127.0.0.1:8188"
ASSETS_DIR = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01\output\assets")
CONTROL_DIR = Path(r"F:\ComfyUI\comfy-agent-mvp\data\rc2_multishot1_ep01\output\control")
COMFY_OUTPUT_DIR = Path(r"F:\ComfyUI\ComfyUI\output")

PROJECT_ROOT = Path(r"F:\ComfyUI\comfy-agent-mvp")
os.chdir(PROJECT_ROOT)  # noqa

# Quality-locked V8 workflow parameters
CHECKPOINT = "realvisxlV50_v50Bakedvae.safetensors"
SAMPLER = "dpmpp_2m"
SCHEDULER = "karras"
STEPS = 30
CFG = 6.5
WIDTH = 1024
HEIGHT = 1024
SEED = random.randint(1, 2**31 - 1)

FILENAME_PREFIX = "combine_v2_v8_quality_locked_shot02"

POSITIVE_PROMPT = (
    "masterpiece, best quality, "
    "young adult female fantasy character, ethereal cinematic portrait, "
    "beautiful young woman with flowing white hair, "
    "elegant white fantasy dress, "
    "blue atmospheric magical background with soft bokeh, "
    # Quality guardrails QR_V8_001-009
    "sharp focus, highly detailed, crisp, "
    "sharp facial features, clear definition, high detail face, "
    "realistic eyes, detailed iris, clean eye shape, natural eye appearance, "
    "detailed eyelashes, natural eyelashes, clean eyelash detail, "
    "natural mouth, well-formed teeth, natural smile, "
    "natural skin texture, visible skin pores, realistic skin detail, "
    "natural skin reflectance, detailed hair strands, "
    "individual hair strands, sharp hair detail, "
    "cinematic lighting with soft falloff, "
    "intricate fantasy details, high fantasy art style, "
    "attractive fantasy character identity, close portrait framing, "
    "soft clean lighting, intricate hair detail"
)

NEGATIVE_PROMPT = (
    "old, elderly, aged face, wrinkles, aged skin, senior, grandmother, "
    "realistic photo, studio portrait, passport photo, documentary, "
    "modern clothing, casual wear, plain background, "
    # Quality guardrail negatives QR_V8_001-009
    "blurry, soft focus, out of focus, "
    "soft face, blurry face, undefined features, "
    "deformed eyes, bad eyes, unrealistic eyes, distorted eyes, "
    "clumpy eyelashes, missing eyelashes, bad eyelashes, "
    "deformed mouth, bad teeth, missing teeth, open mouth distortion, "
    "smooth skin, plastic skin, wax skin, airbrushed skin, unreal skin, "
    "wax skin, plastic face, synthetic skin, doll-like skin, mannequin skin, "
    "soft hair, blurry hair, hair blob, undefined hair, "
    "glossy plastic skin, over-smoothed face, "
    "changing character concept, loss of fantasy styling, "
    "loss of blue fantasy environment, replacing fantasy with realism, "
    "ugly, deformed, bad anatomy, disfigured, poorly drawn face, "
    "extra limbs, cloned face, disgusting, low quality, worst quality, "
    "monochrome, grayscale, boring, mundane"
)


def build_workflow() -> dict:
    """Build the ComfyUI API-format workflow."""
    return {
        "4": {
            "inputs": {"ckpt_name": CHECKPOINT},
            "class_type": "CheckpointLoaderSimple",
        },
        "5": {
            "inputs": {
                "width": WIDTH,
                "height": HEIGHT,
                "batch_size": 1,
            },
            "class_type": "EmptyLatentImage",
        },
        "6": {
            "inputs": {
                "text": POSITIVE_PROMPT,
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "7": {
            "inputs": {
                "text": NEGATIVE_PROMPT,
                "clip": ["4", 1],
            },
            "class_type": "CLIPTextEncode",
        },
        "3": {
            "inputs": {
                "seed": SEED,
                "steps": STEPS,
                "cfg": CFG,
                "sampler_name": SAMPLER,
                "scheduler": SCHEDULER,
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0],
            },
            "class_type": "KSampler",
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            },
            "class_type": "VAEDecode",
        },
        "9": {
            "inputs": {
                "filename_prefix": FILENAME_PREFIX,
                "images": ["8", 0],
            },
            "class_type": "SaveImage",
        },
    }


def get_submitted_workflow() -> dict:
    """Build the submitted workflow record (same as workflow but wrapped in metadata)."""
    return {
        "task_id": "RC-COMBINE-V2-7601-8600",
        "workflow_type": "v8_quality_locked_generation",
        "saveimage_filename_prefix": FILENAME_PREFIX,
        "positive_prompt": POSITIVE_PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "refinement_parameters": {
            "cfg_scale": CFG,
            "steps": STEPS,
            "sampler": SAMPLER,
            "scheduler": SCHEDULER,
            "resolution": f"{WIDTH}x{HEIGHT}",
            "checkpoint": CHECKPOINT,
            "seed": SEED,
        },
        "quality_guardrails_applied": [
            "QR_V8_001:anti_blur",
            "QR_V8_002:anti_softness",
            "QR_V8_003:realistic_eyes",
            "QR_V8_004:clean_eyelashes",
            "QR_V8_005:stable_mouth_teeth",
            "QR_V8_006:visible_skin_micro_detail",
            "QR_V8_007:no_wax_plastic_skin",
            "QR_V8_008:hair_strand_detail",
            "QR_V8_009:sharper_facial_features",
        ],
        "workflow_payload": build_workflow(),
    }


def compute_sha256(filepath: Path) -> str:
    return hashlib.sha256(filepath.read_bytes()).hexdigest()


def get_image_dimensions(filepath: Path) -> dict:
    """Get image dimensions using PIL."""
    from PIL import Image
    with Image.open(filepath) as img:
        w, h = img.size
    return {"width": w, "height": h}


async def check_server() -> bool:
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(f"{BASE_URL}/")
            r.raise_for_status()
            return True
    except Exception:
        return False


async def submit_prompt(workflow: dict) -> str:
    url = f"{BASE_URL}/prompt"
    payload = {"prompt": workflow}
    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(url, json=payload)
        r.raise_for_status()
        data = r.json()
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"No prompt_id in response: {data}")
    return prompt_id


async def wait_for_history(prompt_id: str, max_attempts: int = 120, delay: int = 3) -> dict:
    for attempt in range(1, max_attempts + 1):
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.get(f"{BASE_URL}/history/{prompt_id}")
            r.raise_for_status()
            history = r.json()
        if prompt_id in history:
            item = history[prompt_id]
            status = item.get("status", {})
            status_str = status.get("status_str")
            # Check for error
            messages = status.get("messages", [])
            for msg in messages:
                if not isinstance(msg, list) or len(msg) != 2:
                    continue
                event, payload = msg
                if event in ("execution_error", "execution_interrupted"):
                    err_msg = payload.get("exception_message", str(payload))
                    raise RuntimeError(f"ComfyUI execution error: {err_msg}")
            if status_str == "success" or status.get("completed"):
                return item
            if status_str == "error":
                raise RuntimeError(f"ComfyUI execution failed with status: {status}")
        if attempt % 10 == 0:
            print(f"  Waiting for generation... attempt {attempt}/{max_attempts}")
        await asyncio.sleep(delay)
    raise TimeoutError(f"Generation timed out after {max_attempts * delay}s for prompt_id={prompt_id}")


def find_output_image(history_item: dict) -> dict | None:
    """Find the generated image in the history output."""
    outputs = history_item.get("outputs", {})
    for node_id, node_output in outputs.items():
        images = node_output.get("images", [])
        for img in images:
            if img.get("type") == "output":
                return img
        for img in images:
            return img
    return None


def locate_comfyui_output(img_info: dict) -> Path | None:
    """Locate the actual image file in ComfyUI output directory."""
    subfolder = img_info.get("subfolder", "")
    filename = img_info.get("filename", "")
    if subfolder:
        path = COMFY_OUTPUT_DIR / subfolder / filename
    else:
        path = COMFY_OUTPUT_DIR / filename
    if path.exists():
        return path
    # Try agent subfolder
    agent_path = COMFY_OUTPUT_DIR / "agent" / filename
    if agent_path.exists():
        return agent_path
    return None


async def main():
    print("=" * 60)
    print("V8 REAL GENERATION — RC-COMBINE-V2-7601-8600")
    print("=" * 60)

    # Step 1: Check server
    print("\n[1/6] Checking ComfyUI server...")
    server_ok = await check_server()
    if not server_ok:
        print("FAILED: ComfyUI server is not available at", BASE_URL)
        return 1
    print("OK: ComfyUI server is available")

    # Step 2: Build and submit workflow
    print("\n[2/6] Building V8 quality-locked workflow...")
    workflow = build_workflow()
    print(f"  Checkpoint: {CHECKPOINT}")
    print(f"  Sampler: {SAMPLER}/{SCHEDULER}, Steps: {STEPS}, CFG: {CFG}")
    print(f"  Resolution: {WIDTH}x{HEIGHT}, Seed: {SEED}")
    print(f"  Prefix: {FILENAME_PREFIX}")

    print("\n[3/6] Submitting to ComfyUI...")
    prompt_id = await submit_prompt(workflow)
    print(f"  prompt_id: {prompt_id}")

    # Step 4: Wait for completion
    print("\n[4/6] Waiting for generation to complete...")
    try:
        history_item = await wait_for_history(prompt_id)
        print(f"  Generation completed successfully")
    except (TimeoutError, RuntimeError) as e:
        print(f"FAILED: {e}")
        return 1

    # Step 5: Find and validate output image
    print("\n[5/6] Locating generated output...")
    img_info = find_output_image(history_item)
    if not img_info:
        print("FAILED: No output image found in history")
        print(f"  History keys: {list(history_item.get('outputs', {}).keys())}")
        return 1

    print(f"  Output image info: {json.dumps(img_info, indent=2)}")
    comfy_path = locate_comfyui_output(img_info)
    if not comfy_path:
        print(f"FAILED: Could not locate output file on filesystem")
        print(f"  Searched in: {COMFY_OUTPUT_DIR}")
        return 1

    print(f"  Found at: {comfy_path}")
    file_size = comfy_path.stat().st_size
    sha256 = compute_sha256(comfy_path)
    dims = get_image_dimensions(comfy_path)
    print(f"  Size: {file_size} bytes")
    print(f"  SHA256: {sha256}")
    print(f"  Dimensions: {dims['width']}x{dims['height']}")

    # Validate asset
    if file_size <= 1024:
        print("FAILED: Asset is too small (<= 1024 bytes) — likely a stub")
        return 1
    if dims["width"] < 64 or dims["height"] < 64:
        print("FAILED: Asset dimensions too small — likely invalid")
        return 1
    print("  Asset validation: PASSED")

    # Step 6: Copy to project assets directory
    print("\n[6/6] Registering canonical output...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    asset_filename = f"{FILENAME_PREFIX}_{SEED}_{prompt_id[:8]}.png"
    asset_path = ASSETS_DIR / asset_filename
    import shutil
    shutil.copy2(comfy_path, asset_path)
    print(f"  Copied to: {asset_path.relative_to(PROJECT_ROOT)}")

    # Save submitted workflow record
    submitted_workflow = get_submitted_workflow()
    submitted_workflow["prompt_id"] = prompt_id
    submitted_workflow["timestamp"] = datetime.now(timezone.utc).isoformat()
    submitted_path = CONTROL_DIR / "combine_v2_v8_quality_locked_submitted_workflow.json"
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    submitted_path.write_text(json.dumps(submitted_workflow, indent=2, ensure_ascii=False))
    print(f"  Submitted workflow saved: {submitted_path.relative_to(PROJECT_ROOT)}")

    # Save result
    result = {
        "task_id": "RC-COMBINE-V2-7601-8600",
        "stage": "v8_real_generation",
        "workflow_submitted": True,
        "comfyui_execution": True,
        "prompt_id": prompt_id,
        "comfyui_status": "success",
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "dry_run_used": False,
        "canonical_outputs_registered": True,
        "generated_assets": [asset_filename],
        "asset_readable": True,
        "sha256_present": True,
        "dimensions_present": True,
        "size_bytes_gt_1024": file_size > 1024,
        "stub_asset_detected": False,
        "failure_code": None,
        "error_message": None,
        "visual_qa_executed": False,
        "operator_visual_decision_created": False,
        "assembly_executed": False,
        "downstream_executed": False,
        "production_accepted": False,
        "current_state": "v8_operator_visual_review_required",
        "next_allowed_action": "v8_operator_visual_review_required",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    result_path = CONTROL_DIR / "combine_v2_v8_real_generation_result.json"
    result_path.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"  Result saved: {result_path.relative_to(PROJECT_ROOT)}")

    # Save outputs manifest
    manifest = {
        "stage": "v8_real_generation",
        "manifest_type": "v8_real_generation_outputs_manifest",
        "task_id": "RC-COMBINE-V2-7601-8600",
        "generation_count": 1,
        "max_generations": 1,
        "second_generation_attempted": False,
        "retry_attempted": False,
        "workflow_submitted": True,
        "generated_assets": [asset_filename],
        "asset_paths": [str(asset_path.relative_to(PROJECT_ROOT))],
        "collection_status": "success",
        "asset_readable": True,
        "sha256_present": True,
        "sha256": sha256,
        "dimensions": dims,
        "size_bytes": file_size,
        "stub_asset_detected": False,
        "visual_qa_executed": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "production_accepted": False,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    manifest_path = CONTROL_DIR / "combine_v2_v8_real_generation_outputs_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    print(f"  Manifest saved: {manifest_path.relative_to(PROJECT_ROOT)}")

    # Create operator visual review packet
    review_packet = {
        "task_id": "RC-COMBINE-V2-7601-8600",
        "stage": "v8_quality_locked_generation",
        "generation_attempted": True,
        "generation_success": True,
        "v8_quality_locked_package_used": "combine_v2_v8_quality_locked_refinement_package.json",
        "v8_quality_guardrails_used": "combine_v2_v8_quality_guardrails.json",
        "v8_generation_gate_used": "combine_v2_v8_quality_locked_generation_gate.json",
        "prompt_id": prompt_id,
        "generation_count": 1,
        "max_generations": 1,
        "generated_assets": [asset_filename],
        "asset_path": str(asset_path.relative_to(PROJECT_ROOT)),
        "comfyui_execution": True,
        "submitted_workflow_ref": "combine_v2_v8_quality_locked_submitted_workflow.json",
        "outputs_manifest_ref": "combine_v2_v8_real_generation_outputs_manifest.json",
        "generation_result_ref": "combine_v2_v8_real_generation_result.json",
        "positive_prompt": POSITIVE_PROMPT,
        "negative_prompt": NEGATIVE_PROMPT,
        "refinement_parameters": {
            "cfg_scale": CFG,
            "steps": STEPS,
            "sampler": SAMPLER,
            "scheduler": SCHEDULER,
            "resolution": f"{WIDTH}x{HEIGHT}",
            "checkpoint": CHECKPOINT,
            "seed": SEED,
        },
        "asset_sha256": sha256,
        "asset_dimensions": dims,
        "asset_size_bytes": file_size,
        "visual_qa_executed": False,
        "visual_qa_verdict": None,
        "visual_qa_report_ref": None,
        "operator_visual_decision_created": False,
        "operator_visual_verdict": None,
        "operator_visual_decision_ref": None,
        "production_accepted": False,
        "assembly_allowed": False,
        "downstream_allowed": False,
        "notes": (
            "V8 quality-locked generation completed successfully. "
            "Asset requires operator visual review before any further pipeline progression. "
            "No visual QA executed — this packet is for manual operator review."
        ),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    review_packet_path = CONTROL_DIR / "combine_v2_v8_quality_locked_operator_visual_review_packet.json"
    review_packet_path.write_text(json.dumps(review_packet, indent=2, ensure_ascii=False))
    print(f"  Operator visual review packet saved: {review_packet_path.relative_to(PROJECT_ROOT)}")

    print("\n" + "=" * 60)
    print("V8 GENERATION COMPLETE")
    print(f"  Asset: {asset_filename}")
    print(f"  prompt_id: {prompt_id}")
    print(f"  Seed: {SEED}")
    print(f"  Current state: v8_operator_visual_review_required")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
