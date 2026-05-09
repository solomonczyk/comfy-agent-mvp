"""RC-COMBINE-V2-CONTROLLED-PREVIEW-RENDER-001 — Preview render artifact validation tests.

Tests validation of preview artifacts including existence, readability,
size, SHA-256, and type-specific checks for video, GIF, and contact sheet.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from PIL import Image

from app.timeline.controlled_preview_render import (
    validate_preview_artifact,
    validate_preview_artifacts,
    execute_preview_render,
    run_controlled_preview_render,
)


def _make_control_dir(tmp_path: Path) -> Path:
    control_dir = tmp_path / "output" / "control"
    preview_dir = tmp_path / "output" / "preview"
    assets_dir = tmp_path / "output" / "assets"
    control_dir.mkdir(parents=True, exist_ok=True)
    preview_dir.mkdir(parents=True, exist_ok=True)
    assets_dir.mkdir(parents=True, exist_ok=True)
    return control_dir


def _make_test_asset(tmp_path: Path) -> Path:
    assets_dir = tmp_path / "output" / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (200, 150), color=(50, 120, 200))
    path = assets_dir / "test_asset.png"
    img.save(path)
    return path


class TestSingleArtifactValidation:
    """Tests for validate_preview_artifact on individual artifacts."""

    def test_missing_file(self, tmp_path: Path):
        path = tmp_path / "nonexistent.mp4"
        result = validate_preview_artifact(path, "video")
        assert result["exists"] is False
        assert result["readable"] is False

    def test_empty_file_detected_as_stub(self, tmp_path: Path):
        path = tmp_path / "empty.gif"
        path.write_text("", encoding="utf-8")
        result = validate_preview_artifact(path, "gif")
        assert result["exists"] is True
        assert result["size_bytes_gt_zero"] is False
        assert result["not_stub"] is False

    def test_valid_gif_passes(self, tmp_path: Path):
        img = Image.new("RGB", (50, 50), color=(255, 0, 0))
        path = tmp_path / "test.gif"
        frames = [
            Image.new("RGB", (50, 50), color=(255, 0, 0)),
            Image.new("RGB", (50, 50), color=(0, 255, 0)),
        ]
        frames[0].save(
            path,
            save_all=True,
            append_images=frames[1:],
            duration=100,
            loop=0,
        )
        result = validate_preview_artifact(path, "gif")
        assert result["exists"] is True
        assert result["size_bytes_gt_zero"] is True
        assert result["not_stub"] is True

    def test_sha256_computed(self, tmp_path: Path):
        img = Image.new("RGB", (50, 50), color=(100, 100, 100))
        path = tmp_path / "test.jpg"
        img.save(path, "JPEG")
        result = validate_preview_artifact(path, "image")
        assert result["sha256_present"] is True


class TestPreviewArtifactsValidation:
    """Tests for validate_preview_artifacts on all preview outputs."""

    def test_all_artifacts_valid(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        result = validate_preview_artifacts(preview_dir)

        assert result["preview_gif_valid"] is True
        assert result["contact_sheet_jpg_valid"] is True

    def test_preview_lowres_validation(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        result = validate_preview_artifacts(preview_dir)

        validation = result.get("preview_lowres_mp4", {})
        assert "sha256" in validation or not validation.get("exists")

    def test_gif_has_frame_count(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        gif_path = preview_dir / "preview.gif"

        with Image.open(gif_path) as img:
            assert getattr(img, "n_frames", 0) > 0
            assert img.width > 0
            assert img.height > 0

    def test_contact_sheet_dimensions(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        sheet_path = preview_dir / "contact_sheet.jpg"

        with Image.open(sheet_path) as img:
            assert img.width > 0
            assert img.height > 0

    def test_fake_gif_blocked(self, tmp_path: Path):
        """Verify a fake/stub GIF fails validation."""
        preview_dir = tmp_path / "output" / "preview"
        preview_dir.mkdir(parents=True, exist_ok=True)

        # Create empty file (stub)
        (preview_dir / "preview.gif").write_text("", encoding="utf-8")
        # Create fake MP4
        (preview_dir / "preview_lowres.mp4").write_text("fake mp4", encoding="utf-8")
        # Create a real JPG
        img = Image.new("RGB", (10, 10))
        img.save(preview_dir / "contact_sheet.jpg")

        result = validate_preview_artifacts(preview_dir)
        # GIF is empty -> stub detection
        assert result.get("preview_gif_valid") is False


class TestPreviewArtifactSha256:
    """SHA-256 verification tests for preview artifacts."""

    def test_gif_sha256_computed(self, tmp_path: Path):
        control_dir = _make_control_dir(tmp_path)
        asset = _make_test_asset(tmp_path)
        preview_dir = tmp_path / "output" / "preview"

        execute_preview_render(asset, preview_dir)
        result = validate_preview_artifacts(preview_dir)

        gif_result = result.get("preview_gif", {})
        if gif_result.get("exists"):
            assert gif_result.get("sha256") is not None
            assert len(gif_result["sha256"]) == 64
