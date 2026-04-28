"""
MK-6K-DP — Decode-Path Differential Probe v1

Differential probing to isolate blue contamination root cause:
- Probe A: Encode/Decode sanity control (no KSampler)
- Probe B: Single-slot img2img clone
- Probe C: Current bounded batch chain

Classification rules:
- If Probe A is blue: defect in encode/decode chain or VAE/checkpoint pairing
- If Probe A normal, Probe B blue: defect is post-KSampler, not batch-specific
- If Probe B normal, Probe C blue: defect is batch-template-specific
- If Probe B and C both blue, but A normal: defect in img2img latent evolution / sampler-decode interplay
"""
import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.comfy.comfy_client import ComfyClient
from app.tools import fetch_outputs, submit_to_comfy, watch_progress

PROJECT_ROOT = Path(__file__).resolve().parents[0]
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "mk6k_dp_probe"
REFERENCE_IMAGE = PROJECT_ROOT / "test_portrait.png"

# Common recipe settings across all probes
COMMON_RECIPE = {
    "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
    "sampler_name": "dpmpp_2m",
    "scheduler": "karras",
    "steps": 15,
    "cfg": 6.0,
    "seed": 123456789,
    "denoise": 0.6,
    "prompt": "realistic female portrait, natural skin texture, detailed eyes, soft natural light, high detail, professional photography",
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting",
}

# Blue contamination threshold
BLUE_DOMINANCE_THRESHOLD = 0.30  # If blue channel > 30% of total, considered blue-contaminated


def analyze_image_channels(image_path: Path) -> dict[str, Any]:
    """Analyze image channel statistics for blue contamination detection."""
    img = Image.open(image_path)
    img_array = np.array(img)
    
    if len(img_array.shape) == 2:  # Grayscale
        return {
            "mean_brightness": float(np.mean(img_array)),
            "std": float(np.std(img_array)),
            "red_dominance_ratio": 0.33,
            "green_dominance_ratio": 0.33,
            "blue_dominance_ratio": 0.33,
            "is_blue_contaminated": False,
        }
    
    # RGB image
    r, g, b = img_array[:, :, 0], img_array[:, :, 1], img_array[:, :, 2]
    
    mean_brightness = float(np.mean(img_array))
    std = float(np.std(img_array))
    
    total = r.sum() + g.sum() + b.sum()
    red_ratio = float(r.sum() / total) if total > 0 else 0.33
    green_ratio = float(g.sum() / total) if total > 0 else 0.33
    blue_ratio = float(b.sum() / total) if total > 0 else 0.33
    
    is_blue_contaminated = blue_ratio > BLUE_DOMINANCE_THRESHOLD
    
    return {
        "mean_brightness": mean_brightness,
        "std": std,
        "red_dominance_ratio": red_ratio,
        "green_dominance_ratio": green_ratio,
        "blue_dominance_ratio": blue_ratio,
        "is_blue_contaminated": is_blue_contaminated,
    }


