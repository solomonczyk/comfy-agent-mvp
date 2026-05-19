"""Tests for framing detector.

RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001
"""
import numpy as np
import pytest
from PIL import Image

from app.visual_generation.framing_detector import FramingDetector, validate_composition


class TestFramingDetector:
    """Test framing detection functionality."""

    def test_detects_square_aspect(self, tmp_path):
        """Test detection of square aspect ratio."""
        detector = FramingDetector()

        # Create a square image
        img_array = np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "square.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        assert result.is_square is True
        assert result.resolution_valid is False  # Square is below min width for wide
        assert result.composition_valid is False

    def test_detects_wide_aspect(self, tmp_path):
        """Test detection of wide aspect ratio."""
        detector = FramingDetector()

        # Create a wide image (1344x768)
        img_array = np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "wide.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        assert result.is_wide is True
        assert result.is_square is False
        assert result.resolution_valid is True
        assert result.min_width_met is True
        assert result.min_height_met is True

    def test_detects_portrait_aspect(self, tmp_path):
        """Test detection of portrait aspect ratio."""
        detector = FramingDetector()

        # Create a portrait image (768x1344)
        img_array = np.random.randint(0, 256, (1344, 768, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "portrait.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        assert result.is_portrait is True
        assert result.is_square is False
        assert result.is_wide is False
        assert result.resolution_valid is False  # Width < 1344

    def test_rejects_below_minimum_resolution(self, tmp_path):
        """Test rejection of images below minimum resolution."""
        detector = FramingDetector()

        # Create a small wide image (1024x768)
        img_array = np.random.randint(0, 256, (768, 1024, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "small.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        assert result.resolution_valid is False
        assert result.min_width_met is False  # 1024 < 1344
        assert result.min_height_met is True

    def test_accepts_minimum_resolution(self, tmp_path):
        """Test acceptance of images at minimum resolution."""
        detector = FramingDetector()

        # Create minimum resolution image (1344x768)
        img_array = np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "min_res.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        assert result.resolution_valid is True
        assert result.min_width_met is True
        assert result.min_height_met is True

    def test_handles_missing_file(self, tmp_path):
        """Test handling of missing file."""
        detector = FramingDetector()

        missing_path = tmp_path / "missing.png"
        result = detector.analyze_framing(missing_path)

        assert result.exists is False
        assert result.rejection_reason == "file_not_found"

    def test_validation_report_format(self, tmp_path):
        """Test that validation report has correct format."""
        detector = FramingDetector()

        # Create a valid wide image
        img_array = np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "report_test.png"
        img.save(img_path)

        report = detector.validate_and_classify(img_path)

        assert report["task_id"] is not None
        assert report["document_type"] == "framing_validation_report"
        assert "timestamp" in report
        assert "image_path" in report
        assert "exists" in report
        assert "readable" in report
        assert "dimensions" in report
        assert "aspect_ratio" in report
        assert "is_square" in report
        assert "is_wide" in report
        assert "resolution_valid" in report
        assert "face_analysis" in report
        assert "shot_type" in report
        assert "composition_valid" in report
        assert "rejection_reason" in report

    def test_accepts_medium_shot(self, tmp_path):
        """Test that medium shots are accepted as valid composition."""
        detector = FramingDetector()

        # Create a wide image (will be classified as medium shot if face detected)
        img_array = np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "medium.png"
        img.save(img_path)

        result = detector.analyze_framing(img_path)

        # Medium shot should be valid if resolution is met and not square
        assert result.resolution_valid is True
        assert result.is_square is False
        # Composition valid if medium or wide shot
        if result.is_medium_shot or result.is_wide_shot:
            assert result.composition_valid is True


class TestCompositionValidation:
    """Test composition validation of multiple images."""

    def test_validates_multiple_images(self, tmp_path):
        """Test validation of multiple images."""
        # Create test images
        img1_path = tmp_path / "valid_wide.png"
        img2_path = tmp_path / "invalid_square.png"

        # Valid wide image
        np.random.seed(42)
        img1 = Image.fromarray(np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8))
        img1.save(img1_path)

        # Invalid square image
        img2 = Image.fromarray(np.random.randint(0, 256, (1024, 1024, 3), dtype=np.uint8))
        img2.save(img2_path)

        report = validate_composition([img1_path, img2_path])

        assert report["total_images"] == 2
        assert report["valid_images"] == 1
        assert report["rejected_images"] == 1
        assert report["all_valid"] is False
        assert report["hard_gates"]["square_1024_output_forbidden"] is False

    def test_all_valid_state(self, tmp_path):
        """Test state when all images are valid."""
        img1_path = tmp_path / "valid1.png"
        img2_path = tmp_path / "valid2.png"

        np.random.seed(42)
        img1 = Image.fromarray(np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8))
        img1.save(img1_path)

        np.random.seed(43)
        img2 = Image.fromarray(np.random.randint(0, 256, (768, 1344, 3), dtype=np.uint8))
        img2.save(img2_path)

        report = validate_composition([img1_path, img2_path])

        assert report["all_valid"] is True
        assert report["current_state"] == "operator_visual_review_required"
        assert report["next_allowed_action"] == "operator_visual_review_required"

    def test_empty_collection(self, tmp_path):
        """Test validation with empty collection."""
        report = validate_composition([])

        assert report["total_images"] == 0
        assert report["valid_images"] == 0
        assert report["all_valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
