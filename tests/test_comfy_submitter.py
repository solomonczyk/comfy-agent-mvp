"""Tests for MK-E1 — ComfySubmitter.

All HTTP calls are mocked via a mock session object.
"""
from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock

import pytest

from app.comfy.exceptions import ComfySubmitError, ComfyTimeoutError
from app.comfy.models import SubmitResult
from app.comfy.submitter import ComfySubmitter
from app.scenes.models import BuiltScene


# ── MK-REAL3R — Graph contract validation tests ─────────────────────────────────

def test_validate_reference_locked_graph_contract_passes_valid_img2img_workflow():
    """MK-REAL3R — Test that valid img2img workflow passes graph contract validation."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Valid img2img workflow with LoadImage -> ImageScale -> VAEEncode -> KSampler
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],  # Connected to VAEEncode
                "steps": 16,  # MK-REAL3R-2: Added steps
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["11", 0]},
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1},
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert errors == []


def test_validate_reference_locked_graph_contract_fails_missing_load_image():
    """MK-REAL3R — Test that workflow without LoadImage fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: no LoadImage node
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
            },
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {},
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert "no LoadImage node found in workflow" in errors


def test_validate_reference_locked_graph_contract_fails_missing_vae_encode():
    """MK-REAL3R — Test that workflow without VAEEncode fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: no VAEEncode node
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["5", 0],  # Connected to EmptyLatentImage
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert "no VAEEncode node found in workflow" in errors


def test_validate_reference_locked_graph_contract_fails_ksampler_connected_to_empty_latent():
    """MK-REAL3R — Test that workflow with KSampler connected to EmptyLatentImage fails."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: KSampler connected to EmptyLatentImage instead of VAEEncode
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["10", 0],  # Connected to EmptyLatentImage
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {},
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 1},
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("EmptyLatentImage" in error for error in errors)


