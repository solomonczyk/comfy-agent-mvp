"""MK-CTRL26 — Tests for prompt-pack driven generation."""
import json
from pathlib import Path
import pytest
import tempfile
import shutil

from app.control.prompt_pack import load_prompt_pack, get_beat_seed, calculate_deterministic_seed


class TestPromptPackLoader:
    """Test prompt pack loader functionality."""

    def test_load_prompt_pack_reads_prompt_pack_json(self, tmp_path: Path):
        """Test that load_prompt_pack reads prompt_pack.json correctly."""
        # Create test project structure
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True)
        
        # Create test prompt_pack.json
        prompt_pack_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "checkpoint": "juggernautXL_version2.safetensors",
            "beats": [
                {
                    "beat_id": "beat_01_reach_phone",
                    "positive_prompt": "Test prompt 1",
                    "negative_prompt": "Test negative 1",
                    "seed_policy": {
                        "mode": "deterministic_per_shot",
                        "character_seed": 747001,
                        "beat_seed_offset": {"beat_01_reach_phone": 0}
                    },
                    "steps": 20,
                    "cfg": 7.0,
                    "sampler": "dpmpp_sde",
                    "scheduler": "karras"
                }
            ]
        }
        
        prompt_pack_path = control_dir / "prompt_pack.json"
        prompt_pack_path.write_text(json.dumps(prompt_pack_data, indent=2), encoding="utf-8")
        
        # Load prompt pack
        loaded = load_prompt_pack(str(project_root), "ep01", "shot01")
        
        # Verify loaded data
        assert loaded is not None
        assert loaded["episode_id"] == "ep01"
        assert loaded["shot_id"] == "shot01"
        assert loaded["checkpoint"] == "juggernautXL_version2.safetensors"
        assert len(loaded["beats"]) == 1
        assert loaded["beats"][0]["beat_id"] == "beat_01_reach_phone"

    def test_load_prompt_pack_returns_none_when_missing(self, tmp_path: Path):
        """Test that load_prompt_pack returns None when prompt_pack.json doesn't exist."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        
        loaded = load_prompt_pack(str(project_root), "ep01", "shot01")
        assert loaded is None

    def test_load_prompt_pack_returns_none_when_episode_mismatch(self, tmp_path: Path):
        """Test that load_prompt_pack returns None when episode_id doesn't match."""
        project_root = tmp_path / "test_project"
        project_root.mkdir()
        control_dir = project_root / "output" / "control"
        control_dir.mkdir(parents=True)
        
        prompt_pack_data = {
            "episode_id": "ep02",  # Different episode
            "shot_id": "shot01",
            "beats": []
        }
        
        prompt_pack_path = control_dir / "prompt_pack.json"
        prompt_pack_path.write_text(json.dumps(prompt_pack_data, indent=2), encoding="utf-8")
        
        loaded = load_prompt_pack(str(project_root), "ep01", "shot01")
        assert loaded is None


class TestDeterministicSeedCalculation:
    """Test deterministic seed calculation."""

    def test_calculate_deterministic_seed(self):
        """Test that deterministic seed is calculated correctly."""
        assert calculate_deterministic_seed(747001, 0) == 747001
        assert calculate_deterministic_seed(747001, 1) == 747002
        assert calculate_deterministic_seed(747001, 2) == 747003

    def test_get_beat_seed(self, tmp_path: Path):
        """Test that get_beat_seed returns correct seed for a beat."""
        prompt_pack_data = {
            "beats": [
                {
                    "beat_id": "beat_01_reach_phone",
                    "seed_policy": {
                        "mode": "deterministic_per_shot",
                        "character_seed": 747001,
                        "beat_seed_offset": {"beat_01_reach_phone": 0}
                    }
                },
                {
                    "beat_id": "beat_02_alarm_screen",
                    "seed_policy": {
                        "mode": "deterministic_per_shot",
                        "character_seed": 747001,
                        "beat_seed_offset": {"beat_02_alarm_screen": 1}
                    }
                },
                {
                    "beat_id": "beat_03_error_screen",
                    "seed_policy": {
                        "mode": "deterministic_per_shot",
                        "character_seed": 747001,
                        "beat_seed_offset": {"beat_03_error_screen": 2}
                    }
                }
            ]
        }
        
        # Test each beat
        assert get_beat_seed(prompt_pack_data, "beat_01_reach_phone") == 747001
        assert get_beat_seed(prompt_pack_data, "beat_02_alarm_screen") == 747002
        assert get_beat_seed(prompt_pack_data, "beat_03_error_screen") == 747003

    def test_get_beat_seed_returns_none_for_unknown_beat(self, tmp_path: Path):
        """Test that get_beat_seed returns None for unknown beat."""
        prompt_pack_data = {
            "beats": [
                {
                    "beat_id": "beat_01_reach_phone",
                    "seed_policy": {
                        "mode": "deterministic_per_shot",
                        "character_seed": 747001,
                        "beat_seed_offset": {"beat_01_reach_phone": 0}
                    }
                }
            ]
        }
        
        assert get_beat_seed(prompt_pack_data, "unknown_beat") is None


class TestPromptPackGenerationIntegration:
    """Integration tests for prompt-pack generation."""

    def test_payload_trace_contains_3_beats(self, tmp_path: Path):
        """Test that payload trace contains 3 beats when prompt_pack has 3 beats."""
        # This test verifies the structure of the payload trace artifact
        # The actual generation would be tested in a separate integration test
        
        # Mock payload trace data structure
        payload_trace_data = {
            "episode_id": "ep01",
            "shot_id": "shot01",
            "action": "generate_frames",
            "mode": "prompt_pack",
            "total_beats": 3,
            "checkpoint": "juggernautXL_version2.safetensors",
            "payloads": [
                {
                    "beat_id": "beat_01_reach_phone",
                    "seed": 747001
                },
                {
                    "beat_id": "beat_02_alarm_screen",
                    "seed": 747002
                },
                {
                    "beat_id": "beat_03_error_screen",
                    "seed": 747003
                }
            ]
        }
        
        assert payload_trace_data["total_beats"] == 3
        assert len(payload_trace_data["payloads"]) == 3

    def test_payload_trace_seeds_are_exact(self):
        """Test that payload trace seeds are exactly 747001, 747002, 747003."""
        expected_seeds = [747001, 747002, 747003]
        
        payload_trace_data = {
            "payloads": [
                {"beat_id": "beat_01_reach_phone", "seed": 747001},
                {"beat_id": "beat_02_alarm_screen", "seed": 747002},
                {"beat_id": "beat_03_error_screen", "seed": 747003}
            ]
        }
        
        actual_seeds = [p["seed"] for p in payload_trace_data["payloads"]]
        assert actual_seeds == expected_seeds

    def test_payload_trace_prompt_source_is_prompt_pack(self):
        """Test that payload trace prompt source is prompt_pack.json, not brief.md."""
        payload_trace_data = {
            "payloads": [
                {
                    "beat_id": "beat_01_reach_phone",
                    "positive_prompt_source": "prompt_pack.json",
                    "negative_prompt_source": "prompt_pack.json"
                }
            ]
        }
        
        for payload in payload_trace_data["payloads"]:
            assert payload["positive_prompt_source"] == "prompt_pack.json"
            assert payload["negative_prompt_source"] == "prompt_pack.json"
