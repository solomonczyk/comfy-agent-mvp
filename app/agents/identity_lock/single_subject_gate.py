"""Single Subject Gate - validates exactly one human subject.

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False


class SingleSubjectGate:
    """Validates single-subject policy."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def validate_single_subject(self, asset_path: str) -> Dict[str, Any]:
        """Validate that image contains exactly one human subject."""
        if not CV2_AVAILABLE:
            return self._fallback_validation(asset_path)

        try:
            # Load image
            img = cv2.imread(str(asset_path))
            if img is None:
                return {
                    "single_subject_gate_result": "image_load_failed",
                    "passed": False,
                }

            # Use Haar cascade for face detection (basic single-subject check)
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            face_count = len(faces)

            # Check for extra foreground persons (heuristic: multiple distinct face regions)
            result = {
                "single_subject_gate_result": "face_detection_completed",
                "faces_detected": face_count,
                "exactly_one_primary_human": face_count == 1,
                "extra_foreground_person_forbidden": face_count <= 1,
                "background_people_forbidden": face_count <= 1,
                "passed": face_count == 1,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            return result

        except Exception as e:
            return {
                "single_subject_gate_result": "validation_error",
                "error": str(e),
                "passed": False,
            }

    def _fallback_validation(self, asset_path: str) -> Dict[str, Any]:
        """Fallback validation without OpenCV."""
        return {
            "single_subject_gate_result": "operator_visual_review_required",
            "cv2_available": False,
            "reason": "face_detection_tooling_not_available",
            "operator_review_required": True,
            "passed": None,  # Cannot determine without tooling
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def save_gate_result(self, result: Dict[str, Any]) -> None:
        """Save the single-subject gate result."""
        gate_path = self.identity_lock_dir / "single_subject_gate_result.json"
        with open(gate_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