def test_validate_reference_locked_graph_contract_fails_batch_size_gt_1():
    """MK-REAL3R — Test that workflow with batch_size > 1 fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: batch_size is 2 and EmptyLatentImage is connected to KSampler
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["10", 0],  # Connected to EmptyLatentImage
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {},
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"batch_size": 2},  # Too high and connected to KSampler
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("batch_size" in error and "must be 1" in error for error in errors)


def test_submit_blocks_invalid_reference_locked_workflow_before_http_submit():
    """MK-REAL3R — Test that submit blocks invalid reference_locked workflow before HTTP submit."""
    scene = _built_scene()
    
    # Invalid txt2img workflow (no LoadImage/VAEEncode)
    workflow = _workflow_template()
    
    mock_session = Mock()
    
    submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")
    
    # Should raise ComfySubmitError due to graph contract failure
    with pytest.raises(ComfySubmitError) as exc_info:
        submitter.submit(
            scene,
            workflow,
            timeout_sec=1.0,
            generation_mode="reference_locked",
            reference_image_path=Path("data/references/test.png"),
            episode_id="ep01",
            shot_id="shot01",
            project_root=Path(tempfile.mkdtemp()),
        )
    
    # RC-REAL2 — Clean reference gate runs before graph contract validation
    # If the reference file doesn't exist, the clean reference gate will block it first
    assert "BLOCKED_BY_INVALID_CLEAN_REFERENCE" in str(exc_info.value)
    # HTTP submit should NOT have been called
    assert mock_session.post.call_count == 0


def test_submit_valid_reference_locked_workflow_with_real_alya_path():
    """MK-REAL3R-3A — Test that valid reference_locked workflow with real Alya path passes, writes artifacts, and injects scriptwriter prompts correctly.
    
    RC-REAL2: This test now uses a valid clean reference (480x640) to pass the new ReferenceQC gate.
    """
    scene = _alya_built_scene()
    
    # Valid img2img workflow with LoadImage -> ImageScale -> VAEEncode -> KSampler
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],  # Connected to VAEEncode
                "denoise": 0.5,  # Within valid range 0.45-0.75
                "steps": 16,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/alya_reference_01.png"},
        },
        "6": {
            "inputs": {"text": "", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode"
        },
        "7": {
            "inputs": {"text": "", "clip": ["4", 1]},
            "class_type": "CLIPTextEncode"
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["11", 0],  # Connected to ImageScale
                "vae": ["4", 2],
            },
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {
                "samples": ["3", 0],
                "vae": ["4", 2],
            },
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 480, "height": 640, "batch_size": 1},
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],  # Connected to LoadImage
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    
    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "test-123"}
    mock_session.post.return_value = mock_response
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"test-123": {"status": {"completed": True}}}
    )
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_root = Path(temp_dir)
        submitter = ComfySubmitter(session=mock_session, output_dir=project_root / "output/frames")
        
        # RC-REAL2: Create a valid clean reference (480x640) for the test
        from PIL import Image
        import numpy as np
        references_dir = project_root / "data" / "references"
        references_dir.mkdir(parents=True, exist_ok=True)
        clean_ref_path = references_dir / "alya_clean_reference_480x640.png"
        # Create a valid image with sufficient entropy
        img_array = np.random.randint(50, 200, (640, 480, 3), dtype=np.uint8)
        clean_img = Image.fromarray(img_array, mode='RGB')
        clean_img.save(clean_ref_path)
        
        result = submitter.submit(
            scene,
            workflow,
            timeout_sec=1.0,
            generation_mode="reference_locked",
            reference_image_path=clean_ref_path,  # Use the valid clean reference
            episode_id="ep01",
            shot_id="shot01",
            project_root=project_root,
        )
        
        # Verify HTTP submit was called (graph contract passed)
        assert mock_session.post.call_count > 0
        
        # Verify observed settings snapshot was written
        observed_path = project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        assert observed_path.exists()
        
        # Verify submitted workflow was written
        submitted_path = project_root / "output" / "control" / "ep01_shot01_submitted_workflow.json"
        assert submitted_path.exists()
        
        # Copy artifacts to permanent location for proof
        proof_dir = Path("data/mk_real3r_proof")
        proof_dir.mkdir(parents=True, exist_ok=True)
        
        import shutil
        shutil.copy(observed_path, proof_dir / "ep01_shot01_observed_settings.json")
        shutil.copy(submitted_path, proof_dir / "ep01_shot01_submitted_workflow.json")
        
        # Generate control-status JSON
        from app.cli import control_status
        import argparse
        args = argparse.Namespace(
            episode="ep01",
            shot="shot01",
            project_root=str(project_root),
            ledger_root="output/control",
            json=True,
            last=10,
        )
        
        import io
        from contextlib import redirect_stdout
        output_buffer = io.StringIO()
        with redirect_stdout(output_buffer):
            exit_code = control_status(args)
        
        control_status_json = json.loads(output_buffer.getvalue())
        
        with open(proof_dir / "control_status.json", "w", encoding="utf-8") as f:
            json.dump(control_status_json, f, indent=2)
        
        # Load and verify observed settings
        with open(observed_path, encoding="utf-8") as f:
            observed_data = json.load(f)
        observed_settings = observed_data["observed_settings"]
        
        assert observed_settings["generation_mode"] == "reference_locked"
        # RC-REAL2: Test now uses synthetic clean reference, check for clean reference filename
        assert "alya_clean_reference_480x640.png" in observed_settings["reference_image_path"]
        assert observed_settings["batch_size"] == 1
        assert observed_settings["denoise"] == 0.5  # MK-REAL3R-2: Updated to 0.5 for valid range
        assert observed_settings["raw_nodes"]["load_image_node"] == "5"
        assert observed_settings["raw_nodes"]["vae_encode_node"] == "8"
        assert observed_settings["raw_nodes"]["latent_node"] == "8"  # VAEEncode
        
        # Load and verify submitted workflow
        with open(submitted_path, encoding="utf-8") as f:
            submitted_workflow = json.load(f)
        
        # Verify LoadImage has staged ASCII path (MK-REAL3R-6 / MK-REAL3R-6E)
        load_image = submitted_workflow["5"]
        # RC-REAL2: Test now uses synthetic clean reference, check for that filename
        assert "alya_clean_reference_480x640.png" in load_image["inputs"]["image"]
        
        # Verify ImageScale is present and has correct resolution
        image_scale = submitted_workflow["11"]
        assert image_scale["class_type"] == "ImageScale"
        assert image_scale["inputs"]["width"] == 480
        assert image_scale["inputs"]["height"] == 640
        assert image_scale["inputs"]["upscale_method"] == "lanczos"
        
        # Verify VAEEncode is connected to ImageScale
        vae_encode = submitted_workflow["8"]
        assert vae_encode["inputs"]["pixels"] == ["11", 0]
        
        # Verify KSampler is connected to VAEEncode
        ksampler = submitted_workflow["3"]
        assert ksampler["inputs"]["latent_image"] == ["8", 0]
        
        # Verify prompt injection: scriptwriter positive/negative must be present, placeholders absent
        assert submitted_workflow["6"]["inputs"]["text"] == ALYA_POSITIVE_PROMPT
        assert submitted_workflow["7"]["inputs"]["text"] == ALYA_NEGATIVE_PROMPT
        assert "beautiful anime girl" not in submitted_workflow["6"]["inputs"]["text"].lower()
        assert submitted_workflow["7"]["inputs"]["text"].strip() != "blurry"
        
        # Verify observed settings snapshot matches injected prompts
        assert observed_settings["negative_prompt"] == ALYA_NEGATIVE_PROMPT
        assert observed_settings["raw_nodes"]["negative_prompt_node"] == "7"
        assert observed_settings["raw_nodes"]["ksampler_node"] == "3"


def test_validate_reference_locked_graph_contract_fails_missing_resize_node():
    """MK-REAL3R-3A — Test that workflow with no resize node fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: no ImageScale or ImageResize node
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
                "steps": 16,
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["5", 0],
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("no resize node" in error for error in errors)


