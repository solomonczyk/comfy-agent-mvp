"""Execute one corrective generation using approved v10 contract."""

import asyncio
import hashlib
import json
import random
import time
from pathlib import Path
from datetime import datetime

from app.comfy.comfy_client import ComfyClient


async def main():
    """Execute corrective generation."""
    # Load config
    config_path = Path("data/config.json")
    with open(config_path) as f:
        config = json.load(f)
    
    # Load v10 prompt package
    prompt_package_path = Path("combine_v2_v10_prompt_package.json")
    with open(prompt_package_path) as f:
        prompt_package = json.load(f)
    
    # Load v10 workflow guardrails
    guardrails_path = Path("combine_v2_v10_workflow_guardrails.json")
    with open(guardrails_path) as f:
        guardrails = json.load(f)
    
    # Build simplified workflow for v10 corrective generation
    # Using basic SDXL workflow without IP-Adapter/Lora dependencies
    guardrails_params = guardrails["workflow_guardrails"]["generation_parameters"]
    
    workflow = {
        "3": {
            "inputs": {
                "seed": random.randint(1, 999999999) if guardrails_params["seed"] == "random" else int(guardrails_params["seed"]),
                "steps": guardrails_params["steps"],
                "cfg": guardrails_params["cfg_scale"],
                "sampler_name": guardrails_params["sampler"].replace("DPM++ 2M Karras", "dpmpp_2m"),
                "scheduler": "karras",
                "denoise": 1.0,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            },
            "class_type": "KSampler"
        },
        "4": {
            "inputs": {
                "ckpt_name": config["checkpoint"]
            },
            "class_type": "CheckpointLoaderSimple"
        },
        "5": {
            "inputs": {
                "width": 1024,
                "height": 1024,
                "batch_size": 1
            },
            "class_type": "EmptyLatentImage"
        },
        "6": {
            "inputs": {
                "text": prompt_package["positive_prompt"],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {
                "text": prompt_package["negative_prompt"],
                "clip": ["4", 1]
            },
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2]
            },
            "class_type": "VAEDecode"
        },
        "9": {
            "inputs": {
                "images": ["8", 0],
                "filename_prefix": "corrective_v10"
            },
            "class_type": "SaveImage"
        }
    }
    
    # Initialize client
    client = ComfyClient()
    
    print(f"Submitting corrective generation with v10 parameters...")
    print(f"Positive prompt: {prompt_package['positive_prompt'][:100]}...")
    print(f"Negative prompt: {prompt_package['negative_prompt'][:100]}...")
    print(f"Sampler: {guardrails_params['sampler']}")
    print(f"Steps: {guardrails_params['steps']}")
    print(f"CFG: {guardrails_params['cfg_scale']}")
    print(f"Seed: {workflow['3']['inputs']['seed']}")
    
    # Submit workflow
    prompt_id = await client.queue_prompt(workflow)
    print(f"Prompt submitted: {prompt_id}")
    
    # Wait for completion
    print("Waiting for generation to complete...")
    history_item = await client.watch_progress_websocket(
        prompt_id,
        status_callback=lambda status, payload: print(f"Status: {status} | {payload}")
    )
    
    # Extract images
    images = client.extract_images(history_item)
    print(f"Generation completed. Found {len(images)} images.")
    
    if not images:
        raise RuntimeError("No images generated")
    
    # Download and validate the first image
    image_info = images[0]
    image_data = await client.fetch_image(
        filename=image_info["filename"],
        subfolder=image_info["subfolder"] or "",
        type=image_info["type"]
    )
    
    # Save image to canonical location
    output_dir = Path("data/outputs/corrective_v10")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    image_path = output_dir / image_info["filename"]
    with open(image_path, "wb") as f:
        f.write(image_data["content"])
    
    print(f"Image saved to: {image_path}")
    
    # Calculate sha256
    sha256 = hashlib.sha256(image_data["content"]).hexdigest()
    size_bytes = len(image_data["content"])
    
    # Get dimensions (for PNG, parse the IHDR chunk)
    # Simple approach: use PIL if available, otherwise record as unknown
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            width, height = img.size
    except ImportError:
        width, height = 0, 0
    
    print(f"Image validation:")
    print(f"  Path: {image_path}")
    print(f"  Exists: {image_path.exists()}")
    print(f"  Size: {size_bytes} bytes")
    print(f"  SHA256: {sha256}")
    print(f"  Dimensions: {width}x{height}")
    
    # Create generation result
    result = {
        "task_id": "RC-COMBINE-V2-EXECUTE-ONE-CORRECTIVE-GENERATION-001",
        "prompt_id": prompt_id,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "generated_asset": {
            "path": str(image_path),
            "filename": image_info["filename"],
            "exists": image_path.exists(),
            "readable": True,
            "sha256": sha256,
            "size_bytes": size_bytes,
            "width": width,
            "height": height
        },
        "generation_parameters": {
            "positive_prompt": prompt_package["positive_prompt"],
            "negative_prompt": prompt_package["negative_prompt"],
            "sampler": guardrails_params["sampler"],
            "steps": guardrails_params["steps"],
            "cfg": guardrails_params["cfg_scale"],
            "seed": workflow["3"]["inputs"]["seed"]
        },
        "generation_count": 1,
        "max_generations": 1,
        "retry_attempted": False,
        "blind_retry_attempted": False
    }
    
    # Save result
    result_path = Path("corrective_generation_result.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2)
    
    print(f"Result saved to: {result_path}")
    
    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\n" + "="*60)
    print("CORRECTIVE GENERATION COMPLETED")
    print("="*60)
    print(json.dumps(result, indent=2))
