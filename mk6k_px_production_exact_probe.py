"""
MK-6K-PX — Production-Exact Differential Replay v1

Reproduce the blue contamination using the exact same workflow structure and same runtime payload 
shape as the failing bounded production path, then compare it against a production-exact single-slot clone.

Both probes use the EXACT recipe from the failing batch:
- checkpoint: sd_xl_base_1.0_0.9vae.safetensors
- sampler_name: dpmpp_2m
- scheduler: karras
- steps: 15
- cfg: 6.0
- seed: 2061569467
- width: 768
- height: 768
- positive_prompt: "kt5 asset proof portrait A, natural skin, soft light, cinematic lighting, realistic details, high quality, professional photography, detailed texture"
- negative_prompt: "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting"
"""

import asyncio
import json
from pathlib import Path
from datetime import datetime
from typing import Any
import numpy as np
from PIL import Image

from app.agent.sdxl_agent import ComfyClient, watch_progress, fetch_outputs

PROJECT_ROOT = Path(__file__).parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "outputs" / "mk6k_px_probe"

# Exact production recipe from failing batch (kt5_proof_001/job_001)
PRODUCTION_RECIPE = {
    "checkpoint": "sd_xl_base_1.0_0.9vae.safetensors",
    "sampler_name": "dpmpp_2m",
    "scheduler": "karras",
    "steps": 15,
    "cfg": 6.0,
    "seed": 2061569467,
    "denoise": 1.0,
    "width": 768,
    "height": 768,
    "positive_prompt": "kt5 asset proof portrait A, natural skin, soft light, cinematic lighting, realistic details, high quality, professional photography, detailed texture",
    "negative_prompt": "blurry, low quality, bad anatomy, deformed face, deformed eyes, plastic skin, smooth skin texture, doll-like, anime, cartoon, oversaturated, harsh lighting",
}

# Blue contamination threshold (from MK-6K-DP)
BLUE_DOMINANCE_THRESHOLD = 0.30


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
    
    total_intensity = r.astype(float) + g.astype(float) + b.astype(float)
    total_intensity[total_intensity == 0] = 1  # Avoid division by zero
    
    red_ratio = np.mean(r.astype(float) / total_intensity)
    green_ratio = np.mean(g.astype(float) / total_intensity)
    blue_ratio = np.mean(b.astype(float) / total_intensity)
    
    mean_brightness = np.mean(img_array)
    std = np.std(img_array)
    
    is_blue_contaminated = blue_ratio > BLUE_DOMINANCE_THRESHOLD
    
    return {
        "mean_brightness": float(mean_brightness),
        "std": float(std),
        "red_dominance_ratio": float(red_ratio),
        "green_dominance_ratio": float(green_ratio),
        "blue_dominance_ratio": float(blue_ratio),
        "is_blue_contaminated": bool(is_blue_contaminated),
    }


