"""Blank/gray image detector for ComfyUI output validation.

RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001

Detects near-uniform gray/black/white outputs, stubs, and invalid images
using size, dimensions, pixel variance, entropy, and unique color analysis.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, UnidentifiedImageError
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False


@dataclass
class ImageValidationResult:
    """Result of blank image validation."""
    path: str
    exists: bool
    readable: bool
    size_bytes: int
    width: int
    height: int
    sha256: str | None
    mean_brightness: float
    std_brightness: float
    unique_colors: int
    pixel_variance: float
    entropy_estimate: float
    is_blank: bool
    is_uniform_gray: bool
    is_stub: bool
    is_valid: bool
    rejection_reason: str | None


class BlankImageDetector:
    """Detects blank, gray, stub, or invalid images."""

    # Thresholds for blank detection
    BLANK_MEAN_THRESHOLD = 10  # Near-black
    BLANK_STD_THRESHOLD = 5    # Very low variance
    UNIFORM_GRAY_STD_THRESHOLD = 10  # Low variance for gray
    UNIFORM_GRAY_MEAN_MIN = 100  # Not too dark
    UNIFORM_GRAY_MEAN_MAX = 200  # Not too bright
    MIN_UNIQUE_COLORS = 100  # Minimum for valid image
    MIN_SIZE_BYTES = 1024  # Minimum 1KB for valid image
    MIN_PIXEL_VARIANCE = 10  # Minimum variance for valid image

    def __init__(self) -> None:
        self.errors: list[str] = []

    def validate_image(self, image_path: str | Path) -> ImageValidationResult:
        """Validate an image for blank/gray/stub detection.

        Args:
            image_path: Path to the image file

        Returns:
            ImageValidationResult with all detection metrics
        """
        path = Path(image_path)
        result = ImageValidationResult(
            path=str(path),
            exists=path.exists(),
            readable=False,
            size_bytes=0,
            width=0,
            height=0,
            sha256=None,
            mean_brightness=0.0,
            std_brightness=0.0,
            unique_colors=0,
            pixel_variance=0.0,
            entropy_estimate=0.0,
            is_blank=False,
            is_uniform_gray=False,
            is_stub=False,
            is_valid=False,
            rejection_reason=None,
        )

        # Check existence
        if not path.exists():
            result.exists = False
            result.rejection_reason = "file_not_found"
            return result

        result.exists = True
        result.readable = False
        result.is_valid = False
        result.size_bytes = path.stat().st_size
        if result.size_bytes < self.MIN_SIZE_BYTES:
            result.is_stub = bool(True)
            result.rejection_reason = f"stub_file: size={result.size_bytes}B < {self.MIN_SIZE_BYTES}B"
            return result

        # Try to open and analyze image
        if not CV_AVAILABLE:
            result.rejection_reason = "cv_not_available"
            return result

        try:
            with Image.open(path) as img:
                result.readable = True
                result.width, result.height = img.size

                # Convert to array for analysis
                arr = np.array(img)
                if len(arr.shape) == 2:
                    # Grayscale
                    gray = arr
                else:
                    # Color - convert to grayscale
                    gray = np.array(img.convert('L'))

                # Calculate metrics
                result.mean_brightness = float(np.mean(gray))
                result.std_brightness = float(np.std(gray))
                result.pixel_variance = float(np.var(gray))

                # Unique colors (sample for large images)
                if len(arr.shape) == 3:
                    flat = arr.reshape(-1, arr.shape[-1])
                    if len(flat) > 100000:
                        flat = flat[::len(flat)//100000]  # Sample
                    unique = np.unique(flat, axis=0)
                    result.unique_colors = len(unique)
                else:
                    result.unique_colors = len(np.unique(gray))

                # Entropy estimate (simplified)
                hist, _ = np.histogram(gray, bins=256, range=(0, 256))
                hist = hist[hist > 0]
                if len(hist) > 0:
                    prob = hist / hist.sum()
                    result.entropy_estimate = float(-np.sum(prob * np.log2(prob)))

                # Blank detection
                result.is_blank = bool(
                    result.mean_brightness < self.BLANK_MEAN_THRESHOLD or
                    result.std_brightness < self.BLANK_STD_THRESHOLD
                )
                result.is_uniform_gray = bool(
                    result.std_brightness < self.UNIFORM_GRAY_STD_THRESHOLD and
                    self.UNIFORM_GRAY_MEAN_MIN < result.mean_brightness < self.UNIFORM_GRAY_MEAN_MAX
                )

                # Calculate SHA256
                result.sha256 = self._calculate_sha256(path)

                # Final validity check
                if result.is_blank:
                    result.rejection_reason = "blank_image: near-black or blank"
                elif result.is_uniform_gray:
                    result.rejection_reason = "uniform_gray: near-uniform gray"
                elif result.is_stub:
                    result.rejection_reason = "stub_file: too small"
                else:
                    result.rejection_reason = None
                    result.is_valid = bool(True)

        except UnidentifiedImageError:
            result.rejection_reason = "unidentified_image_format"
        except Exception as e:
            result.rejection_reason = f"analysis_error: {str(e)[:100]}"

        return result

    def validate_and_classify(self, image_path: str | Path) -> dict[str, Any]:
        """Validate image and return classification dict.

        Returns dict matching the task's required output format.
        """
        result = self.validate_image(image_path)

        return {
            "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
            "document_type": "blank_image_validation_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_path": result.path,
            "exists": result.exists,
            "readable": result.readable,
            "size_bytes": result.size_bytes,
            "dimensions": {
                "width": result.width,
                "height": result.height,
            },
            "sha256": result.sha256,
            "pixel_analysis": {
                "mean_brightness": round(result.mean_brightness, 2),
                "std_brightness": round(result.std_brightness, 2),
                "pixel_variance": round(result.pixel_variance, 2),
                "unique_colors": result.unique_colors,
                "entropy_estimate": round(result.entropy_estimate, 2),
            },
            "classification": {
                "is_blank": result.is_blank,
                "is_uniform_gray": result.is_uniform_gray,
                "is_stub": result.is_stub,
                "is_valid": result.is_valid,
            },
            "rejection_reason": result.rejection_reason,
            "operator_rejection_recorded": False,
            "invalid_blank_output_classified": not result.is_valid,
        }

    @staticmethod
    def _calculate_sha256(path: Path) -> str:
        """Calculate SHA256 hash of file."""
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()


def validate_output_collection(
    image_paths: list[str | Path],
    prompt_id: str | None = None,
) -> dict[str, Any]:
    """Validate a collection of output images.

    Args:
        image_paths: List of paths to output images
        prompt_id: Optional ComfyUI prompt_id for tracking

    Returns:
        Validation report for all images
    """
    detector = BlankImageDetector()
    validations = []
    valid_assets = []
    rejected_assets = []

    for path in image_paths:
        validation = detector.validate_and_classify(path)
        validations.append(validation)

        if validation["classification"]["is_valid"]:
            valid_assets.append(validation)
        else:
            rejected_assets.append(validation)

    # Determine overall status
    all_valid = len(rejected_assets) == 0 and len(valid_assets) > 0
    any_blank = any(v["classification"]["is_blank"] for v in validations)
    any_stub = any(v["classification"]["is_stub"] for v in validations)

    return {
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "document_type": "output_collection_validation_report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prompt_id": prompt_id,
        "total_images": len(image_paths),
        "valid_images": len(valid_assets),
        "rejected_images": len(rejected_assets),
        "all_valid": all_valid,
        "blank_detected": any_blank,
        "stub_detected": any_stub,
        "validations": validations,
        "current_state": (
            "operator_visual_review_required" if all_valid
            else "runtime_output_collection_blocked"
        ),
        "next_allowed_action": (
            "operator_visual_review_required" if all_valid
            else "runtime_output_collection_repair_required"
        ),
        "production_accepted": False,
    }


def record_operator_rejection(
    asset_path: str | Path,
    rejection_reason: str,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Record operator rejection of blank/stub asset.

    Args:
        asset_path: Path to the rejected asset
        rejection_reason: Reason for rejection
        project_root: Project root directory

    Returns:
        Rejection record dict
    """
    rejection_record = {
        "task_id": "RC-COMBINE-V2-RUNTIME-OUTPUT-COLLECTION-AND-REAL-GENERATION-RECOVERY-001",
        "document_type": "operator_output_rejection_record",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "asset_path": str(asset_path),
        "rejection_reason": rejection_reason,
        "rejection_type": "invalid_blank_output",
        "operator_decision": "reject_blank_output",
        "production_accepted": False,
        "next_allowed_action": "runtime_output_collection_repair_required",
        "current_state": "runtime_output_collection_blocked",
    }

    # Write to control directory if project_root provided
    if project_root:
        control_dir = Path(project_root) / "output" / "control"
        control_dir.mkdir(parents=True, exist_ok=True)
        rejection_path = control_dir / "operator_output_rejection_record.json"
        with open(rejection_path, "w", encoding="utf-8") as f:
            json.dump(rejection_record, f, indent=2, ensure_ascii=False)

    return rejection_record
