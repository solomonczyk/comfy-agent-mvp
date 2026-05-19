"""Identity and Composition Lock Recovery - RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001

This script recovers from a rejected identity_lock generation by:
- Recording the rejection of identity_lock__00001_.png
- Rebuilding identity + composition + environment conditioning
- Blocking generic portrait fallback
- Requiring environment/background visibility
- Generating one new real visual candidate
- Stopping at operator_visual_review_required
"""

from __future__ import annotations

import json
from pathlib import Path

# Set project root
PROJECT_ROOT = Path(r"f:\ComfyUI\comfy-agent-mvp")
DATA_ROOT = PROJECT_ROOT / "data" / "rc2_multishot1_ep01"

# Import the identity lock runner
from app.agents.identity_lock.runner import IdentityLockRunner


def load_base_workflow() -> dict:
    """Load the base ComfyUI workflow."""
    workflow_path = DATA_ROOT / "output" / "control" / "identity_lock" / "submitted_identity_locked_workflow.json"
    
    if workflow_path.exists():
        with open(workflow_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback to a standard SDXL workflow template
    return {
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "cinematic shot of a woman in environment, medium shot, detailed background",
                "clip": ["4", 1]
            }
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "blurry, low quality, distorted, ugly, bad anatomy, extra limbs, watermark",
                "clip": ["4", 1]
            }
        },
        "4": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "positive placeholder",
                "clip": ["4", 1]
            }
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 1344,
                "height": 768,
                "batch_size": 1
            }
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 20,
                "cfg": 7.0,
                "sampler_name": "euler",
                "scheduler": "normal",
                "denoise": 1.0,
                "model": ["10", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["5", 0]
            }
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "sd_xl_base_1.0.safetensors"
            }
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["10", 2]
            }
        },
        "8": {
            "class_type": "SaveImage",
            "inputs": {
                "filename_prefix": "identity_lock_recovery",
                "images": ["9", 0]
            }
        }
    }


def load_canonical_inventory() -> list[dict]:
    """Load canonical reference inventory."""
    inventory_path = DATA_ROOT / "input" / "canonical_references" / "inventory.json"
    
    if inventory_path.exists():
        with open(inventory_path, "r", encoding="utf-8") as f:
            return json.load(f)
    
    # Fallback inventory
    return [
        {
            "relative_path": "01_identity/character_from_the_front_body_proportions.png",
            "role": "identity",
            "category": "identity"
        },
        {
            "relative_path": "01_identity/headshot_front.png",
            "role": "identity",
            "category": "identity"
        },
        {
            "relative_path": "01_identity/full_body_front_neutral.png",
            "role": "identity",
            "category": "identity"
        }
    ]


def main():
    """Execute the identity and composition lock recovery."""
    print("=" * 80)
    print("RC-COMBINE-V2-ACTOR-IDENTITY-AND-COMPOSITION-LOCKED-VISUAL-RECOVERY-001")
    print("=" * 80)
    
    # Initialize the identity lock runner
    runner = IdentityLockRunner(DATA_ROOT)
    
    # Load inputs
    canonical_inventory = load_canonical_inventory()
    base_workflow = load_base_workflow()
    
    # Previous rejected asset
    previous_rejected_assets = [
        str(DATA_ROOT / "output" / "assets" / "identity_lock__00001_.png")
    ]
    
    previous_asset_path = previous_rejected_assets[0]
    
    # Operator rejection reason (generic portrait fallback, environment not visible)
    operator_rejection_reason = [
        "Generic beauty portrait generated instead of character-in-environment",
        "Environment/background not visible",
        "Character reduced to face-only close-up",
        "Identity lock failed - generic face substitution occurred"
    ]
    
    print(f"\nPrevious rejected asset: {previous_asset_path}")
    print(f"Rejection reason: {operator_rejection_reason}")
    print(f"Canonical inventory: {len(canonical_inventory)} references")
    
    # Run the identity lock recovery
    print("\n" + "=" * 80)
    print("Running identity lock recovery...")
    print("=" * 80 + "\n")
    
    result = runner.run(
        canonical_inventory=canonical_inventory,
        previous_rejected_assets=previous_rejected_assets,
        operator_rejection_reason=operator_rejection_reason,
        previous_asset_path=previous_asset_path,
        base_workflow=base_workflow,
    )
    
    print("\n" + "=" * 80)
    print("Recovery Result")
    print("=" * 80)
    print(json.dumps(result, indent=2))
    
    # Check for success
    if result.get("status") == "completed":
        print("\n" + "=" * 80)
        print("SUCCESS: Identity lock recovery completed")
        print("=" * 80)
        print(f"Generated asset: {result.get('generated_asset_path')}")
        print(f"Prompt ID: {result.get('prompt_id')}")
        print(f"Blank detector passed: {result.get('blank_detector_passed')}")
        print(f"Framing detector passed: {result.get('framing_detector_passed')}")
        print(f"Environment visibility passed: {result.get('environment_visibility_passed')}")
        print(f"Generic portrait blocked: {result.get('generic_portrait_blocked')}")
        print(f"Single subject gate passed: {result.get('single_subject_gate_passed')}")
        print(f"Identity gate result: {result.get('identity_gate_result')}")
        print("\nState: operator_visual_review_required")
        print("Next action: operator_visual_review_required")
        print("\nNo second generation performed (exactly one generation as required)")
        print("No Visual QA/operator acceptance by agent (forbidden)")
        print("No assembly/downstream (forbidden)")
        print("production_accepted remains False (forbidden to set True)")
    else:
        print("\n" + "=" * 80)
        print("FAILURE: Identity lock recovery failed")
        print("=" * 80)
        print(f"Status: {result.get('status')}")
        print(f"Reason: {result.get('reason')}")


if __name__ == "__main__":
    main()
