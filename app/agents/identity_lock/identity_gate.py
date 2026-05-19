"""Identity Gate - validates identity consistency (with honest fallback).

RC-COMBINE-V2-IDENTITY-LOCKED-CANONICAL-REFERENCE-GENERATION-001
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict


class IdentityGate:
    """Validates identity consistency with honest fallback."""

    def __init__(self, project_root: str | Path) -> None:
        self.project_root = Path(project_root)
        self.control_dir = self.project_root / "output" / "control"
        self.identity_lock_dir = self.control_dir / "identity_lock"
        self.identity_lock_dir.mkdir(parents=True, exist_ok=True)

    def validate_identity(
        self, generated_asset_path: str, canonical_identity_path: str
    ) -> Dict[str, Any]:
        """Validate identity consistency with honest fallback."""
        # Check if face embedding tooling is available
        embedding_available = self._check_embedding_tooling()

        if embedding_available:
            # Use real face embedding comparison
            return self._real_identity_validation(generated_asset_path, canonical_identity_path)
        else:
            # Honest fallback - do not fake identity pass
            return self._honest_fallback()

    def _check_embedding_tooling(self) -> bool:
        """Check if face embedding tooling is available."""
        try:
            import face_recognition  # type: ignore
            return True
        except ImportError:
            return False

    def _real_identity_validation(
        self, generated_asset_path: str, canonical_identity_path: str
    ) -> Dict[str, Any]:
        """Real identity validation using face embeddings."""
        try:
            import face_recognition  # type: ignore

            # Load images
            generated_image = face_recognition.load_image_file(generated_asset_path)
            canonical_image = face_recognition.load_image_file(canonical_identity_path)

            # Encode faces
            generated_encodings = face_recognition.face_encodings(generated_image)
            canonical_encodings = face_recognition.face_encodings(canonical_image)

            if not generated_encodings or not canonical_encodings:
                return {
                    "identity_embedding_available": True,
                    "identity_gate_result": "no_faces_detected",
                    "identity_confidence": 0.0,
                    "faces_detected_generated": len(generated_encodings),
                    "faces_detected_canonical": len(canonical_encodings),
                }

            # Compare faces
            distance = face_recognition.face_distance(
                [canonical_encodings[0]], generated_encodings[0]
            )[0]
            similarity = 1.0 - distance

            return {
                "identity_embedding_available": True,
                "identity_gate_result": "identity_similarity_computed",
                "identity_confidence": float(similarity),
                "face_distance": float(distance),
                "faces_detected_generated": len(generated_encodings),
                "faces_detected_canonical": len(canonical_encodings),
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        except Exception as e:
            # If real validation fails, use honest fallback
            return {
                "identity_embedding_available": True,
                "identity_gate_result": "validation_error_honest_fallback",
                "validation_error": str(e),
                "operator_review_required_with_identity_warning": True,
            }

    def _honest_fallback(self) -> Dict[str, Any]:
        """Honest fallback - does not fake identity pass."""
        return {
            "identity_embedding_available": False,
            "identity_gate_result": "operator_review_required_with_identity_warning",
            "identity_confidence": None,
            "reason": "face_embedding_tooling_not_available",
            "operator_review_required": True,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def save_gate_result(self, result: Dict[str, Any]) -> None:
        """Save the identity gate result."""
        gate_path = self.identity_lock_dir / "identity_gate_result.json"
        with open(gate_path, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