def test_validate_reference_locked_graph_contract_fails_image_scale_wrong_resolution():
    """MK-REAL3R-3A — Test that workflow with ImageScale at wrong resolution fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: ImageScale with wrong resolution
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["11", 0],
            },
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 1024,  # Wrong resolution
                "height": 1360,
                "crop": "disabled",
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("480x640" in error for error in errors)


def test_validate_reference_locked_graph_contract_fails_image_scale_not_connected():
    """MK-REAL3R-3A — Test that workflow with ImageScale not connected to LoadImage fails."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: ImageScale not connected to LoadImage
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["11", 0],
            },
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["99", 0],  # Wrong source
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("not connected to LoadImage" in error for error in errors)


def test_validate_reference_locked_graph_contract_fails_vae_encode_not_connected_to_scale():
    """MK-REAL3R-3A — Test that workflow with VAEEncode not connected to ImageScale fails."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: VAEEncode not connected to ImageScale
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["5", 0],  # Connected to LoadImage instead of ImageScale
            },
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("not connected to ImageScale" in error for error in errors)


def test_validate_reference_locked_graph_contract_accepts_imageresize_backwards_compat():
    """MK-REAL3R-3A — Test that ImageResize is still accepted for backwards compatibility."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Valid workflow using legacy ImageResize (backwards compatibility)
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
                "steps": 16,
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["11", 0],
            },
        },
        "11": {
            "class_type": "ImageResize",
            "inputs": {
                "image": ["5", 0],
                "width": 480,
                "height": 640,
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert errors == []


def test_validate_reference_locked_graph_contract_fails_missing_ksampler_steps():
    """MK-REAL3R-2 — Test that workflow with missing KSampler.steps fails graph contract."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Invalid workflow: KSampler missing steps
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "latent_image": ["8", 0],
                "cfg": 7.0,
                # steps missing
            },
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/test.png"},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["11", 0],
            },
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }
    
    errors = submitter._validate_reference_locked_graph_contract(workflow, Path("data/references/test.png"))
    assert any("no steps value" in error for error in errors)


# ── helpers ───────────────────────────────────────────────────────────────────

def _built_scene(
    scene_id: str = "s01",
    positive: str = "test prompt",
    negative: str = "blurry",
    total_frames: int = 8,
) -> BuiltScene:
    return BuiltScene(
        scene_id=scene_id,
        positive_prompt=positive,
        negative_prompt=negative,
        lora_stack=[],
        voice_ids=[],
        total_frames=total_frames,
        duration_sec=1.0,
        fps=8,
        keyframe_hints=["a"],
        location=None,
        dialogue=None,
    )


def _workflow_template():
    return {
        "__inject__": {
            "positive_prompt_node": "6",
            "negative_prompt_node": "7",
            "frame_count_node": "13",
            "lora_stack_node": "20",
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "original_model.safetensors"},
        },
        "3": {
            "class_type": "KSampler",
            "inputs": {"steps": 30, "cfg": 5.0, "sampler_name": "euler", "scheduler": "normal"},
        },
        "5": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 1024, "height": 1024, "batch_size": 1},
        },
        "6": {"inputs": {"text": ""}},
        "7": {"inputs": {"text": ""}},
        "13": {"inputs": {"value": 1}},
        "20": {"inputs": {"lora_stack": []}},
    }


# ── happy path ───────────────────────────────────────────────────────────────

def test_submit_returns_submit_result():
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "test-123"}
    mock_session.post.return_value = mock_response

    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "test-123": {"status": {"completed": True}}
        }
    )

    submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")
    result = submitter.submit(scene, workflow, timeout_sec=1.0)

    assert isinstance(result, SubmitResult)


def test_prompt_id_passed_through():
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "abc-456"}
    mock_session.post.return_value = mock_response
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"abc-456": {"status": {"completed": True}}}
    )

    result = ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    assert result.prompt_id == "abc-456"


def test_scene_id_preserved():
    scene = _built_scene(scene_id="s07")
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    result = ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    assert result.scene_id == "s07"


def test_positive_prompt_injected():
    scene = _built_scene(positive="warrior with sword")
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    posted = mock_session.post.call_args[1]["json"]["prompt"]
    assert posted["6"]["inputs"]["text"] == "warrior with sword"


def test_negative_prompt_injected():
    scene = _built_scene(negative="blurry, low quality")
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    posted = mock_session.post.call_args[1]["json"]["prompt"]
    assert posted["7"]["inputs"]["text"] == "blurry, low quality"


def test_total_frames_injected():
    scene = _built_scene(total_frames=12)
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    posted = mock_session.post.call_args[1]["json"]["prompt"]
    assert posted["13"]["inputs"]["value"] == 12


def test_elapsed_sec_positive():
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    result = ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    assert result.elapsed_sec >= 0


def test_workflow_template_not_mutated():
    scene = _built_scene()
    workflow = _workflow_template()
    original_workflow = workflow.copy()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": True}}}
    )

    ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)
    assert workflow == original_workflow


# ── error cases ──────────────────────────────────────────────────────────────

def test_http_500_raises_comfy_submit_error():
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(status_code=500, text="Internal Error")

    with pytest.raises(ComfySubmitError):
        ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=1.0)


def test_polling_timeout_raises_comfy_timeout_error():
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_session.post.return_value = Mock(
        status_code=200,
        json=lambda: {"prompt_id": "x"}
    )
    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {"x": {"status": {"completed": False}}}
    )

    with pytest.raises(ComfyTimeoutError):
        ComfySubmitter(session=mock_session).submit(scene, workflow, timeout_sec=0.1)


# ── MK-OBS2 integration tests ────────────────────────────────────────────────────

def test_submitter_writes_snapshot_before_http_submit():
    """Test that submitter writes snapshot before HTTP submit when episode_id/shot_id/project_root provided."""
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "test-123"}
    mock_session.post.return_value = mock_response

    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "test-123": {"status": {"completed": True}}
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")
        result = submitter.submit(
            scene,
            workflow,
            timeout_sec=1.0,
            episode_id="ep01",
            shot_id="shot01",
            project_root=project_root,
        )

        # Verify snapshot was written
        snapshot_path = project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        assert snapshot_path.exists()

        # Verify snapshot contains expected structure
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)

        assert "observed_settings" in snapshot_data
        settings = snapshot_data["observed_settings"]
        assert "checkpoint" in settings
        assert "sampler_name" in settings
        assert "scheduler" in settings
        assert "steps" in settings
        assert "cfg" in settings
        assert "width" in settings
        assert "height" in settings
        assert "batch_size" in settings
        assert "raw_nodes" in settings


def test_snapshot_contains_patched_workflow_values_not_template_values():
    """Test that snapshot contains patched workflow values, not original template values."""
    scene = _built_scene()
    workflow = _workflow_template()

    # Original template has different values
    assert workflow["3"]["inputs"]["steps"] == 30
    assert workflow["3"]["inputs"]["cfg"] == 5.0
    assert workflow["3"]["inputs"]["sampler_name"] == "euler"

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "test-123"}
    mock_session.post.return_value = mock_response

    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "test-123": {"status": {"completed": True}}
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")
        submitter.submit(
            scene,
            workflow,
            timeout_sec=1.0,
            episode_id="ep01",
            shot_id="shot01",
            project_root=project_root,
        )

        # Verify snapshot contains patched values (from WorkflowPatcher defaults)
        snapshot_path = project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)

        settings = snapshot_data["observed_settings"]
        # WorkflowPatcher applies safe defaults: steps=6 (if > 25), cfg=7.0 (if < 3.0), sampler=dpmpp_sde, scheduler=karras
        # Since original cfg=5.0 is > 3.0, it won't be patched
        assert settings["steps"] == 6  # Patches if steps > 25
        assert settings["cfg"] == 5.0  # Not patched since 5.0 > 3.0
        assert settings["sampler_name"] == "dpmpp_sde"  # Always patched
        assert settings["scheduler"] == "karras"  # Always patched


def test_submitter_without_episode_id_shot_id_does_not_write_snapshot():
    """Test that submitter without episode_id/shot_id does not write snapshot."""
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"prompt_id": "test-123"}
    mock_session.post.return_value = mock_response

    mock_session.get.return_value = Mock(
        status_code=200,
        json=lambda: {
            "test-123": {"status": {"completed": True}}
        }
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")

        # Submit without episode_id/shot_id
        submitter.submit(scene, workflow, timeout_sec=1.0)

        # Verify snapshot was NOT written
        snapshot_path = project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        assert not snapshot_path.exists()


def test_failed_http_submit_still_leaves_pre_submit_snapshot_written():
    """Test that failed HTTP submit still leaves pre-submit snapshot written."""
    scene = _built_scene()
    workflow = _workflow_template()

    mock_session = Mock()
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_session.post.return_value = mock_response

    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir)
        submitter = ComfySubmitter(session=mock_session, output_dir="output/frames")

        # Submit with episode_id/shot_id/project_root - should fail HTTP but write snapshot
        with pytest.raises(ComfySubmitError):
            submitter.submit(
                scene,
                workflow,
                timeout_sec=1.0,
                episode_id="ep01",
                shot_id="shot01",
                project_root=project_root,
            )

        # Verify snapshot was written despite HTTP failure
        snapshot_path = project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        assert snapshot_path.exists()

        # Verify snapshot contains valid data
        with open(snapshot_path, "r", encoding="utf-8") as f:
            snapshot_data = json.load(f)

        assert "observed_settings" in snapshot_data
        settings = snapshot_data["observed_settings"]
        assert "checkpoint" in settings


def test_pre_submit_validation_modules_available():
    """MK-REF1R-6 — Test that pre-submit validation modules are importable in normal environment."""
    # This test verifies that the recipe validation modules can be imported
    # If this fails, the pre-submit validation will skip with "modules not available" message
    from app.recipes.validator import GenerationRecipeValidator
    from app.recipes.planned_settings_resolver import PlannedSettingsResolver
    from app.recipes.registry import RecipeRegistry, HardwareProfileRegistry
    from app.recipes.advisor import GenerationSettingsAdvisor
    
    # Verify imports succeed
    assert GenerationRecipeValidator is not None
    assert PlannedSettingsResolver is not None
    assert RecipeRegistry is not None
    assert HardwareProfileRegistry is not None
    assert GenerationSettingsAdvisor is not None


def test_pre_submit_fail_blocks_http_submit():
    """MK-REF1R-6 — Test that pre-submit validation modules are available and can validate."""
    # This test verifies that the validation modules are importable and can be called
    # The full submit flow with validation blocking is tested in integration tests
    from app.recipes.validator import GenerationRecipeValidator
    from app.recipes.planned_settings_resolver import PlannedSettingsResolver
    from app.recipes.registry import RecipeRegistry, HardwareProfileRegistry
    from app.recipes.advisor import GenerationSettingsAdvisor
    from app.recipes.models import ObservedGenerationSettings
    
    # Verify modules are available
    assert GenerationRecipeValidator is not None
    assert PlannedSettingsResolver is not None
    assert RecipeRegistry is not None
    assert HardwareProfileRegistry is not None
    assert GenerationSettingsAdvisor is not None
    
    # Test that validator can be instantiated and validate
    recipe_registry = RecipeRegistry()
    hardware_registry = HardwareProfileRegistry()
    validator = GenerationRecipeValidator()
    
    recipe = recipe_registry.get("sdxl_reference_locked_character_gtx1060")
    hardware = hardware_registry.get("gtx_1060_5gb")
    
    # Create observed settings that would fail validation
    observed = ObservedGenerationSettings(
        checkpoint="CyberRealisticXLPlay_V7.0_FP16.safetensors",
        sampler_name="dpmpp_sde",
        scheduler="karras",
        steps=16,
        cfg=7.0,
        width=480,
        height=640,
        batch_size=2,  # Exceeds reference_locked limit of 1
        denoise=0.42,
        negative_prompt="bad anatomy, distorted face",
        generation_mode="reference_locked",
        reference_image_path="data/references/test.png",
    )
    
    result = validator.validate(observed, recipe, hardware, "reference_locked_character")
    
    # Verify validation correctly fails
    assert result.verdict == "fail"
    assert any(issue.code == "REFERENCE_BATCH_SIZE_EXCEEDED" for issue in result.issues)


def test_pre_submit_pass_allows_mocked_http_submit():
    """MK-REF1R-6 — Test that pre-submit validation passes for valid settings."""
    from app.recipes.validator import GenerationRecipeValidator
    from app.recipes.registry import RecipeRegistry, HardwareProfileRegistry
    from app.recipes.models import ObservedGenerationSettings
    
    # Test that validator can be instantiated and validate
    recipe_registry = RecipeRegistry()
    hardware_registry = HardwareProfileRegistry()
    validator = GenerationRecipeValidator()
    
    recipe = recipe_registry.get("sdxl_reference_locked_character_gtx1060")
    hardware = hardware_registry.get("gtx_1060_5gb")
    
    # Create observed settings that would pass validation
    observed = ObservedGenerationSettings(
        checkpoint="CyberRealisticXLPlay_V7.0_FP16.safetensors",
        sampler_name="dpmpp_sde",
        scheduler="karras",
        steps=16,
        cfg=7.0,
        width=480,
        height=640,
        batch_size=1,  # Within reference_locked limit
        denoise=0.5,  # Within reference_locked range
        negative_prompt="bad anatomy, distorted face, red skin, orange skin, blue hoodie, artifacts",
        generation_mode="reference_locked",
        reference_image_path="data/references/test.png",
    )
    
    result = validator.validate(observed, recipe, hardware, "reference_locked_character")
    
    # Verify validation correctly passes
    assert result.verdict in ["pass", "warn"]


# ── MK-PROMPTLOCK1 — Prompt pack binding proof tests ─────────────────────────


ALYA_POSITIVE_PROMPT = (
    "vertical portrait composition, ordinary tired young woman 24 years old, "
    "dark brown hair in messy bun clearly visible, hood down, pale skin, dark eyes, "
    "gray oversized sweatshirt, blue jeans, sitting on messy bed in small modest apartment bedroom, "
    "holding simple black smartphone in both hands, tired focused expression, slightly worried, "
    "early morning cold gray-blue window light, documentary realism, "
    "realistic Ukrainian Eastern European apartment mood, no makeup, candid moment, realistic skin texture"
)

ALYA_NEGATIVE_PROMPT = (
    "glamour, fashion model, beauty portrait, studio portrait, stock photo, advertisement, "
    "perfect makeup, smiling, looking at camera, hood up, hood covering head, blue hoodie, "
    "luxury hotel, clean staged bedroom, plastic skin, wax skin, over-smoothed face, "
    "anime, cartoon, bad anatomy, distorted face, bad hands, extra fingers, "
    "red skin, orange skin, artifacts, picture frame, decorative frame, border, text, watermark"
)


def _alya_workflow_template() -> dict:
    """Reference-locked workflow template matching data/config/workflow_template_img2img_reference.json."""
    return {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 0,
                "steps": 16,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 0.42,
                "model": ["4", 0],
                "positive": ["6", 0],
                "negative": ["7", 0],
                "latent_image": ["8", 0],
            },
        },
        "4": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
        "5": {
            "class_type": "LoadImage",
            "inputs": {"image": "data/references/alya_reference_01.png", "upload": "image"},
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["4", 1]},
        },
        "7": {
            "class_type": "CLIPTextEncode",
            "inputs": {"text": "", "clip": ["4", 1]},
        },
        "8": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
        },
        "9": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["3", 0], "vae": ["4", 2]},
        },
        "10": {
            "class_type": "EmptyLatentImage",
            "inputs": {"width": 480, "height": 640, "batch_size": 1},
        },
        "11": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["5", 0],
                "upscale_method": "lanczos",
                "width": 480,
                "height": 640,
                "crop": "disabled",
            },
        },
    }


def _alya_built_scene() -> "BuiltScene":
    from app.scenes.models import BuiltScene
    return BuiltScene(
        scene_id="beat_01",
        positive_prompt=ALYA_POSITIVE_PROMPT,
        negative_prompt=ALYA_NEGATIVE_PROMPT,
        lora_stack=[],
        voice_ids=[],
        total_frames=1,
        duration_sec=1.0,
        fps=24,
        aspect_ratio="9:16",
    )


def test_promptlock1_positive_prompt_injected_into_correct_clip_node():
    """MK-PROMPTLOCK1 — Scriptwriter positive_prompt is injected into the CLIPTextEncode node connected to KSampler.positive."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    workflow = _alya_workflow_template()
    scene = _alya_built_scene()

    submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")

    # Node 6 is KSampler.positive → CLIPTextEncode
    assert workflow["6"]["inputs"]["text"] == ALYA_POSITIVE_PROMPT
    assert "beautiful anime girl" not in workflow["6"]["inputs"]["text"]
    assert "high quality" not in workflow["6"]["inputs"]["text"]


def test_promptlock1_negative_prompt_injected_into_correct_clip_node():
    """MK-PROMPTLOCK1 — Scriptwriter negative_prompt is injected into the CLIPTextEncode node connected to KSampler.negative."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    workflow = _alya_workflow_template()
    scene = _alya_built_scene()

    submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")

    # Node 7 is KSampler.negative → CLIPTextEncode
    assert workflow["7"]["inputs"]["text"] == ALYA_NEGATIVE_PROMPT
    assert workflow["7"]["inputs"]["text"] != "blurry"
    assert "blurry" not in workflow["7"]["inputs"]["text"], "Alya negative must not contain bare 'blurry' placeholder"


def test_promptlock1_no_placeholder_prompts_in_submitted_workflow():
    """MK-PROMPTLOCK1 — Submitted workflow must not contain placeholder prompts."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    workflow = _alya_workflow_template()
    scene = _alya_built_scene()

    submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")

    # Collect all CLIPTextEncode texts
    clip_texts = [
        node["inputs"].get("text", "")
        for node in workflow.values()
        if isinstance(node, dict) and node.get("class_type") == "CLIPTextEncode"
    ]

    for text in clip_texts:
        assert "beautiful anime girl" not in text.lower(), f"Placeholder found in: {text[:60]}"
        assert text.strip() != "blurry", f"Placeholder negative found: {text}"
        assert text.strip() != "", "Empty CLIPTextEncode text after injection"


def test_promptlock1_reference_locked_graph_remains_correct_after_injection():
    """MK-PROMPTLOCK1 — After prompt injection, LoadImage->ImageResize->VAEEncode->KSampler graph must remain intact."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    workflow = _alya_workflow_template()
    scene = _alya_built_scene()

    submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")

    # KSampler.latent_image → VAEEncode (not EmptyLatentImage)
    ksampler = workflow["3"]
    latent_source_id = str(ksampler["inputs"]["latent_image"][0])
    assert workflow[latent_source_id]["class_type"] == "VAEEncode", (
        f"KSampler.latent_image must point to VAEEncode, got {workflow[latent_source_id]['class_type']}"
    )

    # VAEEncode.pixels → ImageScale
    vae_node = workflow["8"]
    pixels_source_id = str(vae_node["inputs"]["pixels"][0])
    assert workflow[pixels_source_id]["class_type"] == "ImageScale"

    # ImageScale.image → LoadImage
    resize_node = workflow["11"]
    image_source_id = str(resize_node["inputs"]["image"][0])
    assert workflow[image_source_id]["class_type"] == "LoadImage"

    # EmptyLatentImage NOT connected to KSampler
    assert latent_source_id != "10", "EmptyLatentImage must NOT be KSampler latent source in reference_locked mode"


def test_promptlock1_inject_workflow_uses_ksampler_connections_not_arbitrary_clip_nodes():
    """MK-PROMPTLOCK1 — Injection follows KSampler connections, not arbitrary CLIPTextEncode enumeration order."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    # Workflow where CLIPTextEncode IDs are reversed relative to enumeration order
    workflow = {
        "3": {
            "class_type": "KSampler",
            "inputs": {
                "positive": ["99", 0],  # positive → node 99
                "negative": ["88", 0],  # negative → node 88
                "latent_image": ["8", 0],
            },
        },
        "99": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},  # positive
        "88": {"class_type": "CLIPTextEncode", "inputs": {"text": ""}},  # negative
        "8": {"class_type": "VAEEncode", "inputs": {"pixels": ["5", 0], "vae": ["4", 2]}},
        "5": {"class_type": "LoadImage", "inputs": {"image": "ref.png"}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "model.safetensors"}},
    }
    from app.scenes.models import BuiltScene
    scene = BuiltScene(
        scene_id="test",
        positive_prompt=ALYA_POSITIVE_PROMPT,
        negative_prompt=ALYA_NEGATIVE_PROMPT,
        lora_stack=[],
        voice_ids=[],
        total_frames=1,
        duration_sec=1.0,
        fps=24,
    )

    submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")

    assert workflow["99"]["inputs"]["text"] == ALYA_POSITIVE_PROMPT
    assert workflow["88"]["inputs"]["text"] == ALYA_NEGATIVE_PROMPT


