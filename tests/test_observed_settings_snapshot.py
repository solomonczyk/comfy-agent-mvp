"""Tests for MK-OBS2 — ObservedSettingsSnapshotWriter."""
from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from app.observability import ObservedSettingsSnapshotWriter


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """Create a temporary project root for testing."""
    return tmp_path


@pytest.fixture
def sample_settings() -> dict:
    """Create sample settings for testing."""
    return {
        "checkpoint": "realvisxlV50_v50Bakedvae.safetensors",
        "sampler_name": "dpmpp_sde",
        "scheduler": "karras",
        "steps": 20,
        "cfg": 7.0,
        "width": 512,
        "height": 512,
        "batch_size": 1,
        "denoise": 0.75,
        "negative_prompt": "blurry, low quality",
        "raw_nodes": {
            "source": "patched_workflow_before_submit",
            "checkpoint_node": "4",
            "ksampler_node": "3",
            "latent_node": "5",
            "negative_prompt_node": "7",
        },
    }


class TestObservedSettingsSnapshotWriter:
    """Test suite for ObservedSettingsSnapshotWriter."""

    def test_path_is_output_control_episode_shot_observed_settings_json(self, temp_project_root):
        """Test that path is output/control/{episode_id}_{shot_id}_observed_settings.json."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)
        path = writer.path_for("ep01", "shot01")

        expected = temp_project_root / "output" / "control" / "ep01_shot01_observed_settings.json"
        assert path == expected

    def test_write_creates_parent_dirs(self, temp_project_root, sample_settings):
        """Test that write creates parent directories."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)
        output_dir = temp_project_root / "output" / "control"

        assert not output_dir.exists()

        writer.write("ep01", "shot01", sample_settings)

        assert output_dir.exists()
        assert output_dir.is_dir()

    def test_write_wraps_observed_settings_json(self, temp_project_root, sample_settings):
        """Test that write writes wrapped observed_settings JSON."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)
        path = writer.write("ep01", "shot01", sample_settings)

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "observed_settings" in data
        assert data["observed_settings"] == sample_settings

    def test_write_does_not_mutate_input_settings_dict(self, temp_project_root, sample_settings):
        """Test that write does not mutate input settings dict."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)
        original_settings = sample_settings.copy()
        original_id = id(sample_settings)

        writer.write("ep01", "shot01", sample_settings)

        # Check that the dict wasn't mutated
        assert sample_settings == original_settings
        assert id(sample_settings) == original_id

    def test_write_overwrites_atomically_on_second_write(self, temp_project_root, sample_settings):
        """Test that write overwrites atomically on second write."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)

        # First write
        path1 = writer.write("ep01", "shot01", sample_settings)
        with open(path1, "r", encoding="utf-8") as f:
            data1 = json.load(f)

        # Modify settings
        modified_settings = sample_settings.copy()
        modified_settings["steps"] = 25

        # Second write
        path2 = writer.write("ep01", "shot01", modified_settings)
        with open(path2, "r", encoding="utf-8") as f:
            data2 = json.load(f)

        # Paths should be the same
        assert path1 == path2

        # Data should be updated
        assert data1["observed_settings"]["steps"] == 20
        assert data2["observed_settings"]["steps"] == 25

    def test_write_creates_human_readable_json_indent_2(self, temp_project_root, sample_settings):
        """Test that write creates human-readable JSON with indent=2."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)
        path = writer.write("ep01", "shot01", sample_settings)

        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check that JSON is formatted with indentation
        assert "{\n  " in content  # JSON with indent=2

    def test_write_raises_valueerror_on_empty_episode_id(self, temp_project_root, sample_settings):
        """Test that write raises ValueError on empty episode_id."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)

        with pytest.raises(ValueError, match="episode_id cannot be empty"):
            writer.write("", "shot01", sample_settings)

    def test_write_raises_valueerror_on_empty_shot_id(self, temp_project_root, sample_settings):
        """Test that write raises ValueError on empty shot_id."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)

        with pytest.raises(ValueError, match="shot_id cannot be empty"):
            writer.write("ep01", "", sample_settings)

    def test_write_with_path_string_project_root(self, sample_settings):
        """Test that write works with string project_root."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ObservedSettingsSnapshotWriter(tmpdir)
            path = writer.write("ep01", "shot01", sample_settings)

            assert path.exists()
            assert path.is_file()

    def test_write_atomic_operation_temp_file_replace(self, temp_project_root, sample_settings):
        """Test that write uses atomic temp file + replace operation."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)

        # Mock Path.replace to verify atomic operation
        original_replace = Path.replace
        replace_called = []

        def mock_replace(self, target):
            replace_called.append((self, target))
            return original_replace(self, target)

        with patch.object(Path, "replace", mock_replace):
            path = writer.write("ep01", "shot01", sample_settings)

        # Verify replace was called
        assert len(replace_called) == 1
        assert replace_called[0][1] == path

        # Verify final file exists
        assert path.exists()

    def test_write_cleanup_temp_file_on_failure(self, temp_project_root, sample_settings):
        """Test that write cleans up temp file on failure."""
        writer = ObservedSettingsSnapshotWriter(temp_project_root)

        # Mock json.dump to raise an exception
        with patch("json.dump", side_effect=IOError("Mock write error")):
            with pytest.raises(IOError):
                writer.write("ep01", "shot01", sample_settings)

        # Verify temp file was cleaned up
        temp_file = temp_project_root / "output" / "control" / "ep01_shot01_observed_settings.json.tmp"
        assert not temp_file.exists()

    def test_path_for_with_string_project_root(self):
        """Test that path_for works with string project_root."""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            writer = ObservedSettingsSnapshotWriter(tmpdir)
            path = writer.path_for("ep01", "shot01")

            expected = Path(tmpdir) / "output" / "control" / "ep01_shot01_observed_settings.json"
            assert path == expected
