import json
import urllib.request

# Simple test workflow
test_workflow = {
    "3": {
        "inputs": {
            "seed": 123456789,
            "steps": 20,
            "cfg": 7.0,
            "sampler_name": "dpmpp_2m",
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
            "ckpt_name": "sd_xl_base_1.0_0.9vae.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "5": {
        "inputs": {
            "width": 512,
            "height": 512,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    },
    "6": {
        "inputs": {
            "text": "a simple test image",
            "clip": ["4", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "7": {
        "inputs": {
            "text": "blurry, low quality",
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
            "filename_prefix": "test_",
            "images": ["8", 0]
        },
        "class_type": "SaveImage"
    }
}

# Submit to ComfyUI
try:
    body = json.dumps({"prompt": test_workflow}).encode("utf-8")
    req = urllib.request.Request(
        "http://127.0.0.1:8188/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    
    print("Response:", json.dumps(data, indent=2))
    
    if "prompt_id" in data:
        prompt_id = data["prompt_id"]
        print(f"Success! Prompt ID: {prompt_id}")
    else:
        print("Error:", data)
        
except Exception as e:
    print(f"Failed: {e}")
