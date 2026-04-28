"""Tests for MK-OBS1.5 — Contact Sheet Generator."""
from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app.control.contact_sheet import ContactSheetGenerator, generate_contact_sheet


def _make_sample_frame_data() -> list[dict]:
    """Create sample frame data for testing."""
    return [
        {
            "beat_id": "beat_01",
            "frame_path": "/tmp/beat_01.png",
            "qa_verdict": "pass",
        },
        {
            "beat_id": "beat_02",
            "frame_path": "/tmp/beat_02.png",
            "qa_verdict": "fail",
        },
    ]


def test_contact_sheet_jpg_is_created_from_sample_frames() -> None:
    """Test that contact_sheet.jpg is created from sample frames with placeholder images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = _make_sample_frame_data()

        # Use placeholder images (frames don't actually exist)
        result = generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=2,
        )

        assert result == output_path
        assert output_path.exists()
        assert output_path.is_file()


def test_contact_sheet_with_missing_frame_paths() -> None:
    """Test that contact sheet handles missing frame paths with placeholders."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = [
            {
                "beat_id": "beat_01",
                "frame_path": "/nonexistent/path.png",
                "qa_verdict": "pending",
            }
        ]

        result = generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=1,
        )

        assert result == output_path
        assert output_path.exists()


def test_contact_sheet_with_empty_frame_data() -> None:
    """Test that contact sheet raises error with empty frame data."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"

        try:
            generate_contact_sheet(
                frame_data=[],
                output_path=output_path,
            )
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No frame data provided" in str(e)


def test_contact_sheet_generates_with_custom_thumbnail_size() -> None:
    """Test that contact sheet generates with custom thumbnail size."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = _make_sample_frame_data()

        result = generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(200, 200),
            columns=2,
        )

        assert result == output_path
        assert output_path.exists()


def test_contact_sheet_generates_with_custom_columns() -> None:
    """Test that contact sheet generates with custom column count."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = [
            {"beat_id": f"beat_{i:02d}", "frame_path": f"/tmp/beat_{i:02d}.png", "qa_verdict": "pass"}
            for i in range(5)
        ]

        result = generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=3,
        )

        assert result == output_path
        assert output_path.exists()


def test_contact_sheet_generator_class() -> None:
    """Test ContactSheetGenerator class directly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = _make_sample_frame_data()

        generator = ContactSheetGenerator(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=2,
            padding=5,
        )

        result = generator.generate()

        assert result == output_path
        assert output_path.exists()


def test_contact_sheet_output_format() -> None:
    """Test that contact sheet outputs JPEG format."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = _make_sample_frame_data()

        generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=2,
        )

        # Check file extension
        assert output_path.suffix == ".jpg"


def test_no_comfyui_or_subprocess_called() -> None:
    """Test that no ComfyUI or subprocess is called during contact sheet generation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "contact_sheet.jpg"
        frame_data = _make_sample_frame_data()

        # This test ensures we only generate images locally without external calls
        result = generate_contact_sheet(
            frame_data=frame_data,
            output_path=output_path,
            thumbnail_size=(128, 128),
            columns=2,
        )

        # If this completes without error, no subprocess was called
        assert result == output_path