async def run_probe(
    client: ComfyClient,
    workflow_path: Path,
    probe_name: str,
) -> dict[str, Any]:
    """Run a single probe and collect diagnostics."""
    print(f"\n=== Running {probe_name} ===")
    
    template = await client.load_workflow(workflow_path)
    
    # Extract settings for diagnostics
    checkpoint_node = template.get("4", {}).get("inputs", {})
    sampler_node = template.get("3", {}).get("inputs", {})
    
    checkpoint = checkpoint_node.get("ckpt_name", "unknown")
    sampler_name = sampler_node.get("sampler_name", "unknown")
    scheduler = sampler_node.get("scheduler", "unknown")
    steps = sampler_node.get("steps", 0)
    cfg = sampler_node.get("cfg", 0.0)
    denoise = sampler_node.get("denoise", 0.0)
    
    prompt_id = await submit_to_comfy.run(None, client=client, workflow=template)
    print(f"  Prompt ID: {prompt_id}")
    
    history_item = await watch_progress.run(None, client=client, prompt_id=prompt_id)
    images = await fetch_outputs.run(None, client=client, history_item=history_item)
    
    if not images:
        raise RuntimeError(f"No images generated for {probe_name}")
    
    # Analyze first output image
    image_info = images[0]
    print(f"  Image info: {image_info}")
    
    # ComfyUI output directory (from test_vision_defect_proof.py)
    comfyui_output = Path("f:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/output")
    
    # The filename might include subfolder path
    filename = image_info["filename"]
    subfolder = image_info.get("subfolder", "")
    
    if subfolder:
        image_path = comfyui_output / subfolder / filename
    else:
        image_path = comfyui_output / filename
    
    print(f"  Looking for image at: {image_path}")
    print(f"  Image exists: {image_path.exists()}")
    
    if image_path.exists():
        channel_stats = analyze_image_channels(image_path)
    else:
        print(f"  WARNING: Image not found, using fallback values")
        channel_stats = {
            "mean_brightness": 0,
            "std": 0,
            "red_dominance_ratio": 0.33,
            "green_dominance_ratio": 0.33,
            "blue_dominance_ratio": 0.33,
            "is_blue_contaminated": False,
        }
    
    # Determine validity verdict
    is_valid = not channel_stats["is_blue_contaminated"]
    
    result = {
        "probe_name": probe_name,
        "prompt_id": prompt_id,
        "checkpoint": checkpoint,
        "sampler_name": sampler_name,
        "scheduler": scheduler,
        "steps": steps,
        "cfg": cfg,
        "denoise": denoise,
        "output_filename": image_info["filename"],
        "mean_brightness": channel_stats["mean_brightness"],
        "std": channel_stats["std"],
        "red_dominance_ratio": channel_stats["red_dominance_ratio"],
        "green_dominance_ratio": channel_stats["green_dominance_ratio"],
        "blue_dominance_ratio": channel_stats["blue_dominance_ratio"],
        "is_blue_contaminated": channel_stats["is_blue_contaminated"],
        "validity_verdict": "valid" if is_valid else "invalid_blue",
    }
    
    print(f"  Output: {image_info['filename']}")
    print(f"  Blue ratio: {channel_stats['blue_dominance_ratio']:.3f}")
    print(f"  Verdict: {result['validity_verdict']}")
    
    return result


def classify_defect(probe_a: dict, probe_b: dict, probe_c: dict, batch_blue: bool) -> dict[str, Any]:
    """Apply differential classification rules."""
    a_blue = probe_a["is_blue_contaminated"]
    b_blue = probe_b["is_blue_contaminated"]
    c_blue = probe_c["is_blue_contaminated"]
    
    if a_blue:
        defect_class = "encode_decode_chain_defect"
        reasoning = "Probe A (encode/decode only) is already blue. Defect is in VAE encode/decode chain or checkpoint/VAE pairing, not batch-specific."
    elif not a_blue and b_blue:
        defect_class = "post_ksampler_latent_defect"
        reasoning = "Probe A normal, Probe B blue. Defect is post-KSampler latent pathology, not batch-specific."
    elif not a_blue and not b_blue and c_blue:
        defect_class = "batch_template_specific_defect"
        reasoning = "Probe A and B normal, Probe C blue. Defect is batch-template-specific, not in core encode/decode or sampler."
    elif not a_blue and b_blue and c_blue:
        defect_class = "img2img_latent_evolution_defect"
        reasoning = "Probe A normal, but Probe B and C both blue. Defect is in img2img latent evolution / sampler-decode interplay, not raw wiring."
    elif not a_blue and not b_blue and not c_blue and batch_blue:
        defect_class = "batch_execution_context_defect"
        reasoning = "All probes normal, but actual batch output shows blue contamination. Defect is specific to batch execution context (orchestrator, environment, or state), not core pipeline."
    else:
        defect_class = "no_defect_detected"
        reasoning = "All probes normal and batch output normal. No blue contamination detected in any path."
    
    return {
        "defect_class": defect_class,
        "reasoning": reasoning,
        "probe_a_blue": a_blue,
        "probe_b_blue": b_blue,
        "probe_c_blue": c_blue,
        "batch_blue": batch_blue,
    }


