"""Tests for MK-OBS2 — WorkflowSettingsExtractor."""
from __future__ import annotations

import pytest

from app.observability import WorkflowSettingsExtractor


class TestWorkflowSettingsExtractor:
    """Test suite for WorkflowSettingsExtractor."""

    def test_extracts_checkpoint_from_checkpointloader(self):
        """Test that extractor extracts checkpoint from CheckpointLoaderSimple."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "realvisxlV50_v50Bakedvae.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["checkpoint"] == "realvisxlV50_v50Bakedvae.safetensors"
        assert settings["raw_nodes"]["checkpoint_node"] == "4"

    def test_extracts_steps_cfg_sampler_scheduler_denoise_from_ksampler(self):
        """Test that extractor extracts steps/cfg/sampler/scheduler/denoise from KSampler."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "steps": 25,
                    "cfg": 8.0,
                    "sampler_name": "dpmpp_sde",
                    "scheduler": "karras",
                    "denoise": 0.75,
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["steps"] == 25
        assert settings["cfg"] == 8.0
        assert settings["sampler_name"] == "dpmpp_sde"
        assert settings["scheduler"] == "karras"
        assert settings["denoise"] == 0.75
        assert settings["raw_nodes"]["ksampler_node"] == "3"

    def test_extracts_width_height_batch_size_from_emptylatent(self):
        """Test that extractor extracts width/height/batch_size from EmptyLatentImage."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 1024, "height": 768, "batch_size": 4},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["width"] == 1024
        assert settings["height"] == 768
        assert settings["batch_size"] == 4
        assert settings["raw_nodes"]["latent_node"] == "5"

    def test_extracts_negative_prompt_from_injected_node(self):
        """Test that extractor extracts negative prompt from injected negative_prompt_node."""
        workflow = {
            "__inject__": {"negative_prompt_node": "7"},
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "blurry, low quality, distorted"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["negative_prompt"] == "blurry, low quality, distorted"
        assert settings["raw_nodes"]["negative_prompt_node"] == "7"

    def test_returns_raw_nodes_with_used_node_ids(self):
        """Test that extractor returns raw_nodes with used node IDs."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert "raw_nodes" in settings
        assert settings["raw_nodes"]["source"] == "patched_workflow_before_submit"
        assert settings["raw_nodes"]["checkpoint_node"] == "4"
        assert settings["raw_nodes"]["ksampler_node"] == "3"
        assert settings["raw_nodes"]["latent_node"] == "5"

    def test_missing_optional_denoise_returns_none(self):
        """Test that missing optional denoise returns None."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler_name": "euler",
                    "scheduler": "karras",
                    # denoise missing
                },
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["denoise"] is None

    def test_missing_required_checkpoint_raises_valueerror(self):
        """Test that missing required CheckpointLoaderSimple raises ValueError."""
        workflow = {
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="No CheckpointLoaderSimple node found"):
            extractor.extract(workflow)

    def test_missing_required_ksampler_raises_valueerror(self):
        """Test that missing required KSampler raises ValueError."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="No KSampler node found"):
            extractor.extract(workflow)

    def test_missing_required_latent_raises_valueerror(self):
        """Test that missing required EmptyLatentImage raises ValueError."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="No EmptyLatentImage node found"):
            extractor.extract(workflow)

    def test_empty_workflow_raises_valueerror(self):
        """Test that empty workflow raises ValueError."""
        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="Workflow must be a non-empty dict"):
            extractor.extract({})

    def test_non_dict_workflow_raises_valueerror(self):
        """Test that non-dict workflow raises ValueError."""
        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="Workflow must be a non-empty dict"):
            extractor.extract(None)

    def test_negative_prompt_fallback_to_clipencode_heuristic(self):
        """Test that negative prompt falls back to CLIPTextEncode heuristic."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "ugly, distorted, low quality"},
            },
            "8": {
                "class_type": "CLIPTextEncode",
                "inputs": {"text": "beautiful masterpiece"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        # Should find the negative prompt based on keyword heuristic
        assert settings["negative_prompt"] == "ugly, distorted, low quality"
        assert settings["raw_nodes"]["negative_prompt_node"] == "7"

    def test_negative_prompt_none_when_not_found(self):
        """Test that negative_prompt is None when not found."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 20, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 512, "height": 512, "batch_size": 1},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow)

        assert settings["negative_prompt"] is None


class TestWorkflowSettingsExtractorReferenceLocked:
    """MK-REAL3R-3A — Tests for reference_locked mode extraction with ImageScale and ImageResize support."""

    def test_extracts_width_height_from_imagescale_in_reference_locked_mode(self):
        """MK-REAL3R-3A — Test that extractor reads width/height from ImageScale in reference_locked mode."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 16, "cfg": 7.0, "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": 0.5},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "data/references/test.png"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
            },
            "10": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 640, "height": 480, "batch_size": 1},
            },
            "11": {
                "class_type": "ImageScale",
                "inputs": {"image": ["5", 0], "upscale_method": "lanczos", "width": 480, "height": 640, "crop": "disabled"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow, generation_mode="reference_locked", reference_image_path="data/references/test.png")

        # Width/height should come from ImageScale (480x640), not EmptyLatentImage (640x480)
        assert settings["width"] == 480
        assert settings["height"] == 640
        # Batch size should come from EmptyLatentImage
        assert settings["batch_size"] == 1

    def test_includes_resize_node_and_image_scale_node_in_raw_nodes_for_reference_locked(self):
        """MK-REAL3R-3A — Test that resize_node and image_scale_node are included in raw_nodes for reference_locked mode."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 16, "cfg": 7.0, "sampler_name": "dpmpp_sde", "scheduler": "karras"},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "data/references/test.png"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
            },
            "11": {
                "class_type": "ImageScale",
                "inputs": {"image": ["5", 0], "upscale_method": "lanczos", "width": 480, "height": 640, "crop": "disabled"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow, generation_mode="reference_locked", reference_image_path="data/references/test.png")

        # Generic resize_node must be present
        assert "resize_node" in settings["raw_nodes"]
        assert settings["raw_nodes"]["resize_node"] == "11"
        # Type-specific image_scale_node must be present for ImageScale
        assert "image_scale_node" in settings["raw_nodes"]
        assert settings["raw_nodes"]["image_scale_node"] == "11"
        # Backwards-compatible image_resize_node must NOT be present for ImageScale
        assert "image_resize_node" not in settings["raw_nodes"]

    def test_includes_resize_node_and_image_resize_node_for_backwards_compat(self):
        """MK-REAL3R-3A — Test that ImageResize backwards compatibility includes image_resize_node in raw_nodes."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 16, "cfg": 7.0, "sampler_name": "dpmpp_sde", "scheduler": "karras"},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "data/references/test.png"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
            },
            "11": {
                "class_type": "ImageResize",
                "inputs": {"image": ["5", 0], "width": 480, "height": 640},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow, generation_mode="reference_locked", reference_image_path="data/references/test.png")

        # Generic resize_node must be present
        assert "resize_node" in settings["raw_nodes"]
        assert settings["raw_nodes"]["resize_node"] == "11"
        # Type-specific image_resize_node must be present for ImageResize
        assert "image_resize_node" in settings["raw_nodes"]
        assert settings["raw_nodes"]["image_resize_node"] == "11"

    def test_reference_locked_mode_requires_resize_node(self):
        """MK-REAL3R-3A — Test that reference_locked mode requires ImageScale or ImageResize node."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 16, "cfg": 7.0},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "data/references/test.png"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["5", 0], "vae": ["4", 2]},
            },
        }

        extractor = WorkflowSettingsExtractor()
        with pytest.raises(ValueError, match="No ImageScale or ImageResize node found"):
            extractor.extract(workflow, generation_mode="reference_locked", reference_image_path="data/references/test.png")

    def test_does_not_read_disconnected_emptylatent_dimensions(self):
        """MK-REAL3R-3A — Test that extractor does not read EmptyLatentImage dimensions when disconnected in reference_locked mode."""
        workflow = {
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "model.safetensors"},
            },
            "3": {
                "class_type": "KSampler",
                "inputs": {"steps": 16, "cfg": 7.0, "sampler_name": "dpmpp_sde", "scheduler": "karras", "denoise": 0.5},
            },
            "5": {
                "class_type": "LoadImage",
                "inputs": {"image": "data/references/test.png"},
            },
            "8": {
                "class_type": "VAEEncode",
                "inputs": {"pixels": ["11", 0], "vae": ["4", 2]},
            },
            # EmptyLatentImage present but with wrong dimensions - should not affect output
            "10": {
                "class_type": "EmptyLatentImage",
                "inputs": {"width": 9999, "height": 9999, "batch_size": 1},
            },
            "11": {
                "class_type": "ImageScale",
                "inputs": {"image": ["5", 0], "upscale_method": "lanczos", "width": 480, "height": 640, "crop": "disabled"},
            },
        }

        extractor = WorkflowSettingsExtractor()
        settings = extractor.extract(workflow, generation_mode="reference_locked", reference_image_path="data/references/test.png")

        # Width/height must come from ImageScale, NOT from disconnected EmptyLatentImage
        assert settings["width"] == 480
        assert settings["height"] == 640
        assert settings["batch_size"] == 1  # Batch size still from EmptyLatentImage