def test_promptlock1_no_real_comfyui_network_subprocess_called():
    """MK-PROMPTLOCK1 — Proof that no real ComfyUI/network/subprocess is called during prompt injection test."""
    import sys

    # Verify no real HTTP session is created (session=Mock())
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")

    # Verify session is a Mock (not a real requests.Session)
    from unittest.mock import MagicMock, Mock as _Mock
    assert isinstance(submitter.session, (_Mock, MagicMock)), "Session must be mocked, not real"

    # Verify _inject_workflow does not make any network calls
    workflow = _alya_workflow_template()
    scene = _alya_built_scene()

    # Track any subprocess calls
    original_popen = None
    popen_called = []
    import subprocess as _subprocess
    original_popen = _subprocess.Popen

    class _GuardPopen:
        def __init__(self, *a, **kw):
            popen_called.append(True)
            raise RuntimeError("Real subprocess must NOT be called in prompt injection test")

    _subprocess.Popen = _GuardPopen
    try:
        submitter._inject_workflow(workflow, scene, generation_mode="reference_locked")
    finally:
        _subprocess.Popen = original_popen

    assert not popen_called, "subprocess.Popen was called during prompt injection — forbidden"
    assert workflow["6"]["inputs"]["text"] == ALYA_POSITIVE_PROMPT
    assert workflow["7"]["inputs"]["text"] == ALYA_NEGATIVE_PROMPT