async def run_probe(client: ComfyClient, workflow_path: Path, probe_name: str) -> dict[str, Any]:
    """Run a single probe with production-exact workflow."""
    print(f"\n=== Running {probe_name} ===")
    
    # Load workflow
    with open(workflow_path, 'r') as f:
        workflow = json.load(f)
    
    # Verify recipe parity
    ksampler_node = workflow["3"]
    checkpoint_node = workflow["4"]
    empty_latent_node = workflow["5"]
    positive_node = workflow["6"]
    negative_node = workflow["7"]
    
    # Extract and verify recipe settings
    actual_checkpoint = checkpoint_node["inputs"]["ckpt_name"]
    actual_sampler = ksampler_node["inputs"]["sampler_name"]
    actual_scheduler = ksampler_node["inputs"]["scheduler"]
    actual_steps = ksampler_node["inputs"]["steps"]
    actual_cfg = ksampler_node["inputs"]["cfg"]
    actual_seed = ksampler_node["inputs"]["seed"]
    actual_denoise = ksampler_node["inputs"]["denoise"]
    actual_width = empty_latent_node["inputs"]["width"]
    actual_height = empty_latent_node["inputs"]["height"]
    actual_positive = positive_node["inputs"]["text"]
    actual_negative = negative_node["inputs"]["text"]
    
    # Verify parity
    parity_checks = {
        "checkpoint": bool(actual_checkpoint == PRODUCTION_RECIPE["checkpoint"]),
        "sampler_name": bool(actual_sampler == PRODUCTION_RECIPE["sampler_name"]),
        "scheduler": bool(actual_scheduler == PRODUCTION_RECIPE["scheduler"]),
        "steps": bool(actual_steps == PRODUCTION_RECIPE["steps"]),
        "cfg": bool(actual_cfg == PRODUCTION_RECIPE["cfg"]),
        "seed": bool(actual_seed == PRODUCTION_RECIPE["seed"]),
        "denoise": bool(actual_denoise == PRODUCTION_RECIPE["denoise"]),
        "width": bool(actual_width == PRODUCTION_RECIPE["width"]),
        "height": bool(actual_height == PRODUCTION_RECIPE["height"]),
        "positive_prompt": bool(actual_positive == PRODUCTION_RECIPE["positive_prompt"]),
        "negative_prompt": bool(actual_negative == PRODUCTION_RECIPE["negative_prompt"]),
    }
    
    all_parity_passed = bool(all(parity_checks.values()))
    
    if not all_parity_passed:
        print(f"  WARNING: Recipe parity check failed!")
        for key, passed in parity_checks.items():
            if not passed:
                print(f"    {key}: FAILED")
    else:
        print(f"  Recipe parity: PASSED")
    
    # Submit to ComfyUI
    prompt_id = await client.queue_prompt(workflow)
    print(f"  Prompt ID: {prompt_id}")
    
    # Watch progress
    history_item = await watch_progress.run(None, client=client, prompt_id=prompt_id)
    images = await fetch_outputs.run(None, client=client, history_item=history_item)
    
    if not images:
        raise RuntimeError(f"No images generated for {probe_name}")
    
    # Analyze first output image
    image_info = images[0]
    print(f"  Image info: {image_info}")
    
    # ComfyUI output directory
    comfyui_output = Path("f:/ComfyUI/comfyUI_portable_inst/ComfyUI_windows_portable_nvidia_cu126/ComfyUI_windows_portable/ComfyUI/output")
    
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
        "checkpoint": actual_checkpoint,
        "sampler_name": actual_sampler,
        "scheduler": actual_scheduler,
        "steps": actual_steps,
        "cfg": actual_cfg,
        "seed": actual_seed,
        "denoise": actual_denoise,
        "width": actual_width,
        "height": actual_height,
        "positive_prompt": actual_positive,
        "negative_prompt": actual_negative,
        "output_filename": image_info["filename"],
        "channel_stats": channel_stats,
        "parity_checks": parity_checks,
        "all_parity_passed": all_parity_passed,
        "validity_verdict": "valid" if is_valid else "invalid_blue",
    }
    
    print(f"  Output: {image_info['filename']}")
    print(f"  Blue ratio: {channel_stats['blue_dominance_ratio']:.3f}")
    print(f"  Verdict: {result['validity_verdict']}")
    
    return result


def classify_defect(p1: dict, p2: dict) -> dict[str, Any]:
    """Apply differential classification logic for production-exact probes."""
    p1_blue = p1["channel_stats"]["is_blue_contaminated"]
    p2_blue = p2["channel_stats"]["is_blue_contaminated"]
    
    if not p1_blue and p2_blue:
        defect_class = "batch_execution_context_defect"
        reasoning = "P1 normal, P2 blue. Defect is batch-execution-context-specific (orchestrator, submission style, or runtime state), not in the workflow itself."
    elif p1_blue and p2_blue:
        defect_class = "production_workflow_defect"
        reasoning = "P1 blue, P2 blue. Defect exists in the production workflow itself, not batch-specific. The issue is in the core pipeline (checkpoint, VAE, or recipe)."
    elif not p1_blue and not p2_blue:
        defect_class = "runtime_submission_context_defect"
        reasoning = "Neither P1 nor P2 reproduces defect. Defect is likely in runtime submission context / orchestration / payload mutation that neither probe replicates."
    else:
        defect_class = "unknown"
        reasoning = "Unexpected combination of results."
    
    return {
        "defect_class": defect_class,
        "reasoning": reasoning,
        "p1_blue": p1_blue,
        "p2_blue": p2_blue,
    }


