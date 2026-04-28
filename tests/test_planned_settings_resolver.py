"""Tests for PlannedSettingsResolver."""
import json
import tempfile
from pathlib import Path

import pytest

from app.recipes.planned_settings_resolver import PlannedSettingsResolver
from app.recipes.models import ObservedGenerationSettings


class TestPlannedSettingsResolver:
    """Test PlannedSettingsResolver."""

    def test_returns_none_when_config_unavailable(self):
        """Test that resolver returns None when config is unavailable."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create project structure but no config.json
            (temp_path / "data").mkdir(parents=True)
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is None

    def test_returns_none_when_observed_settings_exist(self):
        """Test that resolver returns None when observed settings exist (ObservedSettingsResolver takes priority)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create observed settings file
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            observed_file = control_dir / "ep01_shot01_observed_settings.json"
            observed_file.write_text(json.dumps({"checkpoint": "observed.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            # Should return None because observed settings exist
            assert result is None

    def test_derives_checkpoint_from_config(self):
        """Test that resolver derives checkpoint from config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with checkpoint
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "realvisxlV50_v50Bakedvae.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.checkpoint == "realvisxlV50_v50Bakedvae.safetensors"

    def test_derives_checkpoint_from_workflow_fallback(self):
        """Test that resolver derives checkpoint from workflow as fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without checkpoint
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({}))
            
            # Create workflow_template.json with CheckpointLoaderSimple
            workflow_file = config_dir / "workflow_template.json"
            workflow_data = {
                "4": {
                    "inputs": {"ckpt_name": "workflow_checkpoint.safetensors"},
                    "class_type": "CheckpointLoaderSimple"
                }
            }
            workflow_file.write_text(json.dumps(workflow_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.checkpoint == "workflow_checkpoint.safetensors"

    def test_derives_steps_from_config(self):
        """Test that resolver derives steps from config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with steps
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "steps": 25
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.steps == 25

    def test_derives_steps_from_workflow_fallback(self):
        """Test that resolver derives steps from workflow as fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without steps
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create workflow_template.json with KSampler
            workflow_file = config_dir / "workflow_template.json"
            workflow_data = {
                "3": {
                    "inputs": {"steps": 30, "cfg": 7.0, "sampler_name": "euler", "scheduler": "karras"},
                    "class_type": "KSampler"
                }
            }
            workflow_file.write_text(json.dumps(workflow_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.steps == 30

    def test_derives_steps_default_fallback(self):
        """Test that resolver uses default steps when config and workflow missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with only checkpoint
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.steps == 20  # DEFAULT_STEPS

    def test_derives_sampler_scheduler_from_config(self):
        """Test that resolver derives sampler_name and scheduler from config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with sampler and scheduler
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras"
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.sampler_name == "dpmpp_2m"
            assert result.scheduler == "karras"

    def test_derives_sampler_scheduler_from_workflow_fallback(self):
        """Test that resolver derives sampler_name and scheduler from workflow as fallback."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without sampler/scheduler
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create workflow_template.json with KSampler
            workflow_file = config_dir / "workflow_template.json"
            workflow_data = {
                "3": {
                    "inputs": {"sampler_name": "dpp_2m", "scheduler": "normal"},
                    "class_type": "KSampler"
                }
            }
            workflow_file.write_text(json.dumps(workflow_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.sampler_name == "dpp_2m"
            assert result.scheduler == "normal"

    def test_derives_9_16_resolution_as_480x640(self):
        """Test that resolver derives 9:16 aspect ratio as 480x640."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with 9:16 aspect ratio
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "aspect_ratio": "9:16"
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.width == 480
            assert result.height == 640

    def test_derives_4_3_resolution_as_640x480(self):
        """Test that resolver derives 4:3 aspect ratio as 640x480."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with 4:3 aspect ratio
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "aspect_ratio": "4:3"
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.width == 640
            assert result.height == 480

    def test_derives_default_9_16_resolution_when_aspect_ratio_missing(self):
        """Test that resolver uses default 9:16 when aspect ratio missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without aspect ratio
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.width == 480
            assert result.height == 640

    def test_derives_batch_size_from_max_frames_per_batch(self):
        """Test that resolver derives batch_size from max_frames_per_batch."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with max_frames_per_batch
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "max_frames_per_batch": 4
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.batch_size == 4

    def test_derives_batch_size_from_prompt_pack_frame_count(self):
        """Test that resolver derives batch_size from prompt_pack frame_count when lower."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with max_frames_per_batch
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "max_frames_per_batch": 4
            }))
            
            # Create prompt_pack with lower frame_count
            prompt_pack_file = temp_path / "prompt_pack.json"
            prompt_pack_data = {
                "frame_count": 2,
                "beat_prompts": []
            }
            prompt_pack_file.write_text(json.dumps(prompt_pack_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            assert result is not None
            assert result.batch_size == 2  # Lower of 4 and 2

    def test_derives_batch_size_default_fallback(self):
        """Test that resolver uses default batch_size when config and prompt_pack missing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without max_frames_per_batch
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.batch_size == 2  # DEFAULT_BATCH_SIZE

    def test_merges_default_negative_and_prompt_pack_negative(self):
        """Test that resolver merges default_negative and prompt_pack negative_prompt."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with default_negative
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "default_negative": "blurry, deformed, bad anatomy"
            }))
            
            # Create prompt_pack with additional negative terms
            prompt_pack_file = temp_path / "prompt_pack.json"
            prompt_pack_data = {
                "beat_prompts": [{
                    "negative_prompt": "watermark, text, logo, cropped"
                }]
            }
            prompt_pack_file.write_text(json.dumps(prompt_pack_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            assert result is not None
            # Should contain both sets of terms
            assert "blurry" in result.negative_prompt
            assert "deformed" in result.negative_prompt
            assert "bad anatomy" in result.negative_prompt
            assert "watermark" in result.negative_prompt
            assert "text" in result.negative_prompt
            assert "logo" in result.negative_prompt
            assert "cropped" in result.negative_prompt

    def test_deduplicates_negative_prompt_terms(self):
        """Test that resolver deduplicates negative_prompt terms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with default_negative
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "default_negative": "blurry, deformed, bad anatomy"
            }))
            
            # Create prompt_pack with overlapping negative terms
            prompt_pack_file = temp_path / "prompt_pack.json"
            prompt_pack_data = {
                "beat_prompts": [{
                    "negative_prompt": "deformed, watermark, text"  # "deformed" is duplicate
                }]
            }
            prompt_pack_file.write_text(json.dumps(prompt_pack_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            assert result is not None
            # Count occurrences of "deformed"
            deformed_count = result.negative_prompt.count("deformed")
            assert deformed_count == 1  # Should appear only once

    def test_returns_raw_nodes_source_summary(self):
        """Test that resolver returns raw_nodes with source summary."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create workflow_template.json
            workflow_file = config_dir / "workflow_template.json"
            workflow_file.write_text(json.dumps({}))
            
            # Create prompt_pack
            prompt_pack_file = temp_path / "prompt_pack.json"
            prompt_pack_file.write_text(json.dumps({"beat_prompts": []}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            assert result is not None
            assert result.raw_nodes is not None
            assert result.raw_nodes["source"] == "planned_settings"
            assert result.raw_nodes["config_path"] is not None
            assert result.raw_nodes["workflow_template_path"] is not None
            assert result.raw_nodes["prompt_pack_path"] is not None

    def test_does_not_mutate_config_file(self):
        """Test that resolver does not mutate config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            original_config = {"checkpoint": "test.safetensors", "steps": 20}
            config_file.write_text(json.dumps(original_config))
            
            # Resolve settings
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            # Verify config file unchanged
            with open(config_file, encoding="utf-8") as f:
                config_after = json.load(f)
            
            assert config_after == original_config

    def test_does_not_mutate_workflow_file(self):
        """Test that resolver does not mutate workflow_template.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create workflow_template.json
            workflow_file = config_dir / "workflow_template.json"
            original_workflow = {"3": {"class_type": "KSampler", "inputs": {"steps": 20}}}
            workflow_file.write_text(json.dumps(original_workflow))
            
            # Resolve settings
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            # Verify workflow file unchanged
            with open(workflow_file, encoding="utf-8") as f:
                workflow_after = json.load(f)
            
            assert workflow_after == original_workflow

    def test_does_not_mutate_prompt_pack_file(self):
        """Test that resolver does not mutate prompt_pack file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            # Create prompt_pack
            prompt_pack_file = temp_path / "prompt_pack.json"
            original_prompt_pack = {"beat_prompts": [{"negative_prompt": "blurry"}]}
            prompt_pack_file.write_text(json.dumps(original_prompt_pack))
            
            # Resolve settings
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            # Verify prompt_pack file unchanged
            with open(prompt_pack_file, encoding="utf-8") as f:
                prompt_pack_after = json.load(f)
            
            assert prompt_pack_after == original_prompt_pack

    def test_derives_cfg_from_config(self):
        """Test that resolver derives cfg from config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with cfg
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "cfg": 8.5
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.cfg == 8.5

    def test_derives_denoise_from_config(self):
        """Test that resolver derives denoise from config.json."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with denoise
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "denoise": 0.6
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.denoise == 0.6

    def test_denoise_none_when_missing_for_txt2img(self):
        """Test that denoise is None when missing (for txt2img/storyboard recipe)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json without denoise
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({"checkpoint": "test.safetensors"}))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.denoise is None

    def test_planned_settings_preserves_incomplete_negative_prompt(self):
        """Test that planned settings with incomplete negative prompt preserves incomplete prompt and does not auto-hide missing terms."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json with incomplete negative prompt (missing some required terms)
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
                "default_negative": "blurry, deformed, bad anatomy"  # Missing: distorted face, red skin, orange skin, blue hoodie, artifacts
            }))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            # Should preserve the incomplete prompt exactly as-is
            assert result.negative_prompt == "blurry, deformed, bad anatomy"
            # Should not auto-add missing terms

    def test_preserves_generation_mode_from_prompt_pack():
        """MK-REF1R-5 — Test that planned settings resolver preserves generation_mode from prompt_pack."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create config.json
            config_dir = temp_path / "data"
            config_dir.mkdir(parents=True)
            config_file = config_dir / "config.json"
            config_file.write_text(json.dumps({
                "checkpoint": "test.safetensors",
            }))
            
            # Create prompt_pack with generation_mode
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            prompt_pack_file = control_dir / "prompt_pack.json"
            prompt_pack_data = {
                "characters": ["Alya"],
                "beats": [],
                "generation_mode": "reference_locked",
                "reference_image_path": "data/references/alya.png",
            }
            prompt_pack_file.write_text(json.dumps(prompt_pack_data))
            
            resolver = PlannedSettingsResolver(temp_path)
            result = resolver.resolve_for_shot("ep01", "shot01", prompt_pack_path=prompt_pack_file)
            
            assert result is not None
            assert result.generation_mode == "reference_locked"
            assert result.reference_image_path == "data/references/alya.png"