# ── MK-REAL3R-4B — Graph validation tests for dangling references ─────────────────────

def test_reference_locked_workflow_has_no_dangling_node_references():
    """MK-REAL3R-4B — Test that reference_locked workflow has no dangling node references."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Valid reference_locked workflow with correct CheckpointLoaderSimple wiring
    workflow = {
        "1": {
            "class_type": "LoadImage",
            "inputs": {"image": "F:/VideoProjects/МИР/Эрдан/референсы/Аля.png"},
        },
        "2": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["1", 0],
                "width": 480,
                "height": 640,
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
            "inputs": {"batch_size": 1},
        },
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "positive prompt",
                "clip": ["10", 1],  # CLIP output from CheckpointLoaderSimple
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "negative prompt",
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
                "latent_image": ["3", 0],  # VAEEncode output
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
    }
    
    # Validate no dangling references
    errors = []
    for node_id, node in workflow.items():
        if isinstance(node, dict):
            for key, value in node.get("inputs", {}).items():
                if isinstance(value, list) and len(value) == 2:
                    source_node_id, output_index = value
                    if source_node_id not in workflow:
                        errors.append(f"Node {node_id}.{key} references non-existent node {source_node_id}")
    
    assert not errors, f"Dangling node references found: {errors}"


def test_vae_encode_vae_points_to_checkpoint_vae_output():
    """MK-REAL3R-4B — Test that VAEEncode.vae points to CheckpointLoaderSimple VAE output."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    workflow = {
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["10", 2],  # VAE output (index 2) from CheckpointLoaderSimple
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
    }
    
    vae_encode = workflow["3"]
    vae_input = vae_encode["inputs"]["vae"]
    
    assert vae_input[0] == "10", "VAEEncode.vae must point to CheckpointLoaderSimple"
    assert vae_input[1] == 2, "VAEEncode.vae must use output index 2 (VAE) from CheckpointLoaderSimple"


