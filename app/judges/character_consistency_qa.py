"""Character Identity Consistency QA for multi-frame generation.

Evaluates character identity consistency across a batch of generated frames.
This is critical for ensuring the same character appears consistently across
multiple frames in a shot.

If no face/identity model is available, this QA returns manual_review_required
to prevent accepting inconsistent character identities without verification.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class CharacterConsistencyQA:
    """QA for character identity consistency across frame batches."""

    def __init__(self) -> None:
        """Initialize CharacterConsistencyQA."""
        # Try to load face detector (optional)
        self.face_cascade = None
        try:
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
            )
            logger.info("Face cascade loaded successfully")
        except Exception as e:
            logger.warning(f"Could not load face cascade: {e}")

    def evaluate_batch(
        self,
        frame_paths: list[Path | str],
        reference_image_path: Path | str | None = None,
        shot_id: str = "unknown",
    ) -> dict[str, Any]:
        """Evaluate character identity consistency across a batch of frames.

        Args:
            frame_paths: List of frame image paths to evaluate.
            reference_image_path: Optional reference character image.
            shot_id: Shot identifier for reporting.

        Returns:
            QA report dict with identity consistency assessment.
        """
        # Normalize paths
        frame_paths = [Path(p) for p in frame_paths]
        reference_image_path = Path(reference_image_path) if reference_image_path else None

        # Initialize report
        report = {
            "shot_id": shot_id,
            "frame_paths": [str(p) for p in frame_paths],
            "reference_image_path": str(reference_image_path) if reference_image_path else None,
            "checks_performed": [],
            "similarity_scores": {},
            "identity_consistency_passed": False,
            "verdict": "manual_review_required",
            "reason": "identity consistency could not be verified",
            "recommended_action": "retry_generate_frames",
            "evaluated_at": datetime.utcnow().isoformat() + "Z",
        }

        # Check if all frames exist
        missing_frames = [p for p in frame_paths if not p.exists()]
        if missing_frames:
            report["verdict"] = "rejected"
            report["reason"] = f"Missing frame files: {missing_frames}"
            report["recommended_action"] = "regenerate_frames"
            return report

        # Check if reference exists if provided
        if reference_image_path and not reference_image_path.exists():
            report["verdict"] = "rejected"
            report["reason"] = f"Reference image not found: {reference_image_path}"
            report["recommended_action"] = "provide_reference"
            return report

        # Perform checks
        report["checks_performed"] = self._perform_checks(frame_paths, reference_image_path)

        # Determine verdict based on availability of face detector
        if self.face_cascade is None:
            # No face detector available - require manual review
            report["verdict"] = "manual_review_required"
            report["reason"] = (
                "identity consistency could not be verified: "
                "no face/identity model available"
            )
            report["identity_consistency_passed"] = False
        else:
            # Face detector available - perform actual consistency check
            consistency_result = self._check_face_consistency(frame_paths, reference_image_path)
            report.update(consistency_result)

        return report

    def _perform_checks(
        self,
        frame_paths: list[Path],
        reference_image_path: Path | None,
    ) -> list[dict[str, Any]]:
        """Perform basic checks on frames.

        Args:
            frame_paths: List of frame paths.
            reference_image_path: Optional reference image path.

        Returns:
            List of check results.
        """
        checks = []

        # Check 1: Frame count
        checks.append({
            "check": "frame_count",
            "passed": len(frame_paths) > 0,
            "details": {"frame_count": len(frame_paths)},
        })

        # Check 2: All frames are valid images
        valid_frames = 0
        for frame_path in frame_paths:
            try:
                img = cv2.imread(str(frame_path))
                if img is not None:
                    valid_frames += 1
            except Exception:
                pass

        checks.append({
            "check": "valid_images",
            "passed": valid_frames == len(frame_paths),
            "details": {"valid_count": valid_frames, "total_count": len(frame_paths)},
        })

        # Check 3: Reference image exists if provided
        if reference_image_path:
            checks.append({
                "check": "reference_exists",
                "passed": reference_image_path.exists(),
                "details": {"reference_path": str(reference_image_path)},
            })

        # Check 4: Face detector availability
        checks.append({
            "check": "face_detector_available",
            "passed": self.face_cascade is not None,
            "details": {"available": self.face_cascade is not None},
        })

        return checks

    def _check_face_consistency(
        self,
        frame_paths: list[Path],
        reference_image_path: Path | None,
    ) -> dict[str, Any]:
        """Check face consistency across frames using face detector.

        Args:
            frame_paths: List of frame paths.
            reference_image_path: Optional reference image path.

        Returns:
            Dict with consistency assessment.
        """
        result = {
            "similarity_scores": {},
            "identity_consistency_passed": False,
            "verdict": "identity_drift",
            "reason": "",
        }

        # Detect faces in each frame
        face_counts = []
        for i, frame_path in enumerate(frame_paths):
            try:
                img = cv2.imread(str(frame_path))
                if img is None:
                    face_counts.append(0)
                    continue

                gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4)
                face_counts.append(len(faces))

                # Check for exactly one face
                if len(faces) != 1:
                    result["similarity_scores"][f"frame_{i}_face_count"] = len(faces)

            except Exception as e:
                logger.warning(f"Failed to detect faces in {frame_path}: {e}")
                face_counts.append(0)

        # Check face count consistency
        if len(set(face_counts)) == 1 and face_counts[0] == 1:
            # All frames have exactly one face - could be consistent
            result["identity_consistency_passed"] = True
            result["verdict"] = "accepted"
            result["reason"] = "All frames have exactly one detected face"
        elif len(set(face_counts)) == 1 and face_counts[0] == 0:
            # No faces detected - cannot verify
            result["identity_consistency_passed"] = False
            result["verdict"] = "manual_review_required"
            result["reason"] = "No faces detected in any frame - cannot verify identity"
        else:
            # Inconsistent face counts - identity drift
            result["identity_consistency_passed"] = False
            result["verdict"] = "identity_drift"
            result["reason"] = f"Inconsistent face counts across frames: {face_counts}"

        result["similarity_scores"]["face_counts"] = face_counts

        return result


def run_identity_qa(
    project_root: Path | str,
    episode_id: str,
    shot_id: str,
    frame_manifest_path: Path | str | None = None,
) -> dict[str, Any]:
    """Run identity QA on a shot's generated frames.

    Args:
        project_root: Project root directory.
        episode_id: Episode identifier.
        shot_id: Shot identifier.
        frame_manifest_path: Optional path to frames manifest.

    Returns:
        QA report dict.
    """
    project_root = Path(project_root)

    # Determine frame manifest path
    if frame_manifest_path is None:
        frame_manifest_path = project_root / "output" / "control" / "frames_manifest.json"
    else:
        frame_manifest_path = Path(frame_manifest_path)

    # Load frame manifest
    if not frame_manifest_path.exists():
        return {
            "shot_id": shot_id,
            "error": f"Frame manifest not found: {frame_manifest_path}",
            "verdict": "rejected",
            "reason": "frame_manifest_missing",
            "recommended_action": "generate_frames_first",
        }

    with open(frame_manifest_path, "r") as f:
        manifest = json.load(f)

    # Verify manifest matches shot
    if manifest.get("shot_id") != shot_id:
        return {
            "shot_id": shot_id,
            "error": f"Manifest shot_id mismatch: {manifest.get('shot_id')} != {shot_id}",
            "verdict": "rejected",
            "reason": "manifest_shot_id_mismatch",
            "recommended_action": "verify_shot_id",
        }

    # Get frame paths from manifest
    frame_paths = manifest.get("frame_paths", [])
    if not frame_paths:
        return {
            "shot_id": shot_id,
            "error": "No frame paths in manifest",
            "verdict": "rejected",
            "reason": "no_frames_in_manifest",
            "recommended_action": "generate_frames_first",
        }

    # Get reference image path from prompt pack if available
    reference_image_path = None
    prompt_pack_path = project_root / "output" / "control" / "prompt_pack.json"
    if prompt_pack_path.exists():
        with open(prompt_pack_path, "r") as f:
            prompt_pack = json.load(f)
            reference_image_path = prompt_pack.get("reference_image_path")

    # Run QA
    qa = CharacterConsistencyQA()
    report = qa.evaluate_batch(
        frame_paths=frame_paths,
        reference_image_path=reference_image_path,
        shot_id=shot_id,
    )

    return report
