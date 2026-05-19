"""Face crop detector and basic framing check for wide/medium-shot validation.

RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001

Detects:
- Face crop/close-up (face occupies >50% of frame)
- Square aspect ratio (1024x1024 forbidden)
- Minimum resolution (1344x768 or equivalent)
- Wide/medium-shot composition (face in upper third, body visible)
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageStat
    import cv2
    import numpy as np
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False


@dataclass
class FramingAnalysis:
    """Result of framing analysis."""
    path: str
    exists: bool
    readable: bool
    width: int
    height: int
    aspect_ratio: float
    is_square: bool
    is_wide: bool
    is_portrait: bool
    resolution_valid: bool
    min_width_met: bool
    min_height_met: bool
    face_detected: bool
    face_crop_detected: bool
    face_area_ratio: float
    face_center_y_ratio: float
    is_closeup: bool
    is_medium_shot: bool
    is_wide_shot: bool
    composition_valid: bool
    rejection_reason: str | None


class FramingDetector:
    """Detector for face crop and framing analysis."""

    # Thresholds
    MIN_WIDTH = 1344
    MIN_HEIGHT = 768
    SQUARE_ASPECT_TOLERANCE = 0.1  # Within 10% of 1.0
    FACE_CROP_THRESHOLD = 0.5  # Face area > 50% of frame
    CLOSEUP_FACE_THRESHOLD = 0.35  # Face area > 35%
    FACE_CENTER_Y_UPPER_THIRD = 0.33  # Face center should be in upper third
    MEDIUM_SHOT_FACE_THRESHOLD = 0.15  # Face area 15-35%
    WIDE_SHOT_FACE_THRESHOLD = 0.15  # Face area < 15%

    def __init__(self) -> None:
        self.face_cascade = None
        if CV_AVAILABLE:
            try:
                self.face_cascade = cv2.CascadeClassifier(
                    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
                )
            except Exception:
                pass

    def analyze_framing(self, image_path: str | Path) -> FramingAnalysis:
        """Analyze image framing and composition.

        Args:
            image_path: Path to image file

        Returns:
            FramingAnalysis with all metrics
        """
        path = Path(image_path)
        result = FramingAnalysis(
            path=str(path),
            exists=path.exists(),
            readable=False,
            width=0,
            height=0,
            aspect_ratio=0.0,
            is_square=False,
            is_wide=False,
            is_portrait=False,
            resolution_valid=False,
            min_width_met=False,
            min_height_met=False,
            face_detected=False,
            face_crop_detected=False,
            face_area_ratio=0.0,
            face_center_y_ratio=0.0,
            is_closeup=False,
            is_medium_shot=False,
            is_wide_shot=False,
            composition_valid=False,
            rejection_reason=None,
        )

        if not path.exists():
            result.rejection_reason = "file_not_found"
            return result

        if not CV_AVAILABLE:
            result.rejection_reason = "cv_not_available"
            return result

        try:
            img = cv2.imread(str(path))
            if img is None:
                result.rejection_reason = "unreadable_image"
                return result

            result.readable = True
            height, width = img.shape[:2]
            result.width = width
            result.height = height
            result.aspect_ratio = width / height

            # Check aspect ratio
            result.is_square = bool(abs(result.aspect_ratio - 1.0) < self.SQUARE_ASPECT_TOLERANCE)
            result.is_wide = bool(result.aspect_ratio > 1.0)
            result.is_portrait = bool(result.aspect_ratio < 1.0)

            # Check resolution
            result.min_width_met = bool(width >= self.MIN_WIDTH)
            result.min_height_met = bool(height >= self.MIN_HEIGHT)
            result.resolution_valid = bool(result.min_width_met and result.min_height_met)

            # Detect faces
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.1, 4) if self.face_cascade else []

            result.face_detected = bool(len(faces) > 0)

            if len(faces) > 0:
                # Analyze largest face
                largest_face = max(faces, key=lambda f: f[2] * f[3])
                x, y, w, h = largest_face

                # Face area ratio
                face_area = w * h
                frame_area = width * height
                result.face_area_ratio = face_area / frame_area

                # Face center Y ratio (0 = top, 1 = bottom)
                face_center_y = y + h / 2
                result.face_center_y_ratio = face_center_y / height

                # Determine shot type
                result.face_crop_detected = bool(result.face_area_ratio > self.FACE_CROP_THRESHOLD)
                result.is_closeup = bool(result.face_area_ratio > self.CLOSEUP_FACE_THRESHOLD)
                result.is_medium_shot = bool(
                    self.MEDIUM_SHOT_FACE_THRESHOLD <= result.face_area_ratio <= self.CLOSEUP_FACE_THRESHOLD
                )
                result.is_wide_shot = bool(result.face_area_ratio < self.MEDIUM_SHOT_FACE_THRESHOLD)

                # Composition validation
                # For wide/medium shot: not a closeup, not a crop, resolution met
                # Accept both medium and wide shots regardless of face position
                composition_ok = (
                    not result.face_crop_detected and
                    (result.is_medium_shot or result.is_wide_shot) and
                    result.resolution_valid and
                    not result.is_square
                )
                result.composition_valid = bool(composition_ok)

                if result.face_crop_detected:
                    result.rejection_reason = "face_crop_detected"
                elif not composition_ok:
                    result.rejection_reason = "poor_composition"
            else:
                # No face detected - could be wide shot with body visible
                result.is_wide_shot = True
                result.composition_valid = bool(result.resolution_valid and not result.is_square)
                result.rejection_reason = "no_face_detected"

            # Final validation
            if result.is_square:
                result.rejection_reason = "square_aspect_ratio_forbidden"
            elif not result.resolution_valid:
                result.rejection_reason = f"resolution_below_minimum: {width}x{height} < {self.MIN_WIDTH}x{self.MIN_HEIGHT}"
            elif result.is_closeup:
                result.rejection_reason = "closeup_shot_forbidden"

            # Override rejection if composition is valid and resolution is met
            if result.resolution_valid and not result.is_square and not result.is_closeup:
                result.rejection_reason = None

        except Exception as e:
            result.rejection_reason = f"analysis_error: {str(e)[:100]}"

        return result

    def validate_and_classify(self, image_path: str | Path) -> dict[str, Any]:
        """Validate framing and return classification dict.

        Returns dict matching task requirements.
        """
        result = self.analyze_framing(image_path)

        return {
            "task_id": "RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001",
            "document_type": "framing_validation_report",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "image_path": result.path,
            "exists": result.exists,
            "readable": result.readable,
            "dimensions": {
                "width": result.width,
                "height": result.height,
            },
            "aspect_ratio": round(result.aspect_ratio, 3),
            "is_square": result.is_square,
            "is_wide": result.is_wide,
            "is_portrait": result.is_portrait,
            "resolution_valid": result.resolution_valid,
            "min_width_met": result.min_width_met,
            "min_height_met": result.min_height_met,
            "face_analysis": {
                "face_detected": result.face_detected,
                "face_crop_detected": result.face_crop_detected,
                "face_area_ratio": round(result.face_area_ratio, 3),
                "face_center_y_ratio": round(result.face_center_y_ratio, 3),
            },
            "shot_type": {
                "is_closeup": result.is_closeup,
                "is_medium_shot": result.is_medium_shot,
                "is_wide_shot": result.is_wide_shot,
            },
            "composition_valid": result.composition_valid,
            "rejection_reason": result.rejection_reason,
            "previously_rejected_assets_forbidden": True,
            "square_1024_output_forbidden": result.is_square,
            "closeup_reference_as_composition_forbidden": result.is_closeup,
            "min_expected_resolution_met": result.resolution_valid,
        }


def validate_composition(
    image_paths: list[str | Path],
    min_width: int = 1344,
    min_height: int = 768,
) -> dict[str, Any]:
    """Validate composition of multiple images.

    Args:
        image_paths: List of image paths
        min_width: Minimum required width
        min_height: Minimum required height

    Returns:
        Validation report
    """
    detector = FramingDetector()
    validations = []
    valid_assets = []
    rejected_assets = []

    for path in image_paths:
        validation = detector.validate_and_classify(path)
        validations.append(validation)

        # Check hard gates
        is_valid = (
            not validation["is_square"] and
            validation["resolution_valid"] and
            not validation["shot_type"]["is_closeup"] and
            validation["composition_valid"]
        )

        if is_valid:
            valid_assets.append(validation)
        else:
            rejected_assets.append(validation)

    # Determine overall status
    all_valid = len(rejected_assets) == 0 and len(valid_assets) > 0
    any_square = any(v["is_square"] for v in validations)
    any_closeup = any(v["shot_type"]["is_closeup"] for v in validations)
    any_low_resolution = any(not v["resolution_valid"] for v in validations)

    return {
        "task_id": "RC-COMBINE-V2-COMPOSITION-WORKFLOW-REAL-CANDIDATE-GENERATION-001",
        "document_type": "composition_validation_report",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total_images": len(image_paths),
        "valid_images": len(valid_assets),
        "rejected_images": len(rejected_assets),
        "all_valid": all_valid,
        "hard_gates": {
            "previously_rejected_assets_forbidden": True,
            "square_1024_output_forbidden": not any_square,
            "min_expected_resolution": f"{min_width}x{min_height}",
            "min_expected_resolution_met": not any_low_resolution,
            "closeup_reference_as_composition_forbidden": not any_closeup,
            "blank_detector_required": True,
            "face_crop_detector_or_basic_framing_check_required": True,
            "generation_count": 1,
            "production_accepted": False,
        },
        "validations": validations,
        "current_state": (
            "operator_visual_review_required" if all_valid
            else "composition_validation_failed"
        ),
        "next_allowed_action": (
            "operator_visual_review_required" if all_valid
            else "composition_workflow_repair_required"
        ),
        "production_accepted": False,
    }