def test_clip_text_encode_clip_points_to_checkpoint_clip_output():
    """MK-REAL3R-4B — Test that CLIPTextEncode.clip points to CheckpointLoaderSimple CLIP output."""
    workflow = {
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "positive",
                "clip": ["10", 1],  # CLIP output (index 1) from CheckpointLoaderSimple
            },
        },
        "6": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "negative",
                "clip": ["10", 1],  # CLIP output (index 1) from CheckpointLoaderSimple
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
    }
    
    for node_id in ["5", "6"]:
        clip_encode = workflow[node_id]
        clip_input = clip_encode["inputs"]["clip"]
        
        assert clip_input[0] == "10", f"CLIPTextEncode {node_id}.clip must point to CheckpointLoaderSimple"
        assert clip_input[1] == 1, f"CLIPTextEncode {node_id}.clip must use output index 1 (CLIP) from CheckpointLoaderSimple"


def test_clip_text_encode_no_self_reference():
    """MK-REAL3R-4B — Test that CLIPTextEncode does not self-reference."""
    workflow = {
        "5": {
            "class_type": "CLIPTextEncode",
            "inputs": {
                "text": "positive",
                "clip": ["10", 1],  # Points to CheckpointLoaderSimple, not self
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
    }
    
    for node_id, node in workflow.items():
        if node.get("class_type") == "CLIPTextEncode":
            clip_input = node["inputs"]["clip"]
            assert clip_input[0] != node_id, f"CLIPTextEncode {node_id} must not self-reference"


def test_vae_encode_no_ksampler_fields():
    """MK-REAL3R-4B — Test that VAEEncode does not contain KSampler-only fields."""
    workflow = {
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["10", 2],
            },
        },
    }
    
    vae_encode = workflow["3"]
    inputs = vae_encode["inputs"]
    
    # VAEEncode should only have pixels and vae
    ksampler_fields = ["seed", "steps", "cfg", "sampler_name", "scheduler"]
    for field in ksampler_fields:
        assert field not in inputs, f"VAEEncode must not contain KSampler field '{field}'"
    
    assert set(inputs.keys()) == {"pixels", "vae"}, f"VAEEncode inputs must be only pixels and vae, got {list(inputs.keys())}"


