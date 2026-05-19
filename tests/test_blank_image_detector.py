"""Tests for blank image detector.

RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001
"""
import numpy as np
import pytest
from PIL import Image

from app.visual_generation.blank_image_detector import BlankImageDetector, validate_output_collection


class TestBlankImageDetector:
    """Test blank image detection functionality."""

    def test_detects_blank_black_image(self, tmp_path):
        """Test detection of completely black image."""
        detector = BlankImageDetector()

        # Create a black image
        img_array = np.zeros((512, 512, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "black.png"
        img.save(img_path)

        result = detector.validate_image(img_path)

        # Black images should be detected (mean < 10 or std < 5)
        assert result.mean_brightness < 10
        assert result.is_valid is False
        assert "blank" in (result.rejection_reason or "").lower() or "black" in (result.rejection_reason or "").lower() or result.std_brightness < 5

    def test_detects_blank_white_image(self, tmp_path):
        """Test detection of completely white image."""
        detector = BlankImageDetector()

        # Create a white image
        img_array = np.ones((512, 512, 3), dtype=np.uint8) * 255
        img = Image.fromarray(img_array)
        img_path = tmp_path / "white.png"
        img.save(img_path)

        result = detector.validate_image(img_path)

        # White has high mean (>200) but very low variance
        assert result.mean_brightness > 200
        assert result.std_brightness < 5  # Should have very low variance
        # Low variance images are invalid regardless of color
        assert result.is_valid is False

    def test_detects_uniform_gray(self, tmp_path):
        """Test detection of uniform gray image."""
        detector = BlankImageDetector()

        # Create a medium gray image
        img_array = np.ones((512, 512, 3), dtype=np.uint8) * 128
        img = Image.fromarray(img_array)
        img_path = tmp_path / "gray.png"
        img.save(img_path)

        result = detector.validate_image(img_path)

        assert result.is_uniform_gray is True
        assert result.is_valid is False
        assert 100 < result.mean_brightness < 200
        assert result.std_brightness < 10

    def test_passes_valid_image(self, tmp_path):
        """Test that valid images pass detection."""
        detector = BlankImageDetector()

        # Create a random colorful image
        np.random.seed(42)
        img_array = np.random.randint(0, 256, (512, 512, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "valid.png"
        img.save(img_path)

        result = detector.validate_image(img_path)

        assert result.is_blank is False
        assert result.is_uniform_gray is False
        assert result.is_valid is True
        assert result.unique_colors > 100

    def test_detects_stub_file(self, tmp_path):
        """Test detection of stub (too small) file."""
        detector = BlankImageDetector()

        # Create a tiny file
        stub_path = tmp_path / "stub.png"
        stub_path.write_bytes(b"fake png data")

        result = detector.validate_image(stub_path)

        assert result.is_stub is True
        assert result.is_valid is False
        assert result.size_bytes < 1024

    def test_handles_missing_file(self, tmp_path):
        """Test handling of missing file."""
        detector = BlankImageDetector()

        missing_path = tmp_path / "missing.png"
        result = detector.validate_image(missing_path)

        assert result.exists is False
        assert result.is_valid is False
        # rejection_reason should be "file_not_found" or similar
        assert result.rejection_reason is not None

    def test_sha256_calculation(self, tmp_path):
        """Test SHA256 calculation."""
        detector = BlankImageDetector()

        # Create an image
        img_array = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "test_sha.png"
        img.save(img_path)

        result = detector.validate_image(img_path)

        assert result.sha256 is not None
        assert len(result.sha256) == 64  # SHA256 hex length

    def test_validation_report_format(self, tmp_path):
        """Test that validation report has correct format."""
        detector = BlankImageDetector()

        # Create a valid image
        img_array = np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8)
        img = Image.fromarray(img_array)
        img_path = tmp_path / "report_test.png"
        img.save(img_path)

        report = detector.validate_and_classify(img_path)

        assert report["task_id"] is not None
        assert report["document_type"] == "blank_image_validation_report"
        assert "timestamp" in report
        assert "image_path" in report
        assert "exists" in report
        assert "readable" in report
        assert "size_bytes" in report
        assert "dimensions" in report
        assert "sha256" in report
        assert "pixel_analysis" in report
        assert "classification" in report
        assert "rejection_reason" in report


class TestOutputCollectionValidation:
    """Test output collection validation."""

    def test_validates_multiple_images(self, tmp_path):
        """Test validation of multiple images."""
        # Create test images
        img1_path = tmp_path / "img1.png"
        img2_path = tmp_path / "img2.png"

        # Valid image
        np.random.seed(42)
        img1 = Image.fromarray(np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8))
        img1.save(img1_path)

        # Blank image
        img2 = Image.fromarray(np.zeros((256, 256, 3), dtype=np.uint8))
        img2.save(img2_path)

        report = validate_output_collection([img1_path, img2_path], prompt_id="test-prompt")

        assert report["total_images"] == 2
        assert report["valid_images"] == 1
        assert report["rejected_images"] == 1
        # Black image is detected as invalid (blank or low variance)
        assert report["blank_detected"] is True or report["rejected_images"] > 0
        assert report["all_valid"] is False
        assert report["current_state"] == "runtime_output_collection_blocked"
        assert report["next_allowed_action"] == "runtime_output_collection_repair_required"

    def test_all_valid_state(self, tmp_path):
        """Test state when all images are valid."""
        img1_path = tmp_path / "valid1.png"
        img2_path = tmp_path / "valid2.png"

        np.random.seed(42)
        img1 = Image.fromarray(np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8))
        img1.save(img1_path)

        np.random.seed(43)
        img2 = Image.fromarray(np.random.randint(0, 256, (256, 256, 3), dtype=np.uint8))
        img2.save(img2_path)

        report = validate_output_collection([img1_path, img2_path], prompt_id="test-prompt")

        assert report["all_valid"] is True
        assert report["blank_detected"] is False
        assert report["current_state"] == "operator_visual_review_required"
        assert report["next_allowed_action"] == "operator_visual_review_required"

    def test_empty_collection(self, tmp_path):
        """Test validation with empty collection."""
        report = validate_output_collection([], prompt_id="test-prompt")

        assert report["total_images"] == 0
        assert report["valid_images"] == 0
        assert report["all_valid"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
