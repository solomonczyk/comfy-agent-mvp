"""Tests for ObservedSettingsResolver."""
import json
import tempfile
from pathlib import Path

import pytest

from app.recipes.settings_resolver import ObservedSettingsResolver
from app.recipes.models import ObservedGenerationSettings


class TestObservedSettingsResolver:
    """Test ObservedSettingsResolver."""

    def test_returns_none_when_no_settings_file_exists(self):
        """Test that resolver returns None when no settings file exists."""
        with tempfile.TemporaryDirectory() as temp_dir:
            resolver = ObservedSettingsResolver(temp_dir)
            result = resolver.resolve_for_shot("ep01", "shot01")
            assert result is None

    def test_loads_direct_settings_format(self):
        """Test that resolver loads direct settings format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create settings file in output/control (highest priority)
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            settings_data = {
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "steps": 20,
                "cfg": 7.0,
                "width": 480,
                "height": 640,
                "batch_size": 2,
                "negative_prompt": "bad anatomy, distorted face",
            }
            
            settings_file = control_dir / "ep01_shot01_observed_settings.json"
            settings_file.write_text(json.dumps(settings_data))
            
            resolver = ObservedSettingsResolver(temp_dir)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.checkpoint == "realvisxlV50_v50Bakedvae.safetensors"
            assert result.steps == 20
            assert result.cfg == 7.0

    def test_loads_wrapped_observed_settings_format(self):
        """Test that resolver loads wrapped observed_settings format."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create settings file in output/control (highest priority)
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            settings_data = {
                "observed_settings": {
                    "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                    "sampler_name": "dpmpp_2m",
                    "scheduler": "karras",
                    "steps": 20,
                    "cfg": 7.0,
                    "width": 480,
                    "height": 640,
                    "batch_size": 2,
                    "negative_prompt": "bad anatomy, distorted face",
                },
                "raw_nodes": {},
            }
            
            settings_file = control_dir / "ep01_shot01_observed_settings.json"
            settings_file.write_text(json.dumps(settings_data))
            
            resolver = ObservedSettingsResolver(temp_dir)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.checkpoint == "realvisxlV50_v50Bakedvae.safetensors"
            assert result.steps == 20
            assert result.cfg == 7.0

    def test_resolution_priority_prefers_output_control_over_other_paths(self):
        """Test that resolution priority prefers output/control over other paths."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create settings file in data/observed_settings (lowest priority)
            obs_dir = temp_path / "data" / "observed_settings"
            obs_dir.mkdir(parents=True)
            
            low_priority_data = {
                "checkpoint": "low_priority_checkpoint",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "steps": 10,
                "cfg": 5.0,
            }
            
            low_priority_file = obs_dir / "ep01_shot01.json"
            low_priority_file.write_text(json.dumps(low_priority_data))
            
            # Create settings file in output/control (highest priority)
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            high_priority_data = {
                "checkpoint": "high_priority_checkpoint",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                "steps": 20,
                "cfg": 7.0,
            }
            
            high_priority_file = control_dir / "ep01_shot01_observed_settings.json"
            high_priority_file.write_text(json.dumps(high_priority_data))
            
            resolver = ObservedSettingsResolver(temp_dir)
            result = resolver.resolve_for_shot("ep01", "shot01")
            
            assert result is not None
            assert result.checkpoint == "high_priority_checkpoint"
            assert result.steps == 20

    def test_invalid_json_raises_clear_valueerror(self):
        """Test that invalid JSON raises clear ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create invalid JSON file
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            settings_file = control_dir / "ep01_shot01_observed_settings.json"
            settings_file.write_text("{invalid json")
            
            resolver = ObservedSettingsResolver(temp_dir)
            
            with pytest.raises(ValueError) as exc_info:
                resolver.resolve_for_shot("ep01", "shot01")
            
            assert "Invalid JSON" in str(exc_info.value)

    def test_invalid_structure_raises_clear_valueerror(self):
        """Test that invalid structure raises clear ValueError."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create JSON with invalid structure
            control_dir = temp_path / "output" / "control"
            control_dir.mkdir(parents=True)
            
            # Missing required field (steps)
            settings_data = {
                "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
                "sampler_name": "dpmpp_2m",
                "scheduler": "karras",
                # steps is missing
                "cfg": 7.0,
            }
            
            settings_file = control_dir / "ep01_shot01_observed_settings.json"
            settings_file.write_text(json.dumps(settings_data))
            
            resolver = ObservedSettingsResolver(temp_dir)
            
            # This should not raise - from_dict should handle missing fields gracefully
            result = resolver.resolve_for_shot("ep01", "shot01")
            assert result is not None
            assert result.steps is None