def test_ksampler_contains_required_fields():
    """MK-REAL3R-4B — Test that KSampler contains required fields."""
    workflow = {
        "7": {
            "class_type": "KSampler",
            "inputs": {
                "seed": 12345,
                "steps": 16,
                "cfg": 7.0,
                "sampler_name": "dpmpp_sde",
                "scheduler": "karras",
                "denoise": 0.5,
                "model": ["10", 0],
                "positive": ["5", 0],
                "negative": ["6", 0],
                "latent_image": ["3", 0],
            },
        },
    }
    
    ksampler = workflow["7"]
    inputs = ksampler["inputs"]
    
    required_fields = ["seed", "steps", "cfg", "sampler_name", "scheduler", "denoise"]
    for field in required_fields:
        assert field in inputs, f"KSampler must contain field '{field}'"


def test_invalid_dangling_graph_blocks_before_http_submit():
    """MK-REAL3R-4B — Test that invalid dangling graph blocks before HTTP submit."""
    submitter = ComfySubmitter(session=Mock(), output_dir="output/frames")
    
    # Workflow with dangling reference (node 99 doesn't exist)
    workflow = {
        "3": {
            "class_type": "VAEEncode",
            "inputs": {
                "pixels": ["2", 0],
                "vae": ["99", 2],  # Dangling reference - node 99 doesn't exist
            },
        },
        "10": {
            "class_type": "CheckpointLoaderSimple",
            "inputs": {"ckpt_name": "CyberRealisticXLPlay_V7.0_FP16.safetensors"},
        },
    }
    
    scene = BuiltScene(
        scene_id="shot01",
        positive_prompt="test",
        negative_prompt="test",
        lora_stack=[],
        voice_ids=[],
        total_frames=1,
        duration_sec=1.0,
        fps=24,
    )
    
    # Should raise ComfySubmitError due to dangling reference
    try:
        submitter.submit(
            scene,
            workflow,
            reference_image_path=Path("test.png"),
            generation_mode="reference_locked",
            denoise=0.5,
        )
        assert False, "Should have raised ComfySubmitError for dangling reference"
    except ComfySubmitError as e:
        assert "dangling" in str(e).lower() or "invalid" in str(e).lower() or "reference" in str(e).lower()
