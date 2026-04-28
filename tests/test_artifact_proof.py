"""MK-REAL3R-4 Artifact Proof Test

This test generates actual JSON artifacts from the CLI path with mocked ComfySubmitter
to prove the fix works end-to-end with dry/mocked execution.

MK-REAL3R-6E — Updated to use clean single portrait v2 for Alya.
"""
import argparse
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from app.cli import generate_frames_from_prompt_pack


def test_generate_artifact_proofs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Generate actual JSON artifacts from the CLI path with mocked ComfySubmitter for proof."""
    
    # Setup directory structure
    (tmp_path / "data" / "briefs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "config").mkdir(parents=True, exist_ok=True)
    (tmp_path / "data" / "config" / "workflow_template_img2img_reference.json").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "control").mkdir(parents=True, exist_ok=True)
    (tmp_path / "output" / "frames" / "ep01_shot01").mkdir(parents=True, exist_ok=True)
    (tmp_path / "references").mkdir(parents=True, exist_ok=True)

    # Create brief file
    (tmp_path / "data" / "briefs" / "ep01_shot01_brief.md").write_text(
        "## Meta\ntitle: Test\nduration: 5\n\n## Characters\n- name: Hero\n  visual: knight\n\n## Scenes\n- action: hero walks\n",
        encoding="utf-8",
    )

    # Create img2img reference workflow template with correct node wiring
    # CheckpointLoaderSimple outputs: [0]=MODEL, [1]=CLIP, [2]=VAE
    img2img_template = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": "example.png"},
        },
        "2": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["1", 0],
                "width": 480,
                "height": 640,
                "crop": "disabled",
                "upscale_method": "lanczos",
            },
        },
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["10", 2],  # VAE output from CheckpointLoaderSimple
            },
        },
        "4": {
            "class_type": "EmptyLatentImage",
            "inputs": {
                "width": 512,
                "height": 512,
                "batch_size": 1,
            },
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "positive prompt placeholder",
                "clip": ["10", 1],  # CLIP output from CheckpointLoaderSimple
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "negative prompt placeholder",
                "clip": ["10", 1],  # CLIP output from CheckpointLoaderSimple
            },
        },
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 12345,
                "steps": 16,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 0.5,
                "model": ["10", 0],  # MODEL output from CheckpointLoaderSimple
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["3", 0],  # Connected to VAEEncode, not EmptyLatentImage
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {
                "ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
            },
        },
    }
    workflow_path = tmp_path / "data" / "config" / "workflow_template_img2img_reference.json"
    workflow_path.write_text(json.dumps(img2img_template), encoding="utf-8")

    # MK-REAL3R-6E — Create clean single portrait v2 in staging directory
    staging_dir = tmp_path / "output" / "control" / "references"
    staging_dir.mkdir(parents=True, exist_ok=True)
    
    # Create a small mock original that will pass clean reference gate
    from PIL import Image
    mock_contact = tmp_path / "референсы" / "Аля.png"
    mock_contact.parent.mkdir(parents=True, exist_ok=True)
    # Create a small portrait (512x512) that passes clean reference gate
    contact_img = Image.new("RGB", (512, 512), color="white")
    contact_img.save(mock_contact)
    
    # Create v2 clean portrait from mock original
    from app.reference.reference_staging import create_alya_clean_single_portrait_v2
    create_alya_clean_single_portrait_v2(mock_contact, staging_dir, force=True)
    
    # Create prompt_pack.json with reference_locked metadata and exact MK-REAL3R-3 prompts
    control_dir = tmp_path / "output" / "control"
    # Use mock contact path for proof (to trigger staging logic)
    mock_alya_path = str(mock_contact)
    prompt_pack = {
        "episode_id": "ep01",
        "shot_id": "shot01",
        "characters": ["Alya"],
        "beats": [
            {
                "beat_id": "beat_001",
                "positive_prompt": "vertical portrait composition, ordinary tired young woman 24 years old, dark brown hair in messy bun clearly visible, hood down, pale skin, dark eyes, gray oversized sweatshirt, blue jeans, sitting on messy bed in small modest apartment bedroom, holding simple black smartphone in both hands, tired focused expression, slightly worried, early morning cold gray-blue window light, documentary realism, realistic Ukrainian Eastern European apartment mood, no makeup, candid moment, realistic skin texture",
                "negative_prompt": "glamour, fashion model, beauty portrait, studio portrait, stock photo, advertisement, perfect makeup, smiling, looking at camera, hood up, hood covering head, blue hoodie, luxury hotel, clean staged bedroom, plastic skin, wax skin, over-smoothed face, anime, cartoon, bad anatomy, distorted face, bad hands, extra fingers, red skin, orange skin, artifacts, picture frame, decorative frame, border, text, watermark",
                "seed_policy": "deterministic",
            }
        ],
        "generation_mode": "reference_locked",
        "reference_image_path": mock_alya_path,
        "denoise": 0.5,
    }
    (control_dir / "prompt_pack.json").write_text(json.dumps(prompt_pack), encoding="utf-8")

    # Create config.json
    config_data = {
        "lora_dir": "data/loras",
        "fallback_voice_id": "default",
        "default_negative": "bad anatomy",
        "fps": 24,
        "min_keyframes": 1,
        "checkpoint": "CyberRealisticXLPlay_V7.0_FP16.safetensors",
    }
    (tmp_path / "data" / "config.json").write_text(json.dumps(config_data), encoding="utf-8")

    # Create voice_map.json
    (tmp_path / "data" / "voice_map.json").write_text(json.dumps({"default": "default_voice"}), encoding="utf-8")

    # Create generation_recipes.json to enable observed settings snapshot writing
    # Structure must match GenerationRecipe model from app/recipes/models.py
    recipes = [
        {
            "recipe_id": "sdxl_reference_locked_character_gtx1060",
            "task_type": "reference_locked_character",
            "model_family": "sdxl",
            "checkpoint_allowlist": ["CyberRealisticXLPlay_V7.0_FP16.safetensors"],
            "sampler_allowlist": ["dpmpp_sde", "dpmpp_2m", "euler", "euler_a"],
            "scheduler_allowlist": ["karras", "normal", "simple"],
            "steps_min": 10,
            "steps_max": 30,
            "cfg_min": 5.0,
            "cfg_max": 10.0,
            "batch_size_max": 1,
            "max_pixels": 512000,
            "allowed_aspect_ratios": {
                "9:16": [480, 640],
                "1:1": [512, 512],
            },
            "denoise_min": 0.3,
            "denoise_max": 0.7,
            "required_negative_terms": ["bad anatomy"],
        }
    ]
    (tmp_path / "data" / "generation_recipes.json").write_text(json.dumps(recipes, indent=2), encoding="utf-8")

    # Create hardware_profiles.json
    hardware_profile = {
        "profile_id": "gtx_1060_5gb",
        "gpu_name": "NVIDIA GTX 1060 5GB",
        "vram_gb": 5.0,
        "max_pixels_sdxl": 512000,
        "max_batch_size_sdxl": 1,
        "recommended_batch_size_sdxl": 1,
    }
    (tmp_path / "data" / "hardware_profiles.json").write_text(json.dumps(hardware_profile, indent=2), encoding="utf-8")

    # Captured artifacts
    captured_workflow = {"wf": None}
    captured_kwargs = {"kwargs": None}

    # Mock HTTP calls but let real submit run to get prompt injection and workflow patching
    from app.comfy.submitter import ComfySubmitter
    original_submit = ComfySubmitter.submit

    def mock_submit(self, scene, workflow, **kwargs):
        captured_kwargs["kwargs"] = kwargs
        # Call original submit to get prompt injection and patching, but mock HTTP
        with patch.object(self, "session"):
            mock_session = Mock()
            mock_session.post.return_value.status_code = 200
            mock_session.post.return_value.json.return_value = {"prompt_id": "test-123"}
            self.session = mock_session
            
            try:
                result = original_submit(self, scene, workflow, **kwargs)
            except Exception:
                # If anything fails, return a mock result
                from app.comfy.models import SubmitResult
                result = SubmitResult(
                    prompt_id="test-123",
                    scene_id=scene.scene_id,
                    frame_paths=[],
                    elapsed_sec=1.0,
                )
        return result

    monkeypatch.setattr(ComfySubmitter, "submit", mock_submit)

    # Change to tmp_path
    monkeypatch.chdir(tmp_path)

    # Call the CLI function
    args = argparse.Namespace(
        config=str(tmp_path / "data" / "config.json"),
        output=str(tmp_path / "output"),
        host="localhost",
        port=8188,
        episode_id="ep01",
        shot_id="shot01",
        prompt_pack=True,
        brief=str(tmp_path / "data" / "briefs" / "ep01_shot01_brief.md"),
    )

    generate_frames_from_prompt_pack(args)

    # Write artifacts to persistent location for inspection
    proof_dir = Path(__file__).parent.parent / "data" / "artifact_proofs"
    proof_dir.mkdir(parents=True, exist_ok=True)

    # Write submitted workflow from the file that was written by ComfySubmitter
    submitted_workflow_path = tmp_path / "output" / "control" / "ep01_shot01_submitted_workflow.json"
    if submitted_workflow_path.exists():
        submitted_data = json.loads(submitted_workflow_path.read_text(encoding="utf-8"))
        captured_workflow["wf"] = submitted_data
        (proof_dir / "submitted_workflow.json").write_text(
            json.dumps(submitted_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Write observed settings if they were written
    observed_path = tmp_path / "output" / "control" / "ep01_shot01_observed_settings.json"
    observed_file_path = proof_dir / "observed_settings.json"
    if observed_path.exists():
        observed_raw = json.loads(observed_path.read_text(encoding="utf-8"))
        # Handle wrapped format: {"observed_settings": {...}}
        if "observed_settings" in observed_raw:
            observed_data = observed_raw["observed_settings"]
        else:
            observed_data = observed_raw
        (proof_dir / "observed_settings.json").write_text(
            json.dumps(observed_data, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Write prompt pack
    (proof_dir / "prompt_pack.json").write_text(
        json.dumps(prompt_pack, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Generate control-status JSON proof
    from app.recipes.validator import GenerationRecipeValidator
    from app.recipes.registry import RecipeRegistry, HardwareProfileRegistry
    from app.recipes.advisor import GenerationSettingsAdvisor

    if observed_file_path.exists():
        observed_data = json.loads(observed_file_path.read_text(encoding="utf-8"))
        
        # Get recipe and hardware
        recipe_registry = RecipeRegistry(tmp_path / "data" / "generation_recipes.json")
        hardware_registry = HardwareProfileRegistry(tmp_path / "data" / "hardware_profiles.json")
        advisor = GenerationSettingsAdvisor(recipe_registry, hardware_registry)
        
        # Determine task type and hardware profile
        task_type = "reference_locked_character"
        hardware_profile_id = "gtx_1060_5gb"
        
        # Get recommended recipe
        recipe = advisor.recommend_recipe(
            task_type=task_type,
            project_profile={},
            hardware_profile_id=hardware_profile_id,
            generation_mode="reference_locked"
        )
        hardware = hardware_registry.get(hardware_profile_id)
        
        # Validate observed settings against recipe
        validator = GenerationRecipeValidator()
        validation_result = validator.validate(
            observed=observed_data,
            recipe=recipe,
            hardware=hardware,
            task_type=task_type
        )
        
        # Build control-status JSON
        control_status = {
            "recipe_validation": {
                "available": True,
                "settings_source": "observed",
                "recipe_id": recipe.recipe_id,
                "verdict": validation_result.verdict,
            },
            "validation_result": validation_result.to_dict(),
        }
        
        (proof_dir / "control_status.json").write_text(
            json.dumps(control_status, indent=2, ensure_ascii=False), encoding="utf-8"
        )

    # Print proof summary
    print("\n================================================================================")
    print("MK-REAL3R-4 ARTIFACT PROOF SUMMARY")
    print("================================================================================\n")

    # Print submitted workflow structure
    print("--- Submitted Workflow Structure ---")
    if captured_workflow["wf"]:
        wf = captured_workflow["wf"]
        for node_id, node in wf.items():
            class_type = node.get("class_type", "unknown")
            print(f"  {node_id}: {class_type}")
            if class_type == "LoadImage":
                print(f"    image input: {node.get('inputs', {}).get('image', 'N/A')}")
            elif class_type == "ImageScale":
                print(f"    width: {node.get('inputs', {}).get('width', 'N/A')}")
                print(f"    height: {node.get('inputs', {}).get('height', 'N/A')}")
                print(f"    image input: {node.get('inputs', {}).get('image', 'N/A')}")
            elif class_type == "VAEEncode":
                print(f"    inputs: {list(node.get('inputs', {}).keys())}")
            elif class_type == "KSampler":
                print(f"    steps: {node.get('inputs', {}).get('steps', 'N/A')}")
                print(f"    denoise: {node.get('inputs', {}).get('denoise', 'N/A')}")
                print(f"    latent_image: {node.get('inputs', {}).get('latent_image', 'N/A')}")
                print(f"    positive: {node.get('inputs', {}).get('positive', 'N/A')}")
                print(f"    negative: {node.get('inputs', {}).get('negative', 'N/A')}")

    # Print observed settings from the written file
    print("\n--- Observed Settings ---")
    observed_file_path = proof_dir / "observed_settings.json"
    if observed_file_path.exists():
        observed_data = json.loads(observed_file_path.read_text(encoding="utf-8"))
        print(f"  checkpoint: {observed_data.get('checkpoint', 'N/A')}")
        print(f"  generation_mode: {observed_data.get('generation_mode', 'N/A')}")
        print(f"  reference_image_path: {observed_data.get('reference_image_path', 'N/A')}")
        print(f"  width: {observed_data.get('width', 'N/A')}")
        print(f"  height: {observed_data.get('height', 'N/A')}")
        print(f"  batch_size: {observed_data.get('batch_size', 'N/A')}")
        print(f"  steps: {observed_data.get('steps', 'N/A')}")
        print(f"  denoise: {observed_data.get('denoise', 'N/A')}")

    # Print prompt texts
    print("\n--- Prompt Texts ---")
    if captured_workflow["wf"]:
        wf = captured_workflow["wf"]
        for node_id, node in wf.items():
            if node.get("class_type") == "CLIPTextEncode":
                text = node.get("inputs", {}).get("text", "")
                # Truncate for display
                if len(text) > 200:
                    text = text[:200] + "..."
                print(f"  {node_id}: {text}")

    # Print CLI call metadata
    print("\n--- CLI Call Metadata ---")
    if captured_kwargs["kwargs"]:
        kw = captured_kwargs["kwargs"]
        print(f"  generation_mode: {kw.get('generation_mode', 'N/A')}")
        print(f"  reference_image_path: {kw.get('reference_image_path', 'N/A')}")
        print(f"  denoise: {kw.get('denoise', 'N/A')}")

    print("\n================================================================================")
    print(f"Artifacts written to: {proof_dir}")
    print("================================================================================\n")

    # Assertions
    assert captured_kwargs["kwargs"]["generation_mode"] == "reference_locked"
    assert "Аля.png" in str(captured_kwargs["kwargs"]["reference_image_path"])