async def main():
    print("=== MK-6K-DP — Decode-Path Differential Probe v1 ===")
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Verify reference image exists
    if not REFERENCE_IMAGE.exists():
        print(f"ERROR: Reference image not found at {REFERENCE_IMAGE}")
        print("Please ensure test_portrait.png exists in the project root.")
        return
    
    print(f"Reference image: {REFERENCE_IMAGE}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    print("Common recipe settings:")
    for key, value in COMMON_RECIPE.items():
        print(f"  {key}: {value}")
    print()
    
    client = ComfyClient()
    
    # Analyze actual batch outputs for comparison
    print("\n=== Analyzing Actual Batch Outputs ===")
    batch_output_path = PROJECT_ROOT / "data" / "batches" / "kt5_proof_001" / "job_001" / "images" / "sdxl_agent_00011_.png"
    if batch_output_path.exists():
        batch_stats = analyze_image_channels(batch_output_path)
        print(f"  Batch output: {batch_output_path}")
        print(f"  Blue ratio: {batch_stats['blue_dominance_ratio']:.3f}")
        print(f"  Blue contaminated: {batch_stats['is_blue_contaminated']}")
    else:
        print(f"  Batch output not found at: {batch_output_path}")
        batch_stats = None
    print()
    
    # Run probes
    probe_a_path = PROJECT_ROOT / "mk6k_dp_probe_a_workflow.json"
    probe_b_path = PROJECT_ROOT / "mk6k_dp_probe_b_workflow.json"
    probe_c_path = PROJECT_ROOT / "mk6k_dp_probe_c_workflow.json"
    
    try:
        probe_a_result = await run_probe(client, probe_a_path, "Probe_A_Encode_Decode")
        probe_b_result = await run_probe(client, probe_b_path, "Probe_B_Single_Slot_Img2Img")
        probe_c_result = await run_probe(client, probe_c_path, "Probe_C_Batch_Chain")
        
        # Differential comparison
        print("\n=== Differential Comparison ===")
        comparison = {
            "probe_a": probe_a_result,
            "probe_b": probe_b_result,
            "probe_c": probe_c_result,
        }
        
        # Classification
        batch_blue = batch_stats["is_blue_contaminated"] if batch_stats else False
        classification = classify_defect(probe_a_result, probe_b_result, probe_c_result, batch_blue)
        
        print(f"\nDefect Class: {classification['defect_class']}")
        print(f"Reasoning: {classification['reasoning']}")
        print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = OUTPUT_DIR / f"mk6k_dp_results_{timestamp}.json"
        
        results = {
            "probe_id": "MK-6K-DP",
            "probe_version": "v1",
            "timestamp": datetime.now().isoformat(),
            "common_recipe": COMMON_RECIPE,
            "batch_output_analysis": batch_stats,
            "probe_a": probe_a_result,
            "probe_b": probe_b_result,
            "probe_c": probe_c_result,
            "differential_comparison": comparison,
            "root_cause_classification": classification,
            "final_decision": classification["defect_class"],
        }
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {results_path}")
        print()
        
        # Final verdict
        is_pass = classification["defect_class"] != "no_defect_detected" and classification["defect_class"] != "unknown"
        
        print("=== FINAL VERDICT ===")
        print(f"MK-6K-DP: {'PASS' if is_pass else 'FAIL'}")
        print(f"Defect Class: {classification['defect_class']}")
        print()
        
        # Print fragments
        print("=== Probe A Fragment ===")
        print(f"  Workflow: LoadImage -> VAEEncode -> VAEDecode -> SaveImage")
        print(f"  Blue contaminated: {probe_a_result['is_blue_contaminated']}")
        print(f"  Blue ratio: {probe_a_result['blue_dominance_ratio']:.3f}")
        print()
        
        print("=== Probe B Fragment ===")
        print(f"  Workflow: LoadImage -> VAEEncode -> KSampler -> VAEDecode -> SaveImage")
        print(f"  Blue contaminated: {probe_b_result['is_blue_contaminated']}")
        print(f"  Blue ratio: {probe_b_result['blue_dominance_ratio']:.3f}")
        print()
        
        print("=== Probe C Fragment ===")
        print(f"  Workflow: EmptyLatentImage -> KSampler -> VAEDecode -> SaveImage (batch chain)")
        print(f"  Blue contaminated: {probe_c_result['is_blue_contaminated']}")
        print(f"  Blue ratio: {probe_c_result['blue_dominance_ratio']:.3f}")
        print()
        
        print("=== Differential Comparison Fragment ===")
        print(f"  Probe A blue: {classification['probe_a_blue']}")
        print(f"  Probe B blue: {classification['probe_b_blue']}")
        print(f"  Probe C blue: {classification['probe_c_blue']}")
        print()
        
        print("=== Root Cause Classification Fragment ===")
        print(f"  Class: {classification['defect_class']}")
        print(f"  Reasoning: {classification['reasoning']}")
        print()
        
        print("=== Final Decision Fragment ===")
        print(f"  MK-6K-DP: {'PASS' if is_pass else 'FAIL'}")
        print(f"  Defect isolated to: {classification['defect_class']}")
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