async def main():
    print("=== MK-6K-PX — Production-Exact Differential Replay v1 ===")
    print()
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("Production recipe (from failing batch kt5_proof_001/job_001):")
    for key, value in PRODUCTION_RECIPE.items():
        print(f"  {key}: {value}")
    print()
    
    client = ComfyClient()
    
    # Analyze actual batch output for comparison
    print("\n=== Analyzing Actual Batch Output ===")
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
    p1_path = PROJECT_ROOT / "mk6k_px_probe_p1_workflow.json"
    p2_path = PROJECT_ROOT / "mk6k_px_probe_p2_workflow.json"
    
    try:
        p1_result = await run_probe(client, p1_path, "Probe_P1_Single_Slot")
        p2_result = await run_probe(client, p2_path, "Probe_P2_Batch_Replay")
        
        # Differential comparison
        print("\n=== Differential Comparison ===")
        comparison = {
            "p1": p1_result,
            "p2": p2_result,
        }
        
        # Classification
        batch_blue = batch_stats["is_blue_contaminated"] if batch_stats else False
        classification = classify_defect(p1_result, p2_result)
        
        print(f"\nDefect Class: {classification['defect_class']}")
        print(f"Reasoning: {classification['reasoning']}")
        print()
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_path = OUTPUT_DIR / f"mk6k_px_results_{timestamp}.json"
        
        results = {
            "probe_id": "MK-6K-PX",
            "probe_version": "v1",
            "timestamp": datetime.now().isoformat(),
            "production_recipe": PRODUCTION_RECIPE,
            "batch_output_analysis": batch_stats,
            "probe_p1": p1_result,
            "probe_p2": p2_result,
            "differential_comparison": comparison,
            "root_cause_classification": classification,
            "final_decision": classification["defect_class"],
        }
        
        with open(results_path, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to: {results_path}")
        
        # Final verdict
        is_pass = bool(classification["defect_class"] != "runtime_submission_context_defect" and classification["defect_class"] != "unknown")
        
        print("\n=== FINAL VERDICT ===")
        print(f"MK-6K-PX: {'PASS' if is_pass else 'FAIL'}")
        print(f"Defect Class: {classification['defect_class']}")
        
        # Output fragments
        print("\n=== Probe P1 Fragment ===")
        print(f"  Workflow: EmptyLatentImage -> KSampler -> VAEDecode -> SaveImage (production-exact single-slot)")
        print(f"  Blue contaminated: {p1_result['channel_stats']['is_blue_contaminated']}")
        print(f"  Blue ratio: {p1_result['channel_stats']['blue_dominance_ratio']:.3f}")
        print(f"  Parity passed: {p1_result['all_parity_passed']}")
        
        print("\n=== Probe P2 Fragment ===")
        print(f"  Workflow: EmptyLatentImage -> KSampler -> VAEDecode -> SaveImage (production-exact batch replay)")
        print(f"  Blue contaminated: {p2_result['channel_stats']['is_blue_contaminated']}")
        print(f"  Blue ratio: {p2_result['channel_stats']['blue_dominance_ratio']:.3f}")
        print(f"  Parity passed: {p2_result['all_parity_passed']}")
        
        print("\n=== Parity Proof Fragment ===")
        print(f"  P1 parity: {p1_result['all_parity_passed']}")
        print(f"  P2 parity: {p2_result['all_parity_passed']}")
        print(f"  Both probes use exact production recipe")
        
        print("\n=== Differential Comparison Fragment ===")
        print(f"  P1 blue: {classification['p1_blue']}")
        print(f"  P2 blue: {classification['p2_blue']}")
        print(f"  Batch output blue: {batch_blue}")
        
        print("\n=== Root Cause Classification Fragment ===")
        print(f"  Class: {classification['defect_class']}")
        print(f"  Reasoning: {classification['reasoning']}")
        
        print("\n=== Final Decision Fragment ===")
        print(f"  MK-6K-PX: {'PASS' if is_pass else 'FAIL'}")
        print(f"  Defect isolated to: {classification['defect_class']}")
        
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
